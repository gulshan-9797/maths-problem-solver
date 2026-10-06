"""
Topic Analytics Module
======================
Computes deep analytical metrics grouped by mathematical topic using PySpark:
- Volume & distribution
- Accuracy & error rates
- Step counts & complexity metrics
- Most prevalent failure steps
- Automated weakness identification ('needs_improvement')
"""

import os
from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, count, sum as spark_sum, avg, round as spark_round, when, lit
)

# Configurable thresholds
THRESHOLD_ACCURACY_MIN = float(os.getenv("THRESHOLD_ACCURACY_MIN", 0.70))
THRESHOLD_ERROR_RATE_MAX = float(os.getenv("THRESHOLD_ERROR_RATE_MAX", 0.30))
THRESHOLD_COMPLEXITY_MAX = float(os.getenv("THRESHOLD_COMPLEXITY_MAX", 70.0))


def compute_topic_summary(df: DataFrame) -> DataFrame:
    """
    Computes aggregated KPIs for each mathematical topic.
    """
    topic_summary = df.groupBy("topic").agg(
        count("problem_id").alias("total_problems"),
        spark_sum("correctness_flag").alias("correct_count"),
        (count("problem_id") - spark_sum("correctness_flag")).alias("incorrect_count"),
        spark_round((spark_sum("correctness_flag") / count("problem_id")) * 100.0, 2).alias("accuracy_percentage"),
        spark_round(((count("problem_id") - spark_sum("correctness_flag")) / count("problem_id")) * 100.0, 2).alias("error_rate_percentage"),
        spark_round(avg("step_count"), 2).alias("avg_step_count"),
        spark_round(avg("complexity_score"), 2).alias("avg_complexity_score")
    )
    
    # Apply configurable weakness identification logic
    topic_summary_flagged = topic_summary.withColumn(
        "needs_improvement",
        when(
            (col("accuracy_percentage") < (THRESHOLD_ACCURACY_MIN * 100.0)) |
            (col("error_rate_percentage") > (THRESHOLD_ERROR_RATE_MAX * 100.0)) |
            (col("avg_complexity_score") > THRESHOLD_COMPLEXITY_MAX),
            True
        ).otherwise(False)
    ).orderBy(col("accuracy_percentage").asc())
    
    return topic_summary_flagged


def compute_wrong_step_frequencies(df: DataFrame) -> DataFrame:
    """
    Calculates the distribution and ranking of reported incorrect steps across topics.
    """
    incorrect_df = df.filter((col("correctness_flag") == 0) & (col("wrong_step") != ""))
    
    total_incorrect = incorrect_df.count()
    if total_incorrect == 0:
        total_incorrect = 1
        
    step_freq = incorrect_df.groupBy("topic", "wrong_step").agg(
        count("problem_id").alias("frequency")
    ).withColumn(
        "percentage",
        spark_round((col("frequency") / lit(total_incorrect)) * 100.0, 2)
    ).orderBy(col("frequency").desc())
    
    return step_freq
