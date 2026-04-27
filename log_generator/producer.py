import json
import random
import time
import uuid
from datetime import datetime
from kafka import KafkaProducer


KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
TOPIC_NAME = "edtech-events"


USER_EVENTS = [
    "PAGE_VIEW",
    "LECTURE_ENTER",
    "VIDEO_PLAY",
    "VIDEO_PAUSE",
    "VIDEO_SEEK",
    "SUMMARY_VIEW",
    "QUIZ_START",
    "QUIZ_SUBMIT",
]

SYSTEM_EVENTS = [
    "ERROR_EVENT",
    "SLOW_RESPONSE",
]


PAGE_URLS = [
    "/",
    "/courses",
    "/courses/1",
    "/courses/2",
    "/lectures/1",
    "/lectures/2",
    "/lectures/1/summary",
    "/lectures/1/quiz",
]


ERROR_CODES = [
    "VIDEO_LOAD_FAIL",
    "QUIZ_GENERATION_FAIL",
    "AUTH_FAILED",
    "API_TIMEOUT",
    "DB_TIMEOUT",
]


def get_event_level(event_type: str) -> str:
    if event_type == "ERROR_EVENT":
        return "ERROR"
    if event_type == "SLOW_RESPONSE":
        return "WARNING"
    return "INFO"


def create_base_event(event_type: str) -> dict:
    now = datetime.utcnow().isoformat()

    return {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "event_level": get_event_level(event_type),
        "created_at": now,

        # 실제 서비스에서는 JWT/session에서 서버가 추론하는 값이지만
        # 현재는 프론트 대체용 generator이므로 시뮬레이션한다.
        "user_id": random.randint(1, 50),
        "session_id": f"session-{random.randint(1, 20)}",

        "course_id": random.randint(1, 5),
        "lecture_id": random.randint(1, 20),

        "page_url": random.choice(PAGE_URLS),
        "device": random.choice(["desktop", "mobile", "tablet"]),
        "browser": random.choice(["chrome", "edge", "safari"]),

        "duration_sec": None,
        "response_time_ms": random.randint(50, 400),
        "success": True,
        "error_code": None,
        "message": f"{event_type} occurred",

        "metadata": {},
    }


def generate_user_event() -> dict:
    event_type = random.choice(USER_EVENTS)
    event = create_base_event(event_type)

    if event_type in ["VIDEO_PLAY", "VIDEO_PAUSE", "VIDEO_SEEK"]:
        event["duration_sec"] = random.randint(5, 600)
        event["metadata"] = {
            "video_position_sec": random.randint(0, 1800),
            "video_duration_sec": 1800,
            "playback_speed": random.choice([1.0, 1.25, 1.5, 2.0]),
        }

    elif event_type in ["QUIZ_START", "QUIZ_SUBMIT"]:
        event["metadata"] = {
            "quiz_id": random.randint(1, 100),
            "question_count": random.randint(3, 10),
        }

        if event_type == "QUIZ_SUBMIT":
            event["metadata"]["score"] = random.randint(0, 100)

    elif event_type == "SUMMARY_VIEW":
        event["metadata"] = {
            "summary_type": random.choice(["basic", "chapter", "ai_generated"]),
        }

    return event


def generate_system_event() -> dict:
    event_type = random.choice(SYSTEM_EVENTS)
    event = create_base_event(event_type)

    event["success"] = False

    if event_type == "ERROR_EVENT":
        event["response_time_ms"] = random.randint(500, 3000)
        event["error_code"] = random.choice(ERROR_CODES)

    if event_type == "SLOW_RESPONSE":
        event["response_time_ms"] = random.randint(1000, 5000)

    event["metadata"] = {
        "server": random.choice(["api-1", "api-2"]),
        "retry_count": random.randint(0, 3),
    }

    return event


def generate_event() -> dict:
    # 실제 서비스에서는 사용자 행동 이벤트가 대부분이고,
    # 시스템 장애성 이벤트는 일부만 발생한다고 가정한다.
    if random.random() < 0.85:
        return generate_user_event()

    return generate_system_event()


def create_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        key_serializer=lambda key: key.encode("utf-8"),
        retries=5,
    )


def run():
    producer = create_producer()

    print("[log-generator] Kafka producer started")

    while True:
        event = generate_event()

        # 같은 유저 이벤트가 같은 파티션으로 갈 수 있도록 user_id를 key로 사용
        message_key = str(event["user_id"])

        producer.send(
            TOPIC_NAME,
            key=message_key,
            value=event,
        )

        producer.flush()

        print(
            f"[PUBLISHED] "
            f"type={event['event_type']} "
            f"level={event['event_level']} "
            f"user={event['user_id']} "
            f"lecture={event['lecture_id']}"
        )

        time.sleep(random.uniform(0.2, 1.0))


if __name__ == "__main__":
    run()