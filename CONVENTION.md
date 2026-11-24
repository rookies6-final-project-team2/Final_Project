# 개발 컨벤션 (2조)

> 커밋·브랜치·PR·릴리스·이미지 태그 규칙. 바꿀 때는 `[docs(repo)]` 커밋으로 PR을 올리고 팀 합의 후 머지함

## 0. 저장소 구성 (모노레포)

하나의 저장소에 파트별 최상위 폴더를 두고, 폴더 이름을 커밋 범위와 똑같이 맞춤.

```
/
├── model/        주·야간 사람 탐지 모델 (학습·평가 코드, 데이터 처리 스크립트)
├── engine/       AI 엔진 (GStreamer 수신, 탐지·추적, ROI 판정, MQTT 발행)
├── vlm/          VLM 서버, 프롬프트
├── backend/      MQTT 구독·저장, API, SSE, 출동 알림 발송
├── web/          대시보드, 이벤트 페이지, 모바일 출동 알림 화면
├── infra/        MediaMTX 설정, AWS 배포 설정, 빌드·태그 스크립트, 인프라 문서
├── docs/
│   ├── interface/  MQTT 메시지 규격, API 정의서, VLM 입출력 (interface 범위)
│   └── ...         아키텍처, ER Diagram, 회의 결정사항 등 (repo 범위)
├── .github/      PR 템플릿, 이슈 템플릿, 워크플로
├── .gitignore
├── compose.yaml  전체 서비스 통합 실행 (루트에서 docker compose 실행)
├── .env.example
├── CONVENTION.md
└── README.md
```

- 각 파트의 `Dockerfile`은 그 파트 폴더 안에 두고(예: `engine/Dockerfile`), 여러 서비스를 함께 띄우는 `compose.yaml`은 루트에 둠
- 파트 폴더마다 `README.md`를 두고 실행 방법, 필요한 환경변수, 의존성 설치 방법을 적음
- 의존성 파일(`requirements.txt`, `package.json` 등)은 각 파트 폴더 안에 둠. 파트끼리 라이브러리 버전이 달라도 서로 영향이 없게 하기 위함
- 다른 파트 폴더의 코드는 직접 고치지 않고 이슈로 요청함. 꼭 고쳐야 하면 PR 리뷰어에 그 파트 담당자를 넣음
- 파트 간 데이터 형식은 `docs/interface/` 문서를 기준으로 함. 코드와 문서가 다르면 문서를 먼저 고치고 합의함
- `.gitignore`는 루트에 공통 규칙을 두고, 파트에만 필요한 규칙은 파트 폴더의 `.gitignore`에 추가함

## 1. 커밋 메시지

### 형식

```
[타입(범위)] 제목

본문: 무엇을, 왜 바꿨는지

Resolves: #이슈번호
See also: #이슈번호
```

- `(범위)`는 반드시 붙임. 범위는 변경한 파트 폴더 이름과 같게 씀

### 타입

| 타입 | 용도 |
| --- | --- |
| feat | 새 기능 |
| fix | 버그 수정 |
| perf | 지연 시간·처리 속도 등 성능 개선 |
| refactor | 기능 변화 없는 코드 개선 |
| exp | 모델 학습·VLM 프롬프트·파라미터 비교 실험 |
| docs | 문서 (API 정의서, MQTT 메시지 규격 등 포함) |
| test | 테스트 추가·수정 |
| chore | 빌드, 설정, 패키지, Docker |
| style | 포맷, 세미콜론 등 동작과 무관한 변경 |

### 범위 (파트)

| 범위 | 폴더 | 대상 |
| --- | --- | --- |
| model | `model/` | 주·야간 사람 탐지 모델 (학습·평가 코드, 데이터 처리) |
| engine | `engine/` | AI 엔진 (GStreamer 수신, 탐지·추적, ROI 판정, MQTT 발행) |
| vlm | `vlm/` | VLM 서버, 프롬프트, 입출력 |
| backend | `backend/` | MQTT 구독·저장, API, SSE, 출동 알림 발송 |
| web | `web/` | 대시보드, 이벤트 페이지, 모바일 출동 알림 화면 |
| infra | `infra/` | MediaMTX, Docker, AWS 배포 |
| interface | `docs/interface/` | 파트 간 인터페이스 (MQTT 메시지 규격, API 정의서, VLM 입출력) |
| repo | 루트, `docs/`(interface 제외) | 저장소 공통 파일 (`.gitignore`, `.github/`, `README.md`, `CONVENTION.md`, `compose.yaml` 등), 아키텍처·회의 결정사항 문서 |
- 커밋 하나는 범위 하나에만 해당되게 나눔
- 여러 파트를 함께 고쳐야 해서 나누기 어려우면 변경이 가장 큰 파트를 범위로 쓰고, 본문에 함께 바뀐 파트를 적음

