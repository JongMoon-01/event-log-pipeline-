# event-log-pipeline-

## 프로젝트 개요

본 프로젝트는 라이브 서비스에서 발생하는 사용자 이벤트 로그를 기반으로
이벤트 생성 → 수집 → 저장 → 분석 → 시각화까지의 로그 파이프라인을 구축하는 것을 목표로 합니다.

단순 로그 저장이 아닌, 사용자 행동과 시스템 상태를 분석하여
서비스 개선 및 운영 의사결정에 활용할 수 있는 구조를 설계하였습니다.

## 실행 방법

repo clone -> event-log-pipeline/ 위치에서 빌드

### 폴더 구조

```
event-log-pipeline/
│
├── app/
│   ├── event_generator.py
│   ├── db.py
│   └── requirements.txt
│
├── db/
│   └── schema.sql
│
├── analysis/
│   ├── server_dashboard_queries.sql
│   └── instructor_dashboard_queries.sql
│
├── Dockerfile
├── docker-compose.yml
└── README.md
```

```
docker compose up --build
```

### DB 정보(테스트용)

```
Host: mariadb
Port: 3306
DB: edtech_event_db
User: edtech
Password: edtech1234
```


## 전체 아키텍처

실제로는 프론트 웹 서비스 혹은 앱에서 발생하는 이벤트가 API gate를 거쳐 kafka 같은 비동기 분산 메시징 시스템을 거쳐 DB로 적재됩니다.

이번 테스트에서는 프론트 단과 API gate를 생략 후 랜덤으로 이벤트를 발생시키는 event generator와 발생한 이벤트를 소비하고 분석하는 analysis를 배치해 간단한 아키텍쳐로 설계했습니다.

비동기 방식을 구현한 이유는 동기 방식에서는 다음과 같은 처리방식을 거쳐 이벤트 로그가 들어오게 되고, 해당 방식에서는 요청 하나가 처리될 때까지 서버 점유율을 차지하게 됩니다.

```
유저 요청 → 서버 → DB 저장 완료 → 응답
```

하지만 비동기 방식으로 처리할 경우 Producer는 이벤트를 생산만 하면되고 DB에 요청이 느려도 요청이 끝날때까지 서버 점유율을 차지하지 않으니 서비스는 계속 응답할 수 있게 됩니다.

```
유저 요청 → 서버 → Kafka에 적재 → 응답
                         ↓
                    Consumer가 나중에 DB 저장
```


### 라이브 서비스 아키텍쳐
```
User Action(Frontend)
→ Frontend Event SDK
→ Ingestion API
→ Kafka/Kinesis
→ Consumer
→ DB/S3
→ Analysis
→ Dashboard/Recommendation
```

### 로그 파이프라인 테스트용 아키텍쳐

```
[Log Generator]
   ↓ (Kafka Producer)
[Kafka Broker]
   ↓ (Consumer)
[Ingestion Service]
   ↓
[MariaDB]
   ↓
[Metabase Dashboard]
```

## 기술 스택

| 영역     | 기술                |
| ------ | ----------------- |
| 이벤트 생성 | Python            |
| 메시지 큐  | Kafka             |
| 데이터 저장 | MariaDB           |
| 데이터 처리 | Python (Consumer) |
| 시각화    | Metabase          |
| 환경 구성  | Docker Compose    |

## 2. 로그 저장 설계

본 프로젝트에서는 이벤트 로그 저장소로 MariaDB를 선택하였습니다.

이벤트 데이터는 단순 JSON 문자열로 저장하지 않고, 분석에 자주 사용되는 필드를 별도 컬럼으로 분리하였습니다. 예를 들어 event_type, event_level, user_id, lecture_id, created_at, response_time_ms는 SQL 집계 및 필터링에 자주 사용되므로 개별 컬럼으로 저장하였습니다.

반면 이벤트마다 달라질 수 있는 부가 정보는 metadata JSON 컬럼에 저장하여 확장성을 확보하였습니다.

MariaDB를 선택한 이유는 이벤트 타입별 발생 횟수, 유저별 이벤트 수, 시간대별 이벤트 추이, 에러 이벤트 비율과 같은 집계 분석을 SQL로 쉽게 수행할 수 있기 때문입니다. 또한 Azure에서는 더이상 지원하지 않아 MySQL로 마이그레이션 해야하지만 AWS에서는 아직 MariaDB RDBS를 지원하고 있어 추후 마이그레이션 작업이 가능합니다.

이벤트 타입은 향후 심각한 서버에 심각한 장애를 일으킬 수준이나 유저의 기본적인 인터랙션 로그 등을 구분하기 위해 설정해놓았습니다.

### 2.1. Database Schema(event_logs)

| Column | Type | Description |
|---|---|---|
| id | BIGINT, PK | 내부 저장용 ID |
| event_id | VARCHAR(100) | 이벤트 고유 ID |
| event_type | VARCHAR(50) | 이벤트 타입 |
| event_level | VARCHAR(20) | INFO / WARNING / ERROR |
| user_id | BIGINT | 사용자 ID |
| session_id | VARCHAR(100) | 사용자 세션 ID |
| course_id | BIGINT | 코스 ID |
| lecture_id | BIGINT | 강의 ID |
| page_url | VARCHAR(255) | 이벤트가 발생한 페이지 |
| device | VARCHAR(50) | 접속 디바이스 |
| browser | VARCHAR(50) | 브라우저 |
| duration_sec | INT | 영상 시청/행동 지속 시간 |
| response_time_ms | INT | 응답 시간 |
| success | BOOLEAN | 이벤트 성공 여부 |
| error_code | VARCHAR(100) | 에러 코드 |
| message | VARCHAR(500) | 이벤트 메시지 |
| metadata | JSON | 이벤트별 추가 정보 |
| created_at | DATETIME | 이벤트 발생 시간 |
| inserted_at | TIMESTAMP | DB 저장 시간 |

