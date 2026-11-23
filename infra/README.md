# Docker GStreamer 환경 구축 가이드

가상 카메라 `dockisig/mediamtx-cam1:1.1.0`(MediaMTX)에서 RTSP 영상을 받아
**GStreamer로 프레임별 타임스탬프를 추출하는 컨테이너**를 만들고 Docker Hub에 push하는 과정

```
[mediamtx-cam1 컨테이너]                  [gst-engine 컨테이너]
 cam1.mp4 ──ffmpeg 반복송출──▶ MediaMTX ──RTSP :8554/cam1──▶ rtspsrc → 디코딩 → appsink
                              │                              └ 프레임 + PTS + NTP 절대시각
                              └─WebRTC :8889/cam1──▶ 브라우저(웹 대시보드)
```

---

## 1. 폴더 구조

> 이 문서는 저장소 `infra/` 에 있지만, **모든 명령은 저장소 루트(compose.yaml 있는 곳)에서 실행**합니다.

```
(저장소 루트)/
├─ compose.yaml                 # mediamtx + gst-engine 함께 실행
├─ .env.example                 # 복사해서 .env 로 사용 (Docker Hub ID, 태그 등)
├─ infra/
│  └─ README.md                 # 이 문서
└─ engine/                      # AI 엔진 (현재: GStreamer 수신부, 자세한 내용은 engine/README.md)
   ├─ Dockerfile                # GStreamer 1.24 + Python 이미지
   ├─ .dockerignore
   └─ app/
      └─ rtsp_receiver.py       # RTSP 수신 + 타임스탬프 추출 + 자동 재연결
```

---

## 2. 가상 카메라(MediaMTX) 먼저 띄워보기

### 2-1. 이미지 받기

```powershell
docker pull dockisig/mediamtx-cam1:1.1.0
```

이 이미지 구성 (Docker Hub 레이어 기준)
- Alpine 3.24 + FFmpeg + MediaMTX 실행파일(`ENTRYPOINT ["/mediamtx"]`)
- `/mediamtx.yml` 설정 파일, `/videos/cam1.mp4` 영상
- `/windows/` 아래에 `compose.yaml`, `run_cam1.cmd`, `run_cam1.py` 원본 포함

### 2-2. 설정 파일 확인 (스트림 경로·포트 확인용)

```powershell
docker run --rm --entrypoint cat dockisig/mediamtx-cam1:1.1.0 /mediamtx.yml
```
`paths:` 아래 이름이 스트림 경로. 이 문서는 `cam1`로 가정함
다른 이름이면 `.env`의 `RTSP_URL` 끝부분만 수정하면 됨

> 설정을 바꿔야 할 때(순환 녹화, Playback API 등)는 위 명령 결과를 `infra/mediamtx/mediamtx.yml`로 저장해 수정하고,
> `compose.yaml`의 mediamtx 서비스에 `volumes: ["./infra/mediamtx/mediamtx.yml:/mediamtx.yml:ro"]`를 추가합니다.

### 2-3. 단독 실행

> `docker compose`로 이미 띄워 둔 상태면 이름·포트가 겹쳐 실패합니다. 먼저 `docker compose down` 하세요.

```powershell
docker run -d --name mediamtx -p 8554:8554 -p 8888:8888 -p 8889:8889 -p 8189:8189/udp -p 9997:9997 -p 9996:9996 dockisig/mediamtx-cam1:1.1.0
```

| 옵션 | 의미 |
|---|---|
| `-d` | 백그라운드 실행 (터미널을 바로 돌려받음) |
| `--name mediamtx` | 컨테이너 이름. 이후 `docker logs mediamtx`, `docker rm -f mediamtx`처럼 이름으로 다룸 |
| `-p 8554:8554` | `PC 포트:컨테이너 포트` 연결. PC의 `localhost:8554`로 들어오면 컨테이너 8554로 전달 |
| `-p 8189:8189/udp` | WebRTC 영상 데이터는 UDP로 오가므로 `/udp`를 반드시 붙임 |

**실행 확인**
```powershell
docker ps                     # STATUS 가 Up ... 이면 실행 중
docker logs -f mediamtx       # Ctrl+C 로 로그 보기 종료 (컨테이너는 계속 실행됨)
```
로그에 아래와 비슷한 줄이 보이면 정상입니다.
- `[RTSP] listener opened on :8554` : RTSP 서버 열림
- `[path cam1] runOnInit command started` : 내장 FFmpeg가 cam1.mp4 반복 송출 시작
- `is publishing to path 'cam1'` : cam1 경로에 영상이 들어오는 중 (이 줄이 있어야 수신 가능)