### 규칙

- 제목은 50자 이내로 쓰고 끝에 마침표를 찍지 않음
- 제목은 명령형으로 씀 (한국어는 "배회 판정 추가", "RTSP 재연결 오류 수정"처럼 명사형으로 끝냄)
- 제목과 본문 사이에 빈 줄을 하나 둠
- 본문은 한 줄 72자 안팎에서 줄바꿈함
- 본문에는 무엇을 왜 바꿨는지 적음. 어떻게 바꿨는지는 코드가 설명함
- 문제점과 해결 과정이 있으면 본문에 적음 (데일리 스크럼·스프린트 회고에 옮길 수 있을 정도)
- `perf`, `exp` 커밋은 본문에 변경 전후 수치(지연 시간, 판정 결과, 탐지 성능 등)와 측정 조건을 적음. 성능 테스트 결과서와 기술 선택 근거 기록에 그대로 쓰기 위함
- 기술을 바꾼 경우(예: GStreamer → OpenCV 대체) 본문에 바꾼 이유를 적음
- 마지막 줄에 해결한 이슈(`Resolves`)와 참고 이슈(`See also`) 번호를 적음
- "수정", "fix", "작업 완료", "오늘 할 일 끝" 같은 모호한 메시지는 쓰지 않음
- 커밋 메시지는 한국어로 씀. 타입·범위 표기와 코드·파일명·기술명(GStreamer, ROI 등)은 영문 그대로 둠

### 커밋 단위

- 커밋 하나에는 한 가지 변경만 담음 (원자적 커밋)
- 여러 날의 작업을 한 커밋으로 몰아 올리지 않음
- 예: 침입 판정 / 배회 판정 / 이탈 판정을 각각 커밋해도 되고, 작은 작업이면 묶어도 됨
- 인터페이스(MQTT 메시지 규격, API 정의서, VLM 입출력) 변경은 구현 코드와 분리해 `[docs(interface)]` 등 별도 커밋으로 올림

### 커밋하지 않는 것 (`.gitignore` 관리)

- 자동 생성 파일, 빌드 결과물, 로그
- 데이터셋: 저장소 밖 외부 저장소에 보관하고, 저장소에는 보관 위치와 데이터셋 버전만 README 등에 적음
- 녹화 영상(MediaMTX 순환 녹화본 포함), 가중치 파일(`.pt` 등)
- 비식별 처리 전 촬영 영상·이미지 (IR 카메라 직접 촬영본 포함)
- `.env`, 카메라 RTSP 주소·계정, API 키 등 인증 정보 (환경변수로 분리하고 `.env.example`만 커밋)
- 중계 서버 등 Docker 이미지는 저장소가 아니라 Docker Hub로 공유함

### 예시

```
[feat(engine)] ROI 침입 판정 추가

사람 bbox 하단 중심점이 출입 통제 ROI 폴리곤 안에
N 프레임 이상 머물면 침입 이벤트를 MQTT로 발행하도록 함.
프레임 단위 판정 시 ROI 경계에서 깜빡임이 생겨 연속 프레임 조건을 둠.

Resolves: #12
See also: #8
```

```
[perf(engine)] GStreamer 수신 지연 단축

appsink 버퍼 설정을 바꿔 송출·수신 시각 차이를 줄임.
측정 조건: 가상 카메라 1대, 1080p 30fps, 5분 평균
변경 전 820ms → 변경 후 310ms

Resolves: #27
```

```
[docs(interface)] 검출 결과 MQTT 메시지에 track_id 추가

배회·이탈 판정에 같은 사람을 프레임 간에 이어서 봐야 해서
검출 결과 메시지에 추적 ID 필드를 추가함.
영향 파트: engine(발행), backend(구독·저장)

Resolves: #34
```

## 2. 브랜치 전략 (Git-flow 기반)

### 브랜치 종류

| 브랜치 | 역할 | 분기 | 병합 대상 |
| --- | --- | --- | --- |
| main | 발표·시연 가능한 안정 버전 | — | — |
| develop | 다음 버전 통합 개발 | main | main |
| feature/* | 기능 개발 | develop | develop |
| fix/* | develop 단계 버그 수정 | develop | develop |
| exp/* | 모델·VLM·파라미터 비교 실험 (머지하지 않을 수 있음) | develop | develop (채택 시) |
| release/* | 멘토링 점검·제출 전 안정화 (점검 직전에만 만듦) | develop | main, develop |
| fix/* (release용) | release 기간 중 버그 수정. 이름 규칙은 같고 **분기·PR 대상만 release 브랜치** | release/* | release/* |
| hotfix/* | main의 긴급 수정 | main | main, develop |

### 네이밍

- 작업자 이름이 아니라 기능 기준으로 지음
- `feature/{이슈번호}-{작업내용}` 형식
(예: `feature/12-roi-intrusion`, `fix/20-rtsp-reconnect`, `exp/31-vlm-person-crop`)
- release 브랜치는 내보낼 버전 번호로 지음 (예: `release/v0.1.0`). main에 붙일 태그와 이름을 맞추기 위함
- hotfix 브랜치는 `hotfix/{이슈번호}-{작업내용}` 형식으로 지음 (예: `hotfix/52-sse-disconnect`)

### 작업 흐름

1. 작업 전에 GitHub 이슈를 만듦
2. 최신 develop에서 브랜치를 만듦

```
git checkout develop
git pull origin develop
git checkout -b feature/12-roi-intrusion
```

3. 작업 중 develop 변경 사항을 반영함 (내 브랜치에서만)

```
git fetch origin
git pull --rebase origin develop
```

4. 원격에 올리고 develop 대상 PR을 만듦

```
git push origin feature/12-roi-intrusion
```

- 이미 원격에 올린 내 브랜치를 3번처럼 rebase했다면 일반 push가 거부됨. 이때는 **내 작업 브랜치에서만** 아래처럼 올림 (`--force` 대신 `--force-with-lease`를 써서 다른 사람이 그사이 올린 커밋을 덮어쓰지 않게 함)

```
git push --force-with-lease origin feature/12-roi-intrusion
```

5. 리뷰 승인 후 GitHub PR에서 머지함. 머지 방식은 merge commit(Create a merge commit)만 씀. squash·rebase 머지는 쓰지 않아 작업 브랜치의 커밋이 그대로 남게 함
6. 머지 후 더 이상 쓰지 않는 브랜치는 로컬·원격 모두 삭제함

```
git checkout develop
git pull origin develop
git branch -d feature/12-roi-intrusion
git push origin --delete feature/12-roi-intrusion
```

### 실험 브랜치 (exp/*)

- 프레임 샘플링 방식, 사람 영역 크롭, VLM 적용 범위, 탐지 모델 파라미터 등 비교 실험에 씀
- 채택된 결과만 develop에 PR로 올리고, 채택하지 않은 실험은 결과(수치·결론)를 이슈에 남긴 뒤 브랜치를 정리함

### 릴리스 일정

release 브랜치는 멘토링 점검·산출물 제출 직전에만 만들고, 평소에는 develop에서 개발함.

| 버전 | 목적 | release 브랜치 생성 (기능 동결) | main 머지·태그 |
| --- | --- | --- | --- |
| v0.1.0 | 3회차 멘토링(중간 점검): 엔진-백엔드-웹 기본 연동 | 12/16(수) | 12/19 점검 전 |
| v0.2.0 | 5회차 멘토링(산출물 점검): 통합 테스트·AWS 배포 | 27/01/20(수) | 27/01/23 점검 전 |
| v1.0.0 | 산출물 제출 (소스코드 GitHub) | 27/01/26(화) | 27/01/28 제출 전 |
| v1.0.x | 발표회 (27/02/02) | release 없음 | 제출 후 수정은 hotfix로만 처리 |
- release 브랜치 생성일은 점검 약 3일 전을 기준으로 하고, 팀 일정에 따라 조정함
- 릴리스 담당자 1명이 release 브랜치 생성부터 태그·이미지 푸시·브랜치 삭제까지 맡음 (인프라 담당 권장)

### 릴리스 흐름 (release/*)

1. **release 브랜치 생성 (기능 동결)**: 릴리스 담당자가 최신 develop에서 release 브랜치를 만들고 팀에 공지함. 이 시점까지 develop에 머지된 기능만 이번 버전에 들어감

```
git checkout develop
git pull origin develop
git checkout -b release/v0.1.0
git push origin release/v0.1.0
```

2. **release 기간 규칙**
    - release 브랜치에는 새 기능을 넣지 않음. 버그 수정, 설정값 조정, 문서 보완만 허용함
    - 시연 범위에 없는 미완성 기능은 코드를 지우지 않고 설정(환경변수 등)으로 끔
    - 다른 팀원은 develop에서 다음 기능 개발을 그대로 이어감
3. **버그 수정**: release 브랜치에서 fix 브랜치를 만들고, PR 대상을 release 브랜치로 지정함

```
git checkout release/v0.1.0
git pull origin release/v0.1.0
git checkout -b fix/41-roi-boundary-flicker
# 수정 후
git push origin fix/41-roi-boundary-flicker
# GitHub에서 base: release/v0.1.0 으로 PR 생성
```

4. **릴리스 후보(RC) 검증**: 릴리스 담당자가 release 브랜치 기준으로 RC 이미지(`v0.1.0-rc.1`, `rc.2` …)를 빌드·푸시하고, 그 이미지로 통합 테스트와 시연 리허설을 함. 버그를 고칠 때마다 RC 번호를 올림
5. **버전 반영 커밋**: 검증이 끝나면 `compose.yaml`의 `APP_VERSION` 기본값과 `.env.example`의 버전을 바꿔 커밋함 (예: `[chore(repo)] 버전 v0.1.0 반영`). `.env`는 커밋되지 않으므로 여기에 적은 값만으로는 팀원에게 반영되지 않음
6. **main 머지**: `release/v0.1.0` → `main` PR을 만들고, 각 파트 메인 담당자 확인 후 merge commit으로 머지함
7. **태그 생성**: main의 머지 커밋에 태그를 붙이고 푸시함. 마지막으로 통과한 RC 이미지에 정식 버전 태그를 붙임 (아래 "버전 태그 규칙" 참고)

```
git checkout main
git pull origin main
git tag -a v0.1.0 -m "3회차 중간 점검: 엔진-백엔드-웹 기본 연동"
git push origin v0.1.0
```

8. **develop 반영**: `release/v0.1.0` → `develop` PR을 만들어 release 기간의 수정 사항을 develop에 머지함. 빠뜨리면 다음 버전에서 같은 버그가 다시 생기므로 7번과 같은 날 처리함
    - 충돌이 나면 release 브랜치에서 임시 브랜치(`merge/v0.1.0-to-develop`)를 만들어 develop을 머지하고 충돌을 해결한 뒤 그 브랜치로 PR을 올림
9. **정리**: GitHub Releases에 태그 기준 릴리스 노트(포함 기능, 수정한 버그, 알려진 문제, 시연 범위)를 작성하고, release 브랜치를 삭제함. 태그가 남으므로 브랜치를 지워도 해당 시점 코드는 언제든 찾을 수 있음

### 긴급 수정 흐름 (hotfix/*)

main에 올라간 버전(특히 1/28 제출 후 2/2 발표 전)에서 문제가 생기면 hotfix로만 고침.

1. main에서 hotfix 브랜치를 만듦

```
git checkout main
git pull origin main
git checkout -b hotfix/52-sse-disconnect
```

2. 수정 후 `main` 대상 PR을 만들고 merge commit으로 머지함
3. 버전 셋째 자리를 올려 태그를 붙이고 이미지도 같은 버전으로 푸시함 (예: `v1.0.0` → `v1.0.1`)
4. 같은 hotfix 브랜치로 `develop` 대상 PR을 만들어 반영함. 열려 있는 release 브랜치가 있으면 그쪽에도 반영함
5. hotfix 브랜치를 삭제함

### 버전 태그 규칙

> 한 줄 요약: 멘토링 점검·제출 때마다 main에 버전 번호(`v0.1.0` 등)를 붙여, 그 시점의 코드를 나중에도 그대로 꺼내 볼 수 있게 함
> 

**버전 번호 읽는 법** (`v0.2.1` = 첫째.둘째.셋째 자리)

| 자리 | 언제 올리나 | 예 |
| --- | --- | --- |
| 첫째 | 최종 제출 버전부터 1. 그 전까지는 0 | `v0.2.0` → `v1.0.0` |
| 둘째 | 멘토링 점검·제출로 릴리스할 때마다 1씩 | `v0.1.0` → `v0.2.0` |
| 셋째 | main에 올린 뒤 긴급 수정(hotfix)할 때마다 1씩 | `v1.0.0` → `v1.0.1` |

**이번 프로젝트의 버전 흐름**

| 시점 | 버전 |
| --- | --- |
| 12/19 중간 점검 | `v0.1.0` |
| 중간 점검 후 main 긴급 수정이 생기면 | `v0.1.1` |
| 27/01/23 산출물 점검 | `v0.2.0` |
| 27/01/28 산출물 제출 | `v1.0.0` |
| 제출 후 발표 전 긴급 수정이 생기면 | `v1.0.1` |

**규칙**

- 태그는 release·hotfix를 main에 머지한 직후, main에만 붙임
- 태그 메시지에 어떤 점검용 버전인지 적음
- 한 번 붙인 태그는 지우거나 옮기지 않음. 잘못됐으면 다음 번호로 새로 붙임

```
git checkout main
git pull origin main
git tag -a v0.1.0 -m "3회차 중간 점검: 엔진-백엔드-웹 기본 연동"
git push origin v0.1.0
```

### Docker 이미지 태그 규칙

> 한 줄 요약: Docker 이미지에도 코드와 똑같은 버전 번호를 붙임. "v1.0.0으로 띄워"라고 하면 코드와 모든 이미지가 한 번에 정해지게 하기 위함
> 

**이미지 이름**

- `{Docker Hub 계정}/{프로젝트명}-{파트}` 형식으로 지음
- 계정: `.env`의 `DOCKERHUB_USER` (현재 `ekrong01`, 팀 Organization을 만들면 그 이름으로 변경)
- 프로젝트명: `rookies6`
- 파트: `mediamtx`, `engine`, `vlm`, `backend`, `web`
- 예: `ekrong01/rookies6-engine:v0.1.0`
- 가상 카메라는 지금은 강사님 이미지(`dockisig/mediamtx-cam1:1.1.0`)를 그대로 씀. 설정을 바꿔 직접 빌드하게 되면 `{계정}/rookies6-mediamtx`로 올림

**이미지에 붙이는 태그 3종류**

| 태그 | 용도 | 덮어써도 되나 |
| --- | --- | --- |
| `develop` | 개발 중 최신 develop 상태 테스트 | 됨 |
| `v0.1.0-rc.1`, `v0.1.0-rc.2` … | release 기간에 검증하는 후보 버전 (rc = 릴리스 후보). 버그를 고칠 때마다 번호를 올림 | 안 됨 (새 번호로) |
| `v0.1.0` | 정식 버전. 시연·배포에 씀 | 절대 안 됨 |
- `latest` 태그는 쓰지 않음. 누가 언제 덮어썼는지 알 수 없어 시연 직전에 다른 이미지로 바뀔 수 있기 때문
- rc 태그는 이미지에만 붙이고, Git 태그로는 만들지 않음

> Windows PowerShell에서는 아래 예시의 줄 끝 `\` 대신 백틱(`` ` ``)을 쓰거나 한 줄로 이어서 씀
>
> ```
> docker buildx imagetools create -t ekrong01/rookies6-engine:v0.2.0 ekrong01/rookies6-engine:v0.2.0-rc.2
> ```

**"태그만 추가"란?**

이미지 내용은 그대로 두고 이름표만 하나 더 다는 것. 다시 빌드하지 않으므로 시간이 거의 들지 않음. 아래 두 경우에 씀.

- 이번 릴리스에서 코드가 바뀌지 않은 파트의 이미지
- 검증을 통과한 rc 이미지를 정식 버전으로 만들 때

```
# 기존 이미지(오른쪽)에 새 태그(-t)를 추가
docker buildx imagetools create \
  -t {계정}/{프로젝트명}-mediamtx:v0.2.0 \
  {계정}/{프로젝트명}-mediamtx:v0.1.0
```

**릴리스 때 이미지 처리 순서 (`v0.2.0` 예시)**

1. release 브랜치를 만든 뒤, 모든 파트 이미지에 `v0.2.0-rc.1` 태그를 붙여 Docker Hub에 올림
    - 코드가 바뀐 파트(예: engine): 새로 빌드해서 올림
    - 코드가 바뀌지 않은 파트(예: mediamtx): 이전 정식 버전 `v0.1.0`에 태그만 추가함
2. rc.1 이미지로 통합 테스트·시연 리허설을 함. 버그를 고치면 1번과 같은 방식으로 모든 이미지에 `rc.2`를 붙여 다시 테스트함
3. 테스트를 통과하면, 마지막 rc 이미지에 정식 태그 `v0.2.0`을 추가함. 새로 빌드하지 않으므로 테스트한 이미지와 배포하는 이미지가 같음

```
# 마지막으로 통과한 rc.2에 정식 버전 태그 추가 (파트마다 반복)
docker buildx imagetools create \
  -t {계정}/{프로젝트명}-engine:v0.2.0 \
  {계정}/{프로젝트명}-engine:v0.2.0-rc.2
```

4. main 머지 후 Git에도 `v0.2.0` 태그를 붙임 (위 "버전 태그 규칙" 참고)

※ 첫 릴리스 `v0.1.0`은 이전 버전이 없으므로 모든 파트 이미지를 새로 빌드함

**docker-compose에서 쓰는 법**

이미지 버전은 `APP_VERSION` 환경변수 하나로 관리함. 버전을 바꾸거나 이전 버전으로 되돌릴 때 이 값만 고침.

```yaml
# compose.yaml (저장소 루트)
services:
  gst-engine:
    image: ${DOCKERHUB_USER}/rookies6-engine:${APP_VERSION:-develop}
  backend:
    image: ${DOCKERHUB_USER}/rookies6-backend:${APP_VERSION:-develop}
```

- `:-develop` 은 `.env`에 값이 없을 때 쓰는 기본값. 릴리스 때 이 기본값과 `.env.example`을 정식 버전으로 바꿔 커밋함

```
# .env (저장소 루트, Git에 올리지 않음)
APP_VERSION=v0.2.0

# 문제가 생겨 v0.1.0으로 되돌릴 때: 값을 v0.1.0으로 바꾸고 다시 띄움
docker compose up -d
```

**기타**

- 이미지 빌드·태그 작업은 GitHub Actions로 자동화함 (`.github/workflows/`). develop 머지 시 `develop` 태그, release 브랜치에서 수동 실행 시 rc 태그, main에 Git 태그를 푸시하면 정식 태그가 붙음. 릴리스 담당자는 rc 실행과 Git 태그 푸시만 맡음
- Docker Hub 로그인 정보(비밀번호·액세스 토큰)는 저장소에 넣지 않음. 자동화할 경우 GitHub Secrets에 등록함. 계정 이름(`DOCKERHUB_USER`)은 이미지 이름에 드러나는 공개 정보라 `.env.example`에 적어도 됨

### 규칙

- main, develop, release/*에는 직접 push하지 않고 반드시 PR을 거쳐 머지함 (GitHub 브랜치 보호 설정)
- PR 머지는 merge commit 방식으로 통일함 (release·hotfix 브랜치를 main에 머지할 때도 동일)
- rebase는 머지 전 내 작업 브랜치에서만 함. 다른 사람이 쓰는 공유 브랜치(develop, main)에서는 하지 않음
- 공유 브랜치의 히스토리를 바꾸지 않음 (force push 금지)
- 머지가 끝나 더 이상 쓰지 않는 브랜치는 바로 삭제함. 커밋은 merge commit으로 develop·main에 남으므로 브랜치를 지워도 작업 이력은 유지됨
- main, develop은 삭제하지 않음

## 3. PR·코드 리뷰

- PR 하나는 이슈 하나에 대응시킴
- PR 제목도 커밋과 같은 `[타입(범위)] 제목` 형식으로 씀
- PR 본문에 변경 내용, 테스트 방법, 관련 이슈 번호를 적음
- `perf`, `exp` PR은 변경 전후 비교 수치를 PR 본문에 적음
- AI 리뷰(CodeRabbit 등) 1차 확인 후 팀원 1~2명의 승인을 받음
- 리뷰어는 같은 파트의 메인·서브 담당자를 우선 지정함
- 다른 파트 폴더를 건드린 PR은 그 파트 담당자를 리뷰어에 넣음
- 인터페이스(MQTT 메시지 규격, API 정의서, VLM 입출력)를 바꾸는 PR은 해당 인터페이스를 쓰는 파트 담당자를 리뷰어로 반드시 넣고, 팀장에게 공유함

## 4. 주석

- 메소드·함수마다 역할을 한 줄로 적음
- ROI 판정 기준값(체류 시간 등), 프레임 수 등 임계값에는 값을 정한 근거를 주석으로 적음
- AI가 코드를 수정하면 주석도 함께 갱신됐는지 확인함
