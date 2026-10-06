-- ==============================================================================
-- Mathematical Problem Solver: Relational Storage Schema
-- Used by PostgreSQL and mirrored in SQLite fallback
-- ==============================================================================

-- Drop tables if recreating
DROP TABLE IF EXISTS user_feedback_log CASCADE;
DROP TABLE IF EXISTS wrong_step_frequency CASCADE;
DROP TABLE IF EXISTS daily_performance_metrics CASCADE;
DROP TABLE IF EXISTS difficulty_analytics_summary CASCADE;
DROP TABLE IF EXISTS topic_analytics_summary CASCADE;
DROP TABLE IF EXISTS processed_problem_analytics CASCADE;
DROP TABLE IF EXISTS raw_problems CASCADE;

-- 1. Raw Problems (Raw extraction table)
CREATE TABLE IF NOT EXISTS raw_problems (
    problem_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64),
    timestamp TIMESTAMP,
    problem_text TEXT NOT NULL,
    generated_solution TEXT,
    correctness VARCHAR(32),
    feedback TEXT,
    wrong_step VARCHAR(32),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Processed Problem Analytics (PySpark Processed & Cleaned Data)
CREATE TABLE IF NOT EXISTS processed_problem_analytics (
    problem_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64),
    timestamp TIMESTAMP,
    problem_text TEXT NOT NULL,
    generated_solution TEXT,
    topic VARCHAR(64) NOT NULL,
    difficulty VARCHAR(32) NOT NULL,
    step_count INT NOT NULL,
    complexity_score DOUBLE PRECISION NOT NULL,
    correctness_flag INT NOT NULL,  -- 1 = Correct, 0 = Incorrect
    wrong_step VARCHAR(32),
    feedback_text TEXT,
    needs_improvement BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices for rapid Grafana aggregations
CREATE INDEX IF NOT EXISTS idx_processed_topic ON processed_problem_analytics(topic);
CREATE INDEX IF NOT EXISTS idx_processed_difficulty ON processed_problem_analytics(difficulty);
CREATE INDEX IF NOT EXISTS idx_processed_timestamp ON processed_problem_analytics(timestamp);
CREATE INDEX IF NOT EXISTS idx_processed_correctness ON processed_problem_analytics(correctness_flag);

-- 3. Topic Analytics Summary (Aggregated by PySpark ETL)
CREATE TABLE IF NOT EXISTS topic_analytics_summary (
    topic VARCHAR(64) PRIMARY KEY,
    total_problems INT NOT NULL,
    correct_count INT NOT NULL,
    incorrect_count INT NOT NULL,
    accuracy_percentage DOUBLE PRECISION NOT NULL,
    error_rate_percentage DOUBLE PRECISION NOT NULL,
    avg_step_count DOUBLE PRECISION NOT NULL,
    avg_complexity_score DOUBLE PRECISION NOT NULL,
    most_frequent_wrong_step VARCHAR(32),
    needs_improvement BOOLEAN NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Difficulty Analytics Summary
CREATE TABLE IF NOT EXISTS difficulty_analytics_summary (
    difficulty VARCHAR(32) PRIMARY KEY,
    total_problems INT NOT NULL,
    correct_count INT NOT NULL,
    incorrect_count INT NOT NULL,
    accuracy_percentage DOUBLE PRECISION NOT NULL,
    error_rate_percentage DOUBLE PRECISION NOT NULL,
    avg_step_count DOUBLE PRECISION NOT NULL,
    avg_complexity_score DOUBLE PRECISION NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Daily Performance Metrics (Time-series)
CREATE TABLE IF NOT EXISTS daily_performance_metrics (
    metric_date DATE PRIMARY KEY,
    total_problems INT NOT NULL,
    correct_count INT NOT NULL,
    incorrect_count INT NOT NULL,
    accuracy_percentage DOUBLE PRECISION NOT NULL,
    error_rate_percentage DOUBLE PRECISION NOT NULL,
    avg_complexity_score DOUBLE PRECISION NOT NULL,
    rolling_7d_accuracy DOUBLE PRECISION,
    rolling_30d_accuracy DOUBLE PRECISION,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Wrong Step Frequency Analysis
CREATE TABLE IF NOT EXISTS wrong_step_frequency (
    id SERIAL PRIMARY KEY,
    topic VARCHAR(64) NOT NULL,
    wrong_step VARCHAR(32) NOT NULL,
    frequency INT NOT NULL,
    percentage DOUBLE PRECISION NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Live User Feedback Log (Directly inserted from Gradio interface)
CREATE TABLE IF NOT EXISTS user_feedback_log (
    feedback_id VARCHAR(64) PRIMARY KEY,
    problem_id VARCHAR(64),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    problem_text TEXT NOT NULL,
    generated_solution TEXT,
    topic VARCHAR(64),
    difficulty VARCHAR(32),
    step_count INT,
    complexity_score DOUBLE PRECISION,
    user_correctness VARCHAR(16) NOT NULL, -- "Correct" or "Incorrect"
    wrong_step VARCHAR(32),
    feedback_text TEXT,
    is_processed_in_spark BOOLEAN DEFAULT FALSE
);
