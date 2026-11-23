"""
GStreamer RTSP 수신 + 프레임별 타임스탬프 추출 (AI 엔진 1차 뼈대)

파이프라인:
  rtspsrc -> rtph264depay -> h264parse -> avdec_h264 -> videoconvert
          -> video/x-raw,format=BGR -> appsink

각 프레임마다 출력하는 값
  - pts_s     : 스트림 내부 시각(PTS, 초)
  - ntp_unix  : 송출측(RTCP SR) 기준 절대시각 → 녹화 구간·검출 결과 매칭용
  - delay_ms  : 수신 시각 - 송출 절대시각 (지연 시간 비교용)

환경변수
  RTSP_URL        기본 rtsp://mediamtx:8554/cam1
  RTSP_LATENCY_MS 지터버퍼 지연(ms), 기본 200
  PRINT_EVERY     N 프레임마다 로그 1줄, 기본 30
"""
import os
import sys
import time
from datetime import datetime, timezone

import gi
import numpy as np

gi.require_version("Gst", "1.0")
from gi.repository import GLib, Gst  # noqa: E402

RTSP_URL = os.getenv("RTSP_URL", "rtsp://mediamtx:8554/cam1")
# 지터버퍼 최대 대기(ms). 패킷이 빠졌을 때만 이 시간까지 기다리고 정상 패킷은 바로 넘김.
# 200ms: 같은 PC·LAN 환경에서 패킷 재정렬에 충분하면서 지연을 크게 늘리지 않는 값 (실측 수신 지연 약 8ms)
LATENCY_MS = int(os.getenv("RTSP_LATENCY_MS", "200"))
# 로그 출력 간격(프레임). 30: 15fps 영상 기준 2초에 1줄 → 로그가 넘치지 않으면서 수신 상태 확인 가능
PRINT_EVERY = max(1, int(os.getenv("PRINT_EVERY", "30")))
# 재연결 대기(초). 3초: MediaMTX 재시작·카메라 순단 시 접속 시도가 몰리지 않게 하면서 복구를 빠르게 하는 값
RECONNECT_SEC = 3

NTP_UNIX_OFFSET_S = 2208988800  # 1900-01-01 ~ 1970-01-01 초 차이
NTP_CAPS = None  # Gst.init 이후 생성

# protocols=tcp : Docker/Windows 환경에서 UDP 패킷 손실·방화벽 문제를 피하기 위함
# max-buffers=1 drop=true : 추론이 느려도 쌓인 프레임을 버리고 항상 최신 프레임만 처리 (지연 누적 방지)
# sync=false : 재생 시계에 맞춰 기다리지 않고 도착 즉시 처리
PIPELINE = (
    f'rtspsrc name=src location="{RTSP_URL}" latency={LATENCY_MS} protocols=tcp '
    "! rtph264depay ! h264parse ! avdec_h264 ! videoconvert "
    "! video/x-raw,format=BGR "
    "! appsink name=sink emit-signals=true max-buffers=1 drop=true sync=false"
)

frame_count = 0


def ntp_unix_from_buffer(buf):
    """RTCP SR 로 계산된 NTP 기준 절대시각(유닉스 초). 없으면 None."""
    try:
        meta = buf.get_reference_timestamp_meta(NTP_CAPS)
    except Exception:
        return None
    if meta is None:
        return None
    return meta.timestamp / Gst.SECOND - NTP_UNIX_OFFSET_S


def on_new_sample(sink):
    """appsink 에 새 프레임이 오면 numpy BGR 배열로 꺼내고 타임스탬프를 기록."""
    global frame_count
    sample = sink.emit("pull-sample")
    if sample is None:
        return Gst.FlowReturn.ERROR

    recv_unix = time.time()
    buf = sample.get_buffer()
    caps = sample.get_caps().get_structure(0)
    w, h = caps.get_value("width"), caps.get_value("height")

    ok, info = buf.map(Gst.MapFlags.READ)
    if not ok:
        return Gst.FlowReturn.ERROR
    try:
        # 여기서 frame 을 YOLO 등 추론에 넘기면 됨 (복사본 사용)
        frame = np.ndarray((h, w, 3), dtype=np.uint8, buffer=info.data).copy()
    finally:
        buf.unmap(info)

    frame_count += 1
    if frame_count % PRINT_EVERY == 0:
        pts_s = buf.pts / Gst.SECOND if buf.pts != Gst.CLOCK_TIME_NONE else -1
        ntp_unix = ntp_unix_from_buffer(buf)
        if ntp_unix is not None:
            ntp_str = datetime.fromtimestamp(ntp_unix, timezone.utc).isoformat()
            delay_ms = (recv_unix - ntp_unix) * 1000
            extra = f"ntp={ntp_str} delay_ms={delay_ms:.1f}"
        else:
            extra = "ntp=N/A (RTCP SR 수신 전)"
        print(
            f"[frame {frame_count}] {w}x{h} pts_s={pts_s:.3f} {extra} "
            f"mean={frame.mean():.1f}",
            flush=True,
        )
    return Gst.FlowReturn.OK


def run_once():
    """파이프라인 1회 실행. 에러/EOS 시 반환."""
    pipeline = Gst.parse_launch(PIPELINE)

    src = pipeline.get_by_name("src")
    # GStreamer 1.22+ : 버퍼에 NTP 기준 타임스탬프 메타 부착
    if src.find_property("add-reference-timestamp-meta") is not None:
        src.set_property("add-reference-timestamp-meta", True)
    else:
        print("[warn] add-reference-timestamp-meta 미지원 (GStreamer < 1.22)", flush=True)

    sink = pipeline.get_by_name("sink")
    sink.connect("new-sample", on_new_sample)

    loop = GLib.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()

    def on_message(_bus, msg):
        """에러·EOS 메시지를 받으면 루프를 끝내 재연결로 넘김."""
        t = msg.type
        if t == Gst.MessageType.ERROR:
            err, dbg = msg.parse_error()
            print(f"[error] {err.message} | {dbg}", flush=True)
            loop.quit()
        elif t == Gst.MessageType.EOS:
            print("[info] EOS 수신", flush=True)
            loop.quit()

    bus.connect("message", on_message)

    print(f"[info] 연결 시도: {RTSP_URL}", flush=True)
    pipeline.set_state(Gst.State.PLAYING)
    try:
        loop.run()
    finally:
        pipeline.set_state(Gst.State.NULL)
        bus.remove_signal_watch()


def main():
    """GStreamer 초기화 후 파이프라인을 실행하고, 끊기면 재연결을 반복."""
    global NTP_CAPS
    Gst.init(None)
    NTP_CAPS = Gst.Caps.from_string("timestamp/x-ntp")
    print(f"[info] GStreamer {Gst.version_string()}", flush=True)

    try:
        while True:
            try:
                run_once()
            except Exception as e:
                print(f"[error] {e}", flush=True)
            print(f"[info] {RECONNECT_SEC}초 후 재연결", flush=True)
            time.sleep(RECONNECT_SEC)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
