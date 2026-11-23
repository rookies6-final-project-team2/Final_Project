# =============================================================
# GStreamer RTSP 수신 엔진 이미지
#  - Ubuntu 24.04 (GStreamer 1.24) + Python GI 바인딩
#  - MediaMTX(RTSP) 스트림을 받아 프레임별 타임스탬프 추출
# =============================================================
FROM ubuntu:24.04

# apt 설치 중 대화형 질문(타임존 등) 차단
ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Seoul \
    PYTHONUNBUFFERED=1

# GStreamer 코어 + 플러그인 + Python 바인딩
#  - plugins-base : videoconvert, appsink 등
#  - plugins-good : rtspsrc, rtph264depay 등 (RTSP 수신 핵심)
#  - plugins-bad  : h264parse, h265parse 등
#  - plugins-ugly : x264 등
#  - libav        : avdec_h264 (FFmpeg 기반 디코더)
#  - python3-gi / gir1.2-gst-*  : Python 에서 `import gi` 로 GStreamer 사용
RUN apt-get update && apt-get install -y --no-install-recommends \
        gstreamer1.0-tools \
        gstreamer1.0-plugins-base \
        gstreamer1.0-plugins-good \
        gstreamer1.0-plugins-bad \
        gstreamer1.0-plugins-ugly \
        gstreamer1.0-libav \
        gstreamer1.0-rtsp \
        python3 \
        python3-gi \
        python3-gst-1.0 \
        gir1.2-gstreamer-1.0 \
        gir1.2-gst-plugins-base-1.0 \
        python3-numpy \
        tzdata \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app/ /app/

# 기본 수신 주소 (compose 에서는 서비스 이름 mediamtx 로 접근)
ENV RTSP_URL=rtsp://mediamtx:8554/cam1 \
    RTSP_LATENCY_MS=200 \
    PRINT_EVERY=30

CMD ["python3", "/app/rtsp_receiver.py"]