### 2.2. Event Types

| Event Type | Level | Description |
|---|---|---|
| PAGE_VIEW | INFO | 사용자가 페이지에 진입한 이벤트 |
| LECTURE_ENTER | INFO | 사용자가 강의 상세 또는 수강 화면에 진입한 이벤트 |
| VIDEO_PLAY | INFO | 사용자가 영상을 재생한 이벤트 |
| VIDEO_PAUSE | INFO | 사용자가 영상을 일시정지한 이벤트 |
| VIDEO_SEEK | INFO | 사용자가 영상 구간을 이동한 이벤트 |
| VIDEO_COMPLETE | INFO | 사용자가 영상을 끝까지 시청한 이벤트 |
| SUMMARY_VIEW | INFO | 사용자가 강의 요약을 조회한 이벤트 |
| QUIZ_START | INFO | 사용자가 퀴즈를 시작한 이벤트 |
| QUIZ_SUBMIT | INFO | 사용자가 퀴즈를 제출한 이벤트 |
| SLOW_RESPONSE | WARNING | 응답 시간이 기준보다 느린 이벤트 |
| ERROR_EVENT | ERROR | 시스템 또는 서비스 오류 이벤트 |

## 3. 데이터 집계 분석

저장된 이벤트 로그는 세 가지 관점으로 분석하였습니다.

첫 번째는 서버 안정성 관점입니다. 전체 이벤트 수, 이벤트 레벨별 비율, 에러 이벤트 비율, 시간대별 이벤트 추이, 응답 시간 평균, 에러 코드별 발생 횟수를 분석하였습니다. 이를 통해 서비스 운영 중 특정 시간대에 트래픽이나 에러가 집중되는지, 어떤 기능에서 응답 지연이 발생하는지 확인할 수 있습니다.

두 번째는 고객 지원(Customer Support) 관점이다. 유저별 이벤트 타임라인, 세션별 로그 흐름, 에러 로그, 응답 지연 이벤트를 분석하였습니다. 이를 통해 특정 사용자가 겪는 문제를 재현하고, 오류 발생 시점과 원인을 빠르게 추적할 수 있도록 하였습니다. 특히 user_id와 session_id를 기준으로 로그를 필터링하여 실제 고객 문의 상황에서 디버깅이 가능한 구조로 설계하였습니다.

세 번째는 강의 제공자 관점입니다. 강의별 재생 수, 일시정지 및 탐색 수, 퀴즈 시작률, 퀴즈 제출률, 요약 조회 수, 강의별 에러 발생 수를 분석하였습니다. 이를 통해 강의 제공자는 수강자가 어느 강의에서 많이 막히는지, 어떤 강의가 능동 학습으로 이어지는지, 어떤 콘텐츠의 개선이 필요한지 판단할 수 있습니다.

특히 강의별 학습 마찰 점수는 VIDEO_PAUSE, VIDEO_SEEK, ERROR 이벤트에 서로 다른 가중치를 부여하여 산출하였다. 이를 통해 단순 조회 수가 아니라 수강자가 학습 과정에서 겪는 어려움의 정도를 정량적으로 추정할 수 있도록 하였습니다.

### 3.1. Customer Support Dashboard

목적 : 사용자 문제 추적 및 디버깅

주요 기능
- 유저별 이벤트 타임라인 조회
- 세션 기반 로그 분석
- 에러 로그 필터링
- 느린 요청 탐지

<center>
<img src="/assets/img/CS1.png" width="720" height=""/>
<p><b>[그림1]. Customer Support Dashboard </b></p>
</center>

### 3.2. Instructor Analytics Dashboard

목적 : 강의 품질 및 학습 행동 분석

강의 평가에 사용되는 지표는 다음과 같습니다.

| 지표       | 설명                          |
| -------- | --------------------------- |
| 시청 수     | VIDEO_PLAY 이벤트 수            |
| 완주율      | VIDEO_COMPLETE / VIDEO_PLAY |
| 평균 시청 시간 | AVG(duration_sec)           |
| 학습 전환율   | QUIZ_START / VIDEO_PLAY     |
| 학습 마찰 점수 | PAUSE + SEEK×2 + ERROR×5    |

<center>
<img src="/assets/img/IA1.png" width="720" height=""/>
<p><b>[그림2]. Instructor Analytics Dashboard </b></p>
</center>

### 3.3. System Monitoring Dashboard

목적 : 서비스 안정성 및 성능 분석

서버 성능 평가에 사용되는 지표는 다음과 같습니다.

| 지표        | 설명                    |
| --------- | --------------------- |
| 전체 이벤트 수  | COUNT(*)              |
| 이벤트 타입 분포 | GROUP BY event_type   |
| 시간대별 트래픽  | 시간 기준 이벤트 수           |
| 에러율       | ERROR / 전체 이벤트        |
| 평균 응답 시간  | AVG(response_time_ms) |
| 에러 코드 분포  | GROUP BY error_code   |

<center>
<img src="/assets/img/Server1.png" width="720" height=""/>
<p><b>[그림3]. System Monitoring Dashboard </b></p>
</center>