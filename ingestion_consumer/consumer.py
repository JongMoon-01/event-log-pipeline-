import json
import time
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from db import insert_event


KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
TOPIC_NAME = "edtech-events"
GROUP_ID = "edtech-event-consumer-group"


REQUIRED_FIELDS = [
    "event_id",
    "event_type",
    "event_level",
    "created_at",
    "success",
]


def validate_event(event: dict) -> bool:
    for field in REQUIRED_FIELDS:
        if field not in event:
            print(f"[INVALID] missing field: {field}")
            return False

    return True


def create_consumer():
    for attempt in range(20):
        try:
            print(f"[Kafka Consumer] connecting... attempt={attempt + 1}")

            consumer = KafkaConsumer(
                TOPIC_NAME,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=GROUP_ID,
                auto_offset_reset="earliest",
                enable_auto_commit=False,
                value_deserializer=lambda value: json.loads(value.decode("utf-8")),
                key_deserializer=lambda key: key.decode("utf-8") if key else None,
            )

            print("[Kafka Consumer] connected")
            return consumer

        except NoBrokersAvailable:
            print("[Kafka Consumer] Kafka not ready. retrying...")
            time.sleep(3)

    raise RuntimeError("Kafka connection failed")


def run():
    consumer = create_consumer()

    print("[ingestion-consumer] started")

    for message in consumer:
        event = message.value

        try:
            if not validate_event(event):
                consumer.commit()
                continue

            insert_event(event)

            consumer.commit()

            print(
                f"[SAVED] "
                f"type={event['event_type']} "
                f"level={event['event_level']} "
                f"user={event.get('user_id')} "
                f"lecture={event.get('lecture_id')}"
            )

        except Exception as e:
            print(f"[ERROR] failed to process message: {e}")
            time.sleep(1)


if __name__ == "__main__":
    run()