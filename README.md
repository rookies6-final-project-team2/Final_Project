# FinalProject - 2조 - VLM 기반 무인 영상 관제 솔루션

> GStreamer · YOLO · VLM · MQTT · MediaMTX(WebRTC/RTSP) 기반 AI 영상 관제 시스템
> 최종 프로젝트 · 2026.11 ~ 2027.02 (산출물 제출 **1/28 목** · 발표 **2/2 화**)

**처음 받았다면 → [⚡ 빠른 시작](#-빠른-시작)부터 따라 하세요.**

| 목차 | |
|---|---|
| [⚡ 빠른 시작](#-빠른-시작) | 처음 받은 팀원이 할 일 (체크리스트) |
| [1. 프로젝트 개요](#1-프로젝트-개요) | 목적 · 아키텍처 · 서비스/포트 · 디렉터리 |
| [2. 기술 스택](#2-기술-스택) | 기술 · 버전 · Docker 이미지 |
| [3. 개발 환경 세팅](#3-개발-환경-세팅) | 설치 · 저장소 세팅 · `.env` |
| [4. 파트별 시작](#4-파트별-시작) | model · engine · vlm · backend · web · infra |
| [5. 로컬 실행](#5-로컬-실행) | 실행 명령 · 주소 |
| [6. 협업 규칙](#6-협업-규칙) | 커밋 · 브랜치 · PR · 릴리스 (요약) |
| [7. 비밀정보 규칙](#7-비밀정보-규칙) | 계정 · Key · 촬영 데이터 관리 |
| [8. 산출물·일정](#8-산출물일정) | 멘토링 일정 · 산출물 · 릴리스 버전 |
| [9. 문제 해결](#9-문제-해결) | 자주 막히는 상황 |

---

## 팀 구성

멘토: 이소향

| 이름 | 역할 | 담당 |
|---|---|---|
| 윤수연 | 팀장 · 사람 탐지 모델 | 멘토 소통, 파트 간 인터페이스 합의, 일정·문서 총괄 / 주·야간 탐지 모델 |
| 김지우 | 사람 탐지 모델 | 주·야간(IR) 데이터 구축, 모델 학습·평가, 오탐 분석 |
| 이주혁 | 사람 탐지 모델 | 주·야간(IR) 데이터 구축, 모델 학습·평가, 오탐 분석 |
| 장지웅 | VLM (메인) · 웹 (서브) | VLM 서버, 프롬프트, 판정 실험 |
| 전승호 | 웹 (메인) | 실시간 대시보드, 이벤트 페이지, 출동 알림 화면 |
| 강찬식 | AI 엔진 + 백엔드 (메인) | GStreamer 수신, 탐지·추적, ROI 판정, MQTT / API |
| 정성재 | AI 엔진 + 백엔드 (메인) | GStreamer 수신, 탐지·추적, ROI 판정, MQTT / API |
| 서다영 | 인프라 · VLM (서브) · AI 엔진 + 백엔드 (서브) | MediaMTX, Docker, Docker Hub, AWS 배포 |

> 파트 안에서는 상황에 따라 유동적으로 협업합니다. (계획서 팀 구성)

---

## ⚡ 빠른 시작

> 명령은 **PowerShell** 에서, **저장소 최상위 폴더**(`compose.yaml` 있는 곳)에서 실행합니다.

- **1. 프로그램 설치** - Git, Docker Desktop (+ 내 파트 도구) → [3.1](#31-프로그램-설치)
- **2. 커밋 작성자 설정** - GitHub 계정 이메일과 같게 → [3.2](#32-저장소-최초-세팅-1회)
- **3. 저장소 받기** → [3.2](#32-저장소-최초-세팅-1회)
- **4. `.env` 만들기** - `copy .env.example .env` (기본값 그대로 사용 가능) → [3.3](#33-env-작성)
- **5. 가상 카메라 + 엔진 실행** - Docker Desktop 켜고 `docker compose pull` → `docker compose up` → [5장](#5-로컬-실행)
- **6. 내 파트 시작** - 파트 폴더의 `README.md` 확인 → [4장](#4-파트별-시작)

---

## 1. 프로젝트 개요

### 목적 (계획서 프로젝트 개요)

CCTV 관제 인력 1인이 수백 대의 카메라를 맡고 있어(전국 평균 481대) 모든 이벤트를 확인하기 어렵고, 객체 인식 중심의 기존 지능형 CCTV는 상황 맥락을 해석하지 못해 오탐이 많습니다. 특히 침입이 주로 일어나는 **야간**에는 탐지 자체가 어렵습니다.

| # | 목표 | 완성 기준 |
|---|---|---|
| ① | 주·야간 사람 탐지 + 이벤트 판정 | 주간·야간(IR) 영상에서 사람 탐지, ROI 규칙으로 **침입 · 배회 · 이탈** 실시간 판정 |
| ② | VLM 2차 판정 | 이벤트 원본 프레임 + 탐지 결과로 **상황 설명**과 **오탐 여부 · 출동 필요 여부** 제공 → 관제 인력이 확인할 이벤트 감소 |
| ③ | 관제 · 출동 알림 | 실시간 대시보드, 이벤트 페이지, 출동 필요 이벤트 **모바일 알림** |
| ④ | 근거 있는 성능 비교 | 구조 변경 전후 **지연 시간**, VLM 적용 전후 **확인 이벤트 수** 비교 |

**대상 시설**: 금은방 · 학교 · 무인매장 · 은행 등

### 아키텍처

```
[카메라: 가상(MediaMTX 반복 송출) / 실제 IR RTSP 카메라]
        │
        ▼
[MediaMTX 중계 서버] ──WebRTC──▶ [web: 실시간 대시보드]
        │ RTSP                              ▲ SSE
        ▼                                   │
[engine: GStreamer 수신 → 사람 탐지·추적 → ROI 판정] ──MQTT──▶ [backend: 구독·저장·API] ◀──▶ [vlm: 2차 판정]
                                                                      │
                                                                      └──▶ 모바일 출동 알림
```

- 엔진은 **프레임별 타임스탬프**(송출측 NTP 절대시각)를 검출 결과와 함께 MQTT로 발행합니다. 녹화 구간과 검출 결과는 이 시각으로 매칭합니다.
- 브라우저는 엔진·MQTT에 직접 붙지 않고 **반드시 backend를 거쳐** 이벤트를 받습니다. (계획서 비기능 요구사항)
- 실제 카메라는 **RTSP 주소만 교체**해서 연결합니다.

### 서비스 · 포트

| 서비스 (Compose 이름) | 포트 | 용도 | 상태 |
|---|---|---|---|
| `mediamtx` | 8554 | RTSP (엔진, VLC) | ✅ |
| | 8889 (+8189/udp) | WebRTC (웹 대시보드) | ✅ |
| | 8888 | HLS | ✅ |
| | 9997 / 9996 | Control API / Playback API (녹화 구간 재생) | ✅ (설정에 따라) |
| `gst-engine` | - | RTSP 수신 → 프레임·타임스탬프 추출 (외부 공개 없음) | ✅ 수신부 |
| MQTT 브로커 | 1883 | 엔진 → 백엔드 메시지 | 예정 |
| `backend` | 추후 확정 | API · SSE | 예정 |
| `vlm` | 추후 확정 | VLM 판정 | 예정 |
| `web` | 추후 확정 | 대시보드 | 예정 |

- 이 표의 서비스 이름·포트는 산출물 문서 전체에서 동일하게 씁니다. 바뀌면 이 표를 먼저 고칩니다.

### 디렉터리 구조

```
.
├── model/          # 주·야간 사람 탐지 모델 (학습·평가 코드, 데이터 처리 · 데이터·가중치 제외)
├── engine/         # AI 엔진 (GStreamer 수신, 탐지·추적, ROI 판정, MQTT 발행)
├── vlm/            # VLM 서버, 프롬프트
├── backend/        # MQTT 구독·저장, API, SSE, 출동 알림 발송
├── web/            # 대시보드, 이벤트 페이지, 모바일 출동 알림 화면
├── infra/          # MediaMTX 설정, AWS 배포 설정, 인프라 가이드(infra/README.md)
├── docs/           # 아키텍처·결정사항 / docs/interface/: MQTT·API·VLM 입출력 규격 (작성 시 생성)
├── .github/        # PR 템플릿, GitHub Actions 워크플로 (CI · 이미지 빌드·push)
├── compose.yaml    # 전체 서비스 통합 실행
├── .env.example    # 환경변수 샘플 (공개돼도 되는 값만)
├── CONVENTION.md   # 개발 컨벤션 (커밋 · 브랜치 · PR · 릴리스 · 이미지 태그)
└── README.md
```

- 폴더 이름 = 커밋 범위(scope)입니다. 각 파트의 `Dockerfile`, 의존성 파일, `README.md`는 그 파트 폴더 안에 둡니다. (컨벤션 0장)

---

## 2. 기술 스택

### 기술 · 버전

> **로컬 버전 = Docker 이미지 버전 = 산출물 문서 버전** 이 같아야 합니다. 버전이 확정·변경되면 이 표를 함께 갱신합니다.

| 구분 | 기술 · 버전 | 버전 기준 파일 | Docker 이미지 |
|---|---|---|---|
| 영상 중계 | MediaMTX, FFmpeg (RTSP · WebRTC · HLS · Playback) | `compose.yaml` | `dockisig/mediamtx-cam1:1.1.0` (강사 제공) |
| AI 엔진 | Python **3.12**, GStreamer **1.24**, numpy | `engine/Dockerfile` | `ubuntu:24.04` 기반 `rookies6-engine` |
| 탐지 모델 | YOLO(Ultralytics) 등, PyTorch, CUDA | `model/` (추후) | |
| VLM | 추후 확정 (모델 · 호스팅 방식) | `vlm/` (추후) | |
| Messaging | MQTT(Mosquitto), SSE | | |
| Backend / Frontend / DB / Mobile | 추후 확정 | | |
| Infra | Docker, Docker Compose, Docker Hub, AWS | | |
| Hardware | IR 지원 RTSP IP 카메라, GPU 서버 (Core Ultra 9 285K · RTX 5080 · 2TB) | | |

### Docker 이미지

이름 규칙: `{계정}/rookies6-{파트}:{버전}` · 버전은 `.env`의 `APP_VERSION` 하나로 관리합니다. (컨벤션 "Docker 이미지 태그 규칙")

| 서비스 | 이미지 | 비고 |
|---|---|---|
| 가상 카메라 | `dockisig/mediamtx-cam1:1.1.0` | 강사 제공 (직접 빌드하게 되면 `rookies6-mediamtx`) |
| AI 엔진 | `ekrong01/rookies6-engine:develop` | 현재 GStreamer 수신부까지 |

| 태그 | 용도 | 덮어써도 되나 |
|---|---|---|
| `develop` | 개발 중 최신 상태 | 됨 |
| `v0.1.0-rc.1` … | 릴리스 검증 후보 | 안 됨 (새 번호로) |
| `v0.1.0` | 정식 버전, 시연·배포용 | 절대 안 됨 |

- `latest` 태그는 쓰지 않습니다.

---

## 3. 개발 환경 세팅

> 명령은 **PowerShell** 기준입니다.

### 3.1 프로그램 설치

**전원 공통**

| 프로그램 | 용도 | 설치 |
|---|---|---|
| Git | 버전 관리 | <https://git-scm.com/downloads> |
| Docker Desktop | 가상 카메라 · 엔진 등 전체 서비스 실행 | <https://www.docker.com/products/docker-desktop/> (Windows: WSL2 기반) |
| VLC Player | RTSP 스트림 눈으로 확인 (선택) | <https://www.videolan.org/> |
| IDE | VS Code 등 | |

**내 파트만**

| 파트 | 설치 |
|---|---|
| engine | 추가 설치 없음 (GStreamer는 컨테이너 안에서 사용) |
| model · vlm | 추후 확정 (Python 버전 · GPU 드라이버 · CUDA) |
| backend · web | 프레임워크 확정 후 각 파트 README에 기재 |
| infra | Docker Hub 계정·Access Token, AWS 계정 |

**설치 확인**

```powershell
git --version
docker compose version     # v2 이상
docker run --rm hello-world
```

### 3.2 저장소 최초 세팅 (1회)

```powershell
# 1) 커밋 작성자 = GitHub 계정 이메일 (커밋 로그가 기여 기록)
git config --global user.name  "홍길동"
git config --global user.email "GitHub 에 등록된 이메일"

# 2) 저장소 받기
git clone <저장소 URL>
cd <저장소 폴더>
git checkout develop

# 3) 환경변수 파일
copy .env.example .env
```

### 3.3 `.env` 작성

`.env` 는 **저장소 최상위**(`compose.yaml` 옆)에 둡니다.

| 변수 | 누가 / 무엇을 | 기본값 |
|---|---|---|
| `DOCKERHUB_USER` | **팀 공통** 이미지 계정 (공개 정보) · 본인 계정으로 테스트 push할 때만 변경 | `ekrong01` |
| `APP_VERSION` | **팀 공통** 이미지 버전 · 평소 `develop`, 시연 때 정식 버전 | `develop` |
| `RTSP_URL` | 가상 카메라는 그대로 / **실제 카메라 연결 시 각자** 수정 (계정 포함 → `.env`에만) | `rtsp://mediamtx:8554/cam1` |
| `RTSP_LATENCY_MS`, `PRINT_EVERY` | 엔진 수신 설정 | `200`, `30` |

> ⚠️ 새 환경변수를 추가하면 `.env.example` 에 **이름과 공개 가능한 기본값만** 추가합니다.

---

## 4. 파트별 시작

| 파트 | 폴더 | 현재 상태 | 시작 문서 |
|---|---|---|---|
| 사람 탐지 모델 | `model/` | 데이터 확보 전략 수립 단계 | [model/README.md](model/README.md) |
| AI 엔진 | `engine/` | ✅ RTSP 수신 · 프레임별 타임스탬프 · 재연결 → 다음: YOLO 연결, MQTT 발행 | [engine/README.md](engine/README.md) |
| VLM | `vlm/` | 모델 · 호스팅 방식 검토 | [vlm/README.md](vlm/README.md) |
| 백엔드 | `backend/` | 프레임워크 · DB 확정 전 | [backend/README.md](backend/README.md) |
| 웹 | `web/` | 프레임워크 확정 전 · WebRTC 영상은 지금 테스트 가능 | [web/README.md](web/README.md) |
| 인프라 | `infra/` | ✅ 가상 카메라 + 엔진 이미지 구성 | [infra/README.md](infra/README.md) |

> - 프로젝트(프레임워크 뼈대)는 파트 **담당자 1명**이 생성해 PR로 올립니다. (동시에 생성하면 충돌)
> - 파트 간 데이터 형식(MQTT 메시지, API, VLM 입출력)은 `docs/interface/` 문서를 **먼저 합의**하고 개발합니다.
> - 다른 파트 폴더의 코드는 직접 고치지 않고 이슈로 요청합니다.

### 합류하는 팀원

```powershell
git checkout develop
git pull origin develop
docker compose pull
docker compose up                      # 가상 카메라 + 엔진

# 작업은 항상 이슈를 만든 뒤 새 브랜치에서
git checkout -b feature/<이슈번호>-<작업내용>
```

---

## 5. 로컬 실행

| 대상 | 명령 | 주소 |
|---|---|---|
| 가상 카메라만 | `docker compose up -d mediamtx` | RTSP `rtsp://localhost:8554/cam1` · WebRTC <http://localhost:8889/cam1> |
| 가상 카메라 + 엔진 | `docker compose up` | 엔진은 로그로 확인 (`[frame N] ... ntp=... delay_ms=...`) |
| 엔진 코드 수정 후 | `docker compose up --build gst-engine` | |

```powershell
docker compose ps                    # 상태 확인
docker compose logs -f gst-engine    # 엔진 로그
docker compose down                  # 중지
```

- 엔진 로그 값(`pts_s`, `ntp`, `delay_ms` 등)의 의미는 [infra/README.md](infra/README.md)의 "수신 파이프라인" 참고

---

## 6. 협업 규칙

> 전체 규칙은 **[CONVENTION.md](CONVENTION.md)** 를 따릅니다. 아래는 요약입니다.

### 6.1 브랜치 구조

```
main                         ← 발표·시연 가능한 안정 버전 · 직접 push 금지
 └── develop                 ← 통합 개발 · 작업 브랜치의 출발점이자 PR 대상
      ├── feature/이슈번호-작업내용     예) feature/12-roi-intrusion
      ├── fix/이슈번호-작업내용         예) fix/20-rtsp-reconnect
      └── exp/이슈번호-작업내용         예) exp/31-vlm-person-crop (채택 시에만 머지)
release/vX.Y.Z               ← 멘토링 점검·제출 직전에만 생성 (기능 동결)
hotfix/이슈번호-작업내용         ← main 긴급 수정 (제출 후 발표 전 등)
```

- 작업자 이름이 아니라 **기능 기준**으로 이름을 짓습니다.
- 머지는 **merge commit** 만 사용 (squash·rebase 머지 금지), 머지 후 브랜치는 삭제합니다.
- `main`, `develop`, `release/*` 는 PR로만 머지, 공유 브랜치 force push 금지

### 6.2 커밋 메시지

형식: `[타입(범위)] 제목` · 범위 = 파트 폴더 이름 (`model` `engine` `vlm` `backend` `web` `infra` `interface` `repo`)

| 타입 | 의미 | 예시 |
|---|---|---|
| `feat` | 새 기능 | `[feat(engine)] ROI 침입 판정 추가` |
| `fix` | 버그 수정 | `[fix(engine)] RTSP 재연결 오류 수정` |
| `perf` | 지연·속도 등 성능 개선 (**전후 수치 필수**) | `[perf(engine)] GStreamer 수신 지연 단축` |
| `exp` | 모델·프롬프트·파라미터 비교 실험 (**전후 수치 필수**) | `[exp(vlm)] 사람 영역 크롭 판정 비교` |
| `refactor` | 동작은 그대로, 코드 구조만 개선 | |
| `docs` | 문서 (인터페이스 규격 포함) | `[docs(interface)] 검출 결과 MQTT 메시지에 track_id 추가` |
| `test` · `chore` · `style` | 테스트 / 빌드·설정·Docker / 포맷 | `[chore(infra)] engine 이미지 develop 태그 반영` |

- 본문에 **무엇을, 왜** 바꿨는지, 마지막 줄에 `Resolves: #이슈번호`
- **한 커밋 = 한 범위 · 한 가지 변경**, 인터페이스 변경은 구현 코드와 분리해 커밋

### 6.3 작업 흐름

```powershell
git checkout develop
git pull origin develop
git checkout -b feature/12-roi-intrusion
# 작업 · 커밋
git pull --rebase origin develop     # PR 전 최신 develop 반영 (내 브랜치에서만)
git push origin feature/12-roi-intrusion
# GitHub에서 develop 대상으로 PR 생성
```

### 6.4 Pull Request

- 이슈 1개 = PR 1개, 제목은 커밋과 같은 `[타입(범위)] 제목` 형식
- 본문에 변경 내용 · 테스트 방법 · 관련 이슈 (`perf`·`exp`는 변경 전후 수치)
- AI 리뷰 1차 확인 후 팀원 1~2명 승인, 리뷰어는 같은 파트 메인·서브 담당자 우선
- 다른 파트 폴더나 인터페이스를 바꾸면 해당 파트 담당자를 리뷰어로 넣고 팀장에게 공유

### 6.5 스크럼

- 데일리 스크럼: 어제 한 일 / 오늘 할 일 / 막힌 점
- 주 단위 스프린트 · 회고, 평일 진행 상황 멘토 공유, 주말 온라인 스터디 (계획서 수행 기법)

---

## 7. 비밀정보 규칙

1. `.env`·키 파일·비밀번호는 **절대 커밋하지 않습니다.** 저장소에는 `.env.example` 만 둡니다.
2. `.env.example` 에는 **공개돼도 되는 값만** 적습니다. (`DOCKERHUB_USER` 같은 계정 이름은 이미지 이름에 드러나는 공개 정보라 괜찮음)
3. **카메라 RTSP 계정·비밀번호, VLM API Key, Docker Hub 비밀번호·토큰**은 `.env`(로컬)와 GitHub Secrets(자동화 시)에만 둡니다.
4. **직접 촬영한 영상·이미지는 비식별 처리 후** 사용하고, 원본·데이터셋·녹화본·가중치는 저장소에 올리지 않습니다. 외부 저장소에 두고 위치·버전만 파트 README에 적습니다.
5. 발표 자료·문서·캡처에 카메라 주소·계정·Key 가 보이지 않게 가립니다.
6. ⚠️ Key 나 계정 정보를 푸시했다면 **즉시 팀장·인프라에 알리고** 값을 교체합니다. (커밋 삭제만으로는 부족)

---

## 8. 산출물·일정

### 멘토링 일정 (계획서 주요 일정)

| 시점 | 회차 | 목표 |
|---|---|---|
| ~12/05 | 2회차 멘토링 (기술 지원) | 요구사항 정의, 중계 환경, GStreamer 시간 동기화 1차(12/01), 수행계획서·요구사항 정의서 제출(12/03) |
| ~12/19 | 3회차 (중간 점검) | 엔진-백엔드-웹 기본 연동, 주·야간 데이터 확보, IR 카메라 수령·촬영, VLM 선행 연구 |
| ~27/01/09 | 4회차 (기술 고도화) | 탐지 모델 튜닝·오탐 개선, VLM 고도화 실험, 출동 알림 연동 |
| ~27/01/23 | 5회차 (산출물 점검) | 통합 테스트, 성능 비교, AWS 배포 |
| 27/01/28 | 산출물 제출 | |
| 27/02/02 | 발표회 | |

### 릴리스 버전 (컨벤션 "릴리스 일정")

| 버전 | 목적 | release 생성 (기능 동결) | main 머지·태그 |
|---|---|---|---|
| v0.1.0 | 3회차 중간 점검 | 12/16(수) | 12/19 점검 전 |
| v0.2.0 | 5회차 산출물 점검 | 27/01/20(수) | 27/01/23 점검 전 |
| v1.0.0 | 산출물 제출 | 27/01/26(화) | 27/01/28 제출 전 |
| v1.0.x | 발표회 | release 없음 | 수정은 hotfix로만 |

### 산출물 (계획서 프로젝트 산출물)

| 시점 | 문서 |
|---|---|
| 12/03 제출 | 수행 계획서, 요구사항 정의서 |
| 개발 계획서 | WBS, API 정의서, MQTT 메시지 규격 |
| 중간 보고서 | 시스템 Architecture, ER Diagram |
| 완료 보고서 | 성능 테스트 결과서 (주·야간 탐지 성능 및 오탐 분석, VLM 판정 효과, 지연 시간 개선 전후 비교) |
| 기타 | 소스코드(GitHub), 중계 서버 Docker 이미지, 시연 영상, 멘토링 일지 |

**작성 규칙**
- 서비스 이름·포트·기술 버전은 [1장 서비스·포트](#서비스--포트)·[2장](#2-기술-스택) 표와 **일치**시킵니다.
- 성능 결과서의 수치는 `perf`·`exp` 커밋·PR에 남긴 **측정 조건과 전후 수치**를 그대로 씁니다.

---

## 9. 문제 해결

| 증상 | 원인 / 해결 |
|---|---|
| `docker` 명령이 응답 없음 | Docker Desktop 이 꺼져 있음 → 실행 후 재시도 |
| `docker compose pull` 시 `not found` | 이미지 이름·태그 오타 또는 `.env`의 `DOCKERHUB_USER`·`APP_VERSION` 확인 (태그 끝 `.` 등) |
| push 시 `insufficient_scope` / `access denied` | 로그인 계정과 이미지 이름 앞 계정이 다름 → `docker login -u <계정>` 다시, 토큰 권한 Read & Write 확인 |
| `port is already allocated` (8554 등) | 같은 포트를 쓰는 컨테이너가 이미 실행 중 → `docker ps` 후 `docker compose down` 또는 `docker rm -f mediamtx` |
| `The container name "/mediamtx" is already in use` | `docker run` 으로 띄운 컨테이너가 남아 있음 → `docker rm -f mediamtx` |
| 엔진 로그에 `연결 시도` 만 반복 | mediamtx 미실행 또는 스트림 경로 다름 → `docker compose ps`, 경로는 [infra/README.md](infra/README.md) 2-2 |
| 엔진 로그가 계속 `ntp=N/A` | 처음 1~3초는 정상. 계속이면 송출측 RTCP SR 미전송 → PTS로 대체 |
| 브라우저 WebRTC 화면이 안 나옴 | `8189/udp` 포트 확인, 영상에 B-frame 이 있으면 재인코딩(`-bf 0`) 필요 |
| 컨테이너 안 `.sh` 실행 시 `\r` 오류 | 줄바꿈 CRLF → LF 로 변경 |

더 자세한 오류 해결은 [infra/README.md](infra/README.md) "자주 나는 오류" 참고.
