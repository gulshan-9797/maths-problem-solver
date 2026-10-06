"""
Difficulty Analytics Module
===========================
Analyzes solver accuracy, error rate, and complexity across difficulty tiers:
Easy, Medium, Hard.
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, count, sum as spark_sum, avg, round as spark_round, when
)


def compute_difficulty_summary(df: DataFrame) -> DataFrame:
    """
    Computes performance aggregations per difficulty level.
    """
    difficulty_summary = df.groupBy("difficulty").agg(
        count("problem_id").alias("total_problems"),
        spark_sum("correctness_flag").alias("correct_count"),
        (count("problem_id") - spark_sum("correctness_flag")).alias("incorrect_count"),
        spark_round((spark_sum("correctness_flag") / count("problem_id")) * 100.0, 2).alias("accuracy_percentage"),
        spark_round(((count("problem_id") - spark_sum("correctness_flag")) / count("problem_id")) * 100.0, 2).alias("error_rate_percentage"),
        spark_round(avg("step_count"), 2).alias("avg_step_count"),
        spark_round(avg("complexity_score"), 2).alias("avg_complexity_score")
    )
    
    # Custom ordering: Easy -> Medium -> Hard
    diff_ordered = difficulty_summary.withColumn(
        "rank_order",
        when(col("difficulty") == "Easy", 1)
        .when(col("difficulty") == "Medium", 2)
        .when(col("difficulty") == "Hard", 3)
        .otherwise(4)
    ).orderBy("rank_order").drop("rank_order")
    
    return diff_ordered
