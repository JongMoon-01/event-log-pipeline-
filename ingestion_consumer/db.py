import json
import os
import pymysql


def get_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "mariadb"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "edtech"),
        password=os.getenv("DB_PASSWORD", "edtech1234"),
        database=os.getenv("DB_NAME", "edtech_event_db"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def insert_event(event: dict):
    sql = """
    INSERT INTO event_logs (
        event_id,
        event_type,
        event_level,
        user_id,
        session_id,
        course_id,
        lecture_id,
        page_url,
        device,
        browser,
        duration_sec,
        response_time_ms,
        success,
        error_code,
        message,
        metadata,
        created_at
    )
    VALUES (
        %(event_id)s,
        %(event_type)s,
        %(event_level)s,
        %(user_id)s,
        %(session_id)s,
        %(course_id)s,
        %(lecture_id)s,
        %(page_url)s,
        %(device)s,
        %(browser)s,
        %(duration_sec)s,
        %(response_time_ms)s,
        %(success)s,
        %(error_code)s,
        %(message)s,
        %(metadata)s,
        %(created_at)s
    )
    """

    data = event.copy()
    data["metadata"] = json.dumps(data.get("metadata", {}), ensure_ascii=False)

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, data)