| 포트 | 용도 |
|---|---|
| 8554 | RTSP – AI 엔진(GStreamer), VLC |
| 8889 (+8189/udp) | WebRTC – 웹 대시보드 |
| 8888 | HLS |
| 9997 | Control API |
| 9996 | Playback API (녹화 구간 재생) |

### 2-4. 확인

- VLC → *미디어 → 네트워크 스트림 열기* → `rtsp://localhost:8554/cam1`
- 브라우저 → `http://localhost:8889/cam1` (WebRTC)
- (API 켜진 경우) 브라우저 → `http://localhost:9997/v3/paths/list` → `cam1`의 `"ready": true` 확인

확인했으면 정리:
```powershell
docker rm -f mediamtx
```

---

## 3. GStreamer 이미지 이해하기 (`engine/Dockerfile`)

| 패키지 | 들어있는 것 | 왜 필요한가 |
|---|---|---|
| gstreamer1.0-tools | `gst-launch-1.0`, `gst-inspect-1.0` | 파이프라인 테스트 |
| plugins-base | `videoconvert`, `appsink` | 색공간 변환, 파이썬으로 프레임 꺼내기 |
| plugins-good | `rtspsrc`, `rtph264depay` | **RTSP 수신 핵심** |
| plugins-bad | `h264parse`, `h265parse` | 스트림 파싱 |
| plugins-ugly | `x264enc` 등 | 인코딩(필요 시) |
| libav | `avdec_h264` | H.264 디코딩 |
| python3-gi, python3-gst-1.0, gir1.2-* | `import gi` | 파이썬에서 GStreamer 사용 |
| python3-numpy | | 프레임 → numpy 배열 (YOLO 입력) |

베이스를 **Ubuntu 24.04**로 한 이유: GStreamer **1.24**가 들어 있어서
`rtspsrc add-reference-timestamp-meta`(1.22+)로 **송출측 NTP 절대시각을 프레임마다 받을 수 있음** → 수행계획서의
"프레임별 타임스탬프로 녹화 구간과 검출 결과 매칭", "송출·수신 시각 차이 측정"에 바로 쓰임

### 수신 파이프라인 (`engine/app/rtsp_receiver.py`)
```
rtspsrc location=rtsp://mediamtx:8554/cam1 latency=200 protocols=tcp
  ! rtph264depay ! h264parse ! avdec_h264 ! videoconvert
  ! video/x-raw,format=BGR
  ! appsink emit-signals=true max-buffers=1 drop=true sync=false
```
- `protocols=tcp` : Docker/Windows 환경에서 UDP 패킷 손실·방화벽 문제 회피
- `max-buffers=1 drop=true sync=false` : 추론이 느려도 **항상 최신 프레임만** 처리 (지연 누적 방지)
- `format=BGR` : OpenCV/YOLO가 바로 쓰는 형식
- 에러/EOS 시 3초 후 **자동 재연결** (스트림 장애 복구 요구사항)

로그 예시 (실제 `docker compose up` 실행 출력):
```
gst-engine  | [info] GStreamer GStreamer 1.24.2
gst-engine  | [info] 연결 시도: rtsp://mediamtx:8554/cam1
gst-engine  | [frame 30] 1280x720 pts_s=2.008 ntp=2026-11-23T06:04:17.294748+00:00 delay_ms=8.8 mean=81.5
gst-engine  | [frame 60] 1280x720 pts_s=4.008 ntp=2026-11-23T06:04:19.294748+00:00 delay_ms=7.9 mean=81.7
```

**[info] 줄**

| 로그 | 의미 |
|---|---|
| `gst-engine  \|` | compose가 붙여주는 접두어. 어느 컨테이너의 로그인지 표시 |
| `GStreamer 1.24.2` | 컨테이너 안 GStreamer 버전. 1.22 이상이어야 `ntp` 값을 받을 수 있음 |
| `연결 시도: rtsp://...` | 접속하는 RTSP 주소 (`.env`의 `RTSP_URL`). 연결 실패 시 3초마다 이 줄이 반복됨 |

**[frame] 줄의 각 변수** (`[frame 60]` 줄 기준)

