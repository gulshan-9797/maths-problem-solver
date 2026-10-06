-- ==============================================================================
-- Mathematical Problem Solver: Grafana Analytics SQL Views
-- Powers the 10 Dashboard Panels and System Bottleneck Visualizations
-- ==============================================================================

-- Panel 1 & 2: Overview KPI Metrics
CREATE OR REPLACE VIEW view_overall_kpis AS
SELECT 
    COUNT(*) AS total_problems,
    SUM(correctness_flag) AS total_correct,
    COUNT(*) - SUM(correctness_flag) AS total_incorrect,
    ROUND((SUM(correctness_flag)::NUMERIC / NULLIF(COUNT(*), 0) * 100.0), 2) AS overall_accuracy_pct,
    ROUND(((COUNT(*) - SUM(correctness_flag))::NUMERIC / NULLIF(COUNT(*), 0) * 100.0), 2) AS overall_error_rate_pct,
    ROUND(AVG(step_count)::NUMERIC, 2) AS avg_steps,
    ROUND(AVG(complexity_score)::NUMERIC, 2) AS avg_complexity
FROM processed_problem_analytics;

-- Panel 3: Problems Solved Per Day (Time Series)
CREATE OR REPLACE VIEW view_daily_volume AS
SELECT 
    DATE_TRUNC('day', timestamp) AS time,
    COUNT(*) AS problems_solved,
    SUM(correctness_flag) AS correct_solutions,
    COUNT(*) - SUM(correctness_flag) AS incorrect_solutions
FROM processed_problem_analytics
GROUP BY DATE_TRUNC('day', timestamp)
ORDER BY time ASC;

