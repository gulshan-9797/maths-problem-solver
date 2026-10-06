"""
Performance & Time-Series Analytics Module
==========================================
Computes overall system KPIs, daily volume & accuracy trends, rolling performance,
and dynamic learning contexts for Cohere prompt optimization.
"""

from typing import Dict, Any
from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, count, sum as spark_sum, avg, round as spark_round, to_date
)
from pyspark.sql.window import Window


def compute_overall_kpis(df: DataFrame) -> Dict[str, Any]:
    """Computes high-level scalar KPIs across the entire dataset."""
    total_count = df.count()
    if total_count == 0:
        return {
            "total_problems": 0,
            "total_correct": 0,
            "total_incorrect": 0,
            "overall_accuracy": 0.0,
            "overall_error_rate": 0.0,
            "avg_step_count": 0.0,
            "avg_complexity_score": 0.0
        }
        
    agg_row = df.agg(
        spark_sum("correctness_flag").alias("total_correct"),
        spark_round(avg("step_count"), 2).alias("avg_steps"),
        spark_round(avg("complexity_score"), 2).alias("avg_complexity")
    ).collect()[0]
    
    total_correct = agg_row["total_correct"] or 0
    total_incorrect = total_count - total_correct
    accuracy = round((total_correct / total_count) * 100.0, 2)
    error_rate = round((total_incorrect / total_count) * 100.0, 2)
    
    return {
        "total_problems": total_count,
        "total_correct": total_correct,
        "total_incorrect": total_incorrect,
        "overall_accuracy": accuracy,
        "overall_error_rate": error_rate,
        "avg_step_count": float(agg_row["avg_steps"] or 0.0),
        "avg_complexity_score": float(agg_row["avg_complexity"] or 0.0)
    }


def compute_daily_performance(df: DataFrame) -> DataFrame:
    """Computes daily volume, daily accuracy, and rolling 7-day/30-day accuracy."""
    daily = df.withColumn("metric_date", to_date("timestamp")) \
        .groupBy("metric_date") \
        .agg(
            count("problem_id").alias("total_problems"),
            spark_sum("correctness_flag").alias("correct_count"),
            (count("problem_id") - spark_sum("correctness_flag")).alias("incorrect_count"),
            spark_round((spark_sum("correctness_flag") / count("problem_id")) * 100.0, 2).alias("accuracy_percentage"),
            spark_round(((count("problem_id") - spark_sum("correctness_flag")) / count("problem_id")) * 100.0, 2).alias("error_rate_percentage"),
            spark_round(avg("complexity_score"), 2).alias("avg_complexity_score")
        )
        
    window_7d = Window.orderBy("metric_date").rowsBetween(-6, 0)
    window_30d = Window.orderBy("metric_date").rowsBetween(-29, 0)
    
    daily_rolling = daily \
        .withColumn("rolling_7d_accuracy", spark_round(avg("accuracy_percentage").over(window_7d), 2)) \
        .withColumn("rolling_30d_accuracy", spark_round(avg("accuracy_percentage").over(window_30d), 2)) \
        .orderBy("metric_date")
        
    return daily_rolling


def extract_topic_learning_context(df: DataFrame, target_topic: str) -> Dict[str, Any]:
    """
    Extracts data-driven pedagogical context for a specific topic to enhance Cohere prompts.
    """
    topic_df = df.filter(col("topic") == target_topic)
    total = topic_df.count()
    if total == 0:
        return {
            "topic": target_topic,
            "accuracy": 75.0,
            "avg_steps": 5.0,
            "avg_complexity": 50.0,
            "common_wrong_steps": ["Step 3"],
            "common_feedback": ["Verify intermediate steps"]
        }
        
    agg = topic_df.agg(
        spark_sum("correctness_flag").alias("correct"),
        avg("step_count").alias("avg_steps"),
        avg("complexity_score").alias("avg_complexity")
    ).collect()[0]
    
    correct = agg["correct"] or 0
    accuracy = round((correct / total) * 100.0, 1)
    avg_steps = round(float(agg["avg_steps"] or 5.0), 1)
    avg_complexity = round(float(agg["avg_complexity"] or 50.0), 1)
    
    # Top wrong steps for this topic
    wrong_steps = topic_df.filter((col("correctness_flag") == 0) & (col("wrong_step") != "")) \
        .groupBy("wrong_step").count().orderBy(col("count").desc()).limit(2).collect()
    common_wrong = [row["wrong_step"] for row in wrong_steps] or ["Intermediate step"]
    
    # Top negative feedback themes
    feedbacks = topic_df.filter((col("correctness_flag") == 0) & (col("feedback") != "")) \
        .select("feedback").limit(3).collect()
    sample_feedbacks = [row["feedback"] for row in feedbacks] or ["Check algebraic manipulations"]
    
    return {
        "topic": target_topic,
        "accuracy": accuracy,
        "avg_steps": avg_steps,
        "avg_complexity": avg_complexity,
        "common_wrong_steps": common_wrong,
        "common_feedback": sample_feedbacks
    }
