CREATE TABLE IF NOT EXISTS event_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    event_id VARCHAR(100) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_level VARCHAR(20) NOT NULL,

    user_id BIGINT NULL,
    session_id VARCHAR(100) NULL,
    course_id BIGINT NULL,
    lecture_id BIGINT NULL,

    page_url VARCHAR(255) NULL,
    device VARCHAR(50) NULL,
    browser VARCHAR(50) NULL,

    duration_sec INT NULL,
    response_time_ms INT NULL,
    success BOOLEAN NOT NULL,
    error_code VARCHAR(100) NULL,
    message VARCHAR(500) NULL,

    metadata JSON NULL,
    created_at DATETIME NOT NULL,

    inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_event_type ON event_logs(event_type);
CREATE INDEX idx_event_level ON event_logs(event_level);
CREATE INDEX idx_user_id ON event_logs(user_id);
CREATE INDEX idx_lecture_id ON event_logs(lecture_id);
CREATE INDEX idx_created_at ON event_logs(created_at);