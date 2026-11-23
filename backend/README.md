# backend

MQTT 구독·저장, DB, REST API, SSE 기반 실시간 알림, 출동 알림 발송.

- 입력: 엔진이 발행하는 MQTT 메시지 → 규격은 `docs/interface/mqtt_message_spec.md`
- 출력: 웹용 API / SSE → 규격은 `docs/interface/api_spec.md`
- 프레임워크·DB: 추후 확정 (확정되면 이 문서에 기록)
- 컨테이너화 시 `Dockerfile` 을 이 폴더에 두고 루트 `compose.yaml` 에 서비스 추가

## 실행 방법
(작성 예정)

## 환경변수
(작성 예정 · 값은 루트 `.env`에 두고 `.env.example`에 이름만 추가)

## 의존성 설치
(작성 예정 · 의존성 파일은 이 폴더 안에 둠: `requirements.txt` / `build.gradle` / `package.json` 등 프레임워크 확정 후)
