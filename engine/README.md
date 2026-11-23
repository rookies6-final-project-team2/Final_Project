# engine

AI 엔진: GStreamer RTSP 수신, 프레임별 타임스탬프 추출 → (예정) 사람 탐지·추적, ROI 판정, MQTT 발행

## 현재 상태 (`develop`)

- RTSP 수신 + 프레임별 PTS / NTP 절대시각 추출 + 자동 재연결까지 구현
- 다음 단계: `app/rtsp_receiver.py`의 `on_new_sample()` 안 `frame`(numpy BGR) → YOLO 입력, 검출 결과 + `ntp` 타임스탬프 → MQTT 발행

## 구조

```
engine/
├─ Dockerfile           # Ubuntu 24.04 + GStreamer 1.24 + Python(gi) + numpy
├─ .dockerignore
└─ app/
   └─ rtsp_receiver.py  # 수신 파이프라인, 타임스탬프 추출, 재연결
```

## 실행 방법

저장소 루트에서:
```powershell
docker compose up mediamtx gst-engine
```
로그에 `[frame 30] 1280x720 pts_s=... ntp=... delay_ms=...` 가 찍히면 정상. 각 값의 의미는 [`infra/README.md`](../infra/README.md)의 "수신 파이프라인" 참고.

코드를 고친 뒤 확인할 때는 다시 빌드:
```powershell
docker compose up --build gst-engine
```

## 환경변수

| 이름 | 기본값 | 설명 |
|---|---|---|
| `RTSP_URL` | `rtsp://mediamtx:8554/cam1` | 수신할 RTSP 주소. 실제 카메라는 `.env`에서만 교체 (계정 정보 커밋 금지) |
| `RTSP_LATENCY_MS` | `200` | 지터버퍼 최대 대기(ms) |
| `PRINT_EVERY` | `30` | N 프레임마다 로그 1줄 |

## 의존성 설치

- 모든 의존성은 `Dockerfile`에서 apt로 설치 (GStreamer 플러그인, `python3-gi`, `python3-numpy`)
- GStreamer Python 바인딩(`gi`)은 pip 설치가 까다로워 **컨테이너 안에서 개발·실행하는 것을 기본**으로 함
- YOLO 등 pip 패키지를 추가하게 되면 이 폴더에 `requirements.txt`를 만들고 `Dockerfile`에서 설치
- GPU 추론을 붙일 때는 베이스 이미지를 `nvidia/cuda:*-runtime-ubuntu24.04` 계열로 바꾸고 compose에 GPU 설정 추가 (infra와 함께 진행)

## 이미지

- 이름: `{DOCKERHUB_USER}/rookies6-engine:{APP_VERSION}` (규칙은 루트 `CONVENTION.md`)
- 개발 중 공유는 `develop` 태그, 릴리스 이미지는 릴리스 담당자가 올림