| 변수 | 예시 값 | 의미 | 활용 |
|---|---|---|---|
| `frame` | `60` | 엔진 시작 후 받은 **프레임 누적 순번** (재연결해도 이어서 셈). `PRINT_EVERY=30`이라 30프레임마다 1줄만 출력하며, 나머지 프레임도 모두 처리 중 | 수신이 끊기지 않고 진행되는지 확인 |
| 해상도 | `1280x720` | 디코딩된 영상 크기 (가로x세로). 이 크기의 BGR numpy 배열 `frame`이 만들어짐 | YOLO 입력 크기, 바운딩 박스 좌표 기준 |
| `pts_s` | `4.008` | **PTS(Presentation Time Stamp)**, 연결 시점부터 센 스트림 내부 **상대 시각(초)**. 재연결하면 0부터 다시 시작 | 프레임 간격 계산. 30프레임에 2초 → **15fps**. `ntp`가 없을 때 대체값 |
| `ntp` | `2026-11-23T06:04:19.294748+00:00` | 이 프레임이 송출측(MediaMTX)에서 나간 **절대 시각**. RTCP SR(Sender Report)로 계산되며 **UTC 기준**(`+00:00`) → 한국 시간 **15:04:19.29** | 녹화 구간·검출 결과 매칭, MQTT 메시지의 타임스탬프 |
| `delay_ms` | `7.9` | (엔진이 프레임을 받아 디코딩까지 끝낸 시각) − `ntp` 시각. 단위 ms | 수신 지연. 구조 변경 전후 지연 비교 지표 |
| `mean` | `81.7` | 프레임 전체 픽셀 밝기 평균 (0=검정 ~ 255=흰색) | 영상이 실제로 디코딩되는지 확인용. 0·255에 고정되면 영상 깨짐/빈 화면. YOLO 연결 후 삭제 가능 |

**참고 사항**
- 연결 직후 1~3초는 `ntp=N/A (RTCP SR 수신 전)`으로 나오고 `delay_ms`도 빠집니다. 송출측이 RTCP SR을 처음 보내기 전이라 정상입니다.
- `delay_ms`는 **MediaMTX → 네트워크 → 엔진 수신·디코딩** 구간입니다. 가상 카메라는 MediaMTX가 자기 시계로 NTP를 붙이기 때문에 카메라 촬영 시점부터의 지연이 아닙니다. 실제 IP 카메라는 카메라가 NTP를 보내므로 (카메라 NTP 설정이 맞다면) 촬영 시점부터의 지연에 가까워집니다.
- `delay_ms`는 송출측과 엔진의 시계를 비교하는 값이라 **같은 PC**에서 돌릴 때 정확합니다. 서버가 나뉘면(예: AWS) 양쪽 NTP 시간 동기화가 맞아야 합니다.
- `latency=200`인데 지연이 약 8ms인 것은 정상입니다. 지터버퍼는 패킷이 빠졌을 때만 최대 200ms를 기다리고, 순서대로 온 패킷은 바로 넘깁니다.
- 아직 YOLO 추론 시간은 포함되지 않았습니다. 성능 결과서에는 **수신 지연(`delay_ms`) + 추론 시간 + MQTT 발행 시간**으로 나눠 기록하면 비교가 깔끔합니다.

---

## 4. 로컬에서 빌드·실행 (compose로 한 번에)

### 4-1. `.env` 만들기

```powershell
copy .env.example .env
notepad .env
```
기본값(`DOCKERHUB_USER=ekrong01`, `APP_VERSION=develop`)을 **그대로 두면** 팀 공용 이미지를 받아 씁니다.
본인 계정으로 따로 테스트 이미지를 push할 때만 `DOCKERHUB_USER`를 본인 ID로 바꾸세요.

### 4-2. 실행

```powershell
docker compose pull      # 팀 공용 이미지 받기 (빌드 없이 바로 실행할 때)
docker compose up
```
엔진 코드를 고쳐서 내 PC에서 다시 빌드할 때는:
```powershell
docker compose up --build
```
- 첫 빌드는 apt 설치 때문에 3~5분 걸림
- `gst-engine` 로그에 `[frame N] ... ntp=... delay_ms=...` 가 찍히면 성공
- 종료: `Ctrl+C` → `docker compose down`

### 4-3. 백그라운드 실행 & 로그

```powershell
docker compose up -d
docker compose logs -f gst-engine
docker compose ps
```

### 4-4. 컨테이너 안에서 GStreamer 직접 테스트

```powershell
docker compose exec gst-engine bash
```
컨테이너 내부(bash):
```bash
gst-inspect-1.0 rtspsrc | grep reference
gst-launch-1.0 -v rtspsrc location=rtsp://mediamtx:8554/cam1 protocols=tcp latency=200 \
  ! rtph264depay ! h264parse ! avdec_h264 ! fakesink
```

---

## 5. Docker Hub에 Push

### 5-1. 로그인

```powershell
docker login
```

- 브라우저 인증 또는 ID/비밀번호 입력
- 비밀번호 대신 **Access Token 권장**: Docker Hub → Account settings → Personal access tokens → *Read & Write*