-- Panel 4: Accuracy Over Last 30 Days (Time Series)
CREATE OR REPLACE VIEW view_accuracy_trend_30d AS
SELECT 
    DATE_TRUNC('day', timestamp) AS time,
    ROUND((SUM(correctness_flag)::NUMERIC / NULLIF(COUNT(*), 0) * 100.0), 2) AS daily_accuracy_pct,
    ROUND(AVG(SUM(correctness_flag)::NUMERIC / NULLIF(COUNT(*), 0) * 100.0) 
          OVER (ORDER BY DATE_TRUNC('day', timestamp) ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2) AS rolling_7d_accuracy,
    ROUND(AVG(complexity_score)::NUMERIC, 2) AS avg_complexity
FROM processed_problem_analytics
WHERE timestamp >= (SELECT MAX(timestamp) - INTERVAL '30 days' FROM processed_problem_analytics)
GROUP BY DATE_TRUNC('day', timestamp)
ORDER BY time ASC;

-- Panel 5: Problem Distribution by Topic (Bar / Pie)
CREATE OR REPLACE VIEW view_topic_distribution AS
SELECT 
    topic,
    COUNT(*) AS problem_count,
    ROUND((COUNT(*)::NUMERIC / (SELECT COUNT(*) FROM processed_problem_analytics) * 100.0), 2) AS percentage_share
FROM processed_problem_analytics
GROUP BY topic
ORDER BY problem_count DESC;

-- Panel 6: Most Difficult Topics (Ranked by Complexity)
CREATE OR REPLACE VIEW view_most_difficult_topics AS
SELECT 
    topic,
    ROUND(AVG(complexity_score)::NUMERIC, 2) AS avg_complexity_score,
    ROUND(AVG(step_count)::NUMERIC, 2) AS avg_step_count,
    ROUND(((COUNT(*) - SUM(correctness_flag))::NUMERIC / NULLIF(COUNT(*), 0) * 100.0), 2) AS error_rate_pct
FROM processed_problem_analytics
GROUP BY topic
ORDER BY avg_complexity_score DESC;

-- Panel 7: Average Step Count by Topic
CREATE OR REPLACE VIEW view_step_count_by_topic AS
SELECT 
    topic,
    ROUND(AVG(step_count)::NUMERIC, 2) AS avg_step_count,
    MAX(step_count) AS max_step_count,
    MIN(step_count) AS min_step_count
FROM processed_problem_analytics
GROUP BY topic
ORDER BY avg_step_count DESC;

-- Panel 8: Accuracy by Topic (Identifies Lowest Performing Topics)
CREATE OR REPLACE VIEW view_accuracy_by_topic AS
SELECT 
    topic,
    COUNT(*) AS total_problems,
    ROUND((SUM(correctness_flag)::NUMERIC / NULLIF(COUNT(*), 0) * 100.0), 2) AS accuracy_pct,
    ROUND(((COUNT(*) - SUM(correctness_flag))::NUMERIC / NULLIF(COUNT(*), 0) * 100.0), 2) AS error_rate_pct,
    CASE 
        WHEN (SUM(correctness_flag)::NUMERIC / NULLIF(COUNT(*), 0) * 100.0) < 70.0 THEN 'CRITICAL: Needs Improvement'
        WHEN (SUM(correctness_flag)::NUMERIC / NULLIF(COUNT(*), 0) * 100.0) < 80.0 THEN 'WARNING: Moderate Accuracy'
        ELSE 'HEALTHY: High Accuracy'
    END AS status_badge
FROM processed_problem_analytics
GROUP BY topic
ORDER BY accuracy_pct ASC;

-- Panel 9: Error Rate by Difficulty Level
CREATE OR REPLACE VIEW view_error_by_difficulty AS
SELECT 
    difficulty,
    COUNT(*) AS total_problems,
    SUM(correctness_flag) AS correct_problems,
    COUNT(*) - SUM(correctness_flag) AS incorrect_problems,
    ROUND((SUM(correctness_flag)::NUMERIC / NULLIF(COUNT(*), 0) * 100.0), 2) AS accuracy_pct,
    ROUND(((COUNT(*) - SUM(correctness_flag))::NUMERIC / NULLIF(COUNT(*), 0) * 100.0), 2) AS error_rate_pct,
    ROUND(AVG(complexity_score)::NUMERIC, 2) AS avg_complexity
FROM processed_problem_analytics
GROUP BY difficulty
ORDER BY 
    CASE difficulty
        WHEN 'Easy' THEN 1
        WHEN 'Medium' THEN 2
        WHEN 'Hard' THEN 3
        ELSE 4
    END;

-- Panel 10: Feedback / Wrong Step Analysis
CREATE OR REPLACE VIEW view_wrong_step_analysis AS
SELECT 
    COALESCE(wrong_step, 'Unspecified') AS wrong_step,
    COUNT(*) AS failure_count,
    ROUND((COUNT(*)::NUMERIC / (SELECT COUNT(*) FROM processed_problem_analytics WHERE correctness_flag = 0) * 100.0), 2) AS percentage_of_all_errors
FROM processed_problem_analytics
WHERE correctness_flag = 0 AND wrong_step IS NOT NULL AND wrong_step != ''
GROUP BY wrong_step
ORDER BY failure_count DESC;

-- Panel 11: Actionable System Weaknesses & Alerts View
CREATE OR REPLACE VIEW view_system_alerts AS
SELECT 
    topic,
    ROUND((SUM(correctness_flag)::NUMERIC / NULLIF(COUNT(*), 0) * 100.0), 2) AS accuracy_pct,
    ROUND(((COUNT(*) - SUM(correctness_flag))::NUMERIC / NULLIF(COUNT(*), 0) * 100.0), 2) AS error_rate_pct,
    ROUND(AVG(complexity_score)::NUMERIC, 2) AS avg_complexity,
    ROUND(AVG(step_count)::NUMERIC, 2) AS avg_steps,
    CASE 
        WHEN (SUM(correctness_flag)::NUMERIC / NULLIF(COUNT(*), 0) * 100.0) < 70.0 
             OR ((COUNT(*) - SUM(correctness_flag))::NUMERIC / NULLIF(COUNT(*), 0) * 100.0) > 30.0 
             OR AVG(complexity_score) > 70.0
        THEN TRUE
        ELSE FALSE
    END AS needs_improvement,
    'Enhance pedagogical step verification and intermediate breakdown' AS recommended_action
FROM processed_problem_analytics
GROUP BY topic
HAVING (SUM(correctness_flag)::NUMERIC / NULLIF(COUNT(*), 0) * 100.0) < 70.0 
    OR ((COUNT(*) - SUM(correctness_flag))::NUMERIC / NULLIF(COUNT(*), 0) * 100.0) > 30.0
    OR AVG(complexity_score) > 70.0
ORDER BY accuracy_pct ASC;