> 팀 공용 이미지(`ekrong01/...`)는 계정 소유자만 push할 수 있습니다. 다른 팀원은 본인 계정으로 테스트할 때만 `DOCKERHUB_USER`를 바꿔 사용하세요.

### 5-2. 방법 A – compose로 빌드한 이미지 그대로 push
`compose.yaml`의 `image:` 가 `${DOCKERHUB_USER}/rookies6-engine:${APP_VERSION}` 이므로 (`.env`의 `APP_VERSION`, 평소 개발 중에는 `develop`):

```powershell
docker compose build gst-engine
docker compose push gst-engine
```

### 5-3. 방법 B – docker 명령으로 직접

```powershell
$USER_ID = "mydockerid"     # 본인 Docker Hub ID
$VERSION = "develop"        # 평소: develop / 릴리스: v0.1.0-rc.1 등 (CONVENTION.md 참고)

docker build -t "$USER_ID/rookies6-engine:$VERSION" .\engine
docker push "$USER_ID/rookies6-engine:$VERSION"
```

### 5-4. 확인

- https://hub.docker.com/r/<ID>/rookies6-engine 에 태그가 보이면 완료
- 다른 팀원 PC에서:
  ```powershell
  docker pull ekrong01/rookies6-engine:develop
  ```

### 5-5. 팀 공유 팁
- 팀 공용 이미지는 인프라 담당 계정 `ekrong01`로 관리합니다. push는 인프라(릴리스 담당)가 하고, 자동화할 경우 이 계정의 Access Token을 GitHub Secrets에 등록합니다.
- 무료 계정은 Private 저장소 1개 → 영상·코드에 민감정보 없으면 Public, 있으면 Private
- **태그 규칙**: 개발 중 `develop`, 릴리스 후보 `v0.1.0-rc.1`, 정식 `v0.1.0`. `latest`는 쓰지 않음 (자세한 규칙은 루트 `CONVENTION.md`의 "Docker 이미지 태그 규칙")
- AWS(EC2 등)에 배포할 땐 `linux/amd64`로 빌드해야 함. Apple Silicon(M1~M4) 팀원은:
  ```bash
  docker buildx build --platform linux/amd64 -t mydockerid/rookies6-engine:develop --push ./engine
  ```

---

## 6. 실제 IP 카메라(IR)로 바꿀 때

코드 수정 없이 `.env`의 주소만 교체:
```
RTSP_URL=rtsp://계정:비밀번호@192.168.0.50:554/stream1
```
- 카메라 비밀번호는 **`.env`에만**, Git·이미지에 넣지 않기 (`.dockerignore`에 `.env` 포함됨)
- 카메라가 H.265면 파이프라인을 `rtph265depay ! h265parse ! avdec_h265` 로 변경

---

## 7. 자주 나는 오류

| 증상 | 원인 / 해결 |
|---|---|
| `Could not open resource for reading` / 연결 실패 반복 | 경로 이름 확인(2-2), mediamtx 컨테이너 실행 여부, 엔진에서는 `localhost`가 아니라 **`mediamtx`** (서비스 이름) |
| 호스트에서 직접 실행한 엔진이 연결 안 됨 | 컨테이너 밖에서는 `rtsp://localhost:8554/cam1` |
| `ntp=N/A` 가 계속 | 처음 1~3초는 정상. 계속이면 송출측이 RTCP SR을 안 보내는 것 → PTS로 대체 |
| `port is already allocated` | 8554 등 포트를 다른 프로그램이 사용 중 → `docker ps`로 기존 컨테이너 정리 |
| `denied: requested access to the resource is denied` (push) | `docker login` 안 됨, 또는 이미지 이름 앞 ID가 로그인 ID와 다름 |
| 브라우저 WebRTC 화면 안 나옴 | `8189/udp` 포트 매핑 확인, 영상에 B-frame 있으면 안 됨(ffmpeg `-bf 0`으로 재인코딩) |
| Windows에서 `.sh` 실행 시 `\r` 오류 | 줄바꿈 CRLF 문제 → VS Code 우측 하단 CRLF→LF |

---

## 8. 다음 단계 (AI 엔진 연결)

`rtsp_receiver.py`의 `on_new_sample()` 안에서 `frame`(numpy BGR)을 YOLO에 넘기고,
`ntp_unix`(없으면 `pts_s`)를 MQTT 메시지에 넣어 발행하면 수행계획서 2단계 구조가 완성됨
GPU 추론을 붙일 때는 베이스 이미지를 `nvidia/cuda:*-runtime-ubuntu24.04` 로 바꾸고
compose에 `gpus: all` (또는 `deploy.resources.reservations.devices`)을 추가하면 됨
