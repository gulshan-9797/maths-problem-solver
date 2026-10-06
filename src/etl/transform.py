"""
PySpark Data Cleaning & Transformation Module
=============================================
Cleans raw mathematical problem records:
- Deduplication by problem_id
- Missing / Null value remediation
- Timestamp standardization
- Correctness flag normalization (1 = Correct, 0 = Incorrect)
- Text whitespace trimming & sanitization
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, trim, lower, when, to_timestamp, coalesce, lit, length
)


def remove_duplicates(df: DataFrame) -> DataFrame:
    """Removes duplicate records based on problem_id."""
    return df.dropDuplicates(["problem_id"])


def clean_missing_and_malformed(df: DataFrame) -> DataFrame:
    """
    Filters out records with empty or invalid problem texts and handles missing values.
    """
    return df \
        .withColumn("problem_text", trim(coalesce(col("problem_text"), lit("")))) \
        .withColumn("generated_solution", trim(coalesce(col("generated_solution"), lit("")))) \
        .withColumn("feedback", trim(coalesce(col("feedback"), lit("")))) \
        .withColumn("wrong_step", trim(coalesce(col("wrong_step"), lit("")))) \
        .filter(length(col("problem_text")) > 3)


def standardize_timestamps(df: DataFrame) -> DataFrame:
    """Standardizes timestamps into ISO TimestampType."""
    return df.withColumn(
        "timestamp",
        coalesce(
            to_timestamp(col("timestamp"), "yyyy-MM-dd HH:mm:ss"),
            to_timestamp(col("timestamp"), "yyyy-MM-dd'T'HH:mm:ss"),
            to_timestamp(col("timestamp"), "yyyy-MM-dd")
        )
    )


def normalize_correctness(df: DataFrame) -> DataFrame:
    """
    Normalizes varied raw correctness indicators into a unified integer flag:
    1 = Correct
    0 = Incorrect
    Filters out un-parsable corrupt values.
    """
    norm_col = lower(trim(coalesce(col("correctness"), lit(""))))
    
    return df.withColumn(
        "correctness_flag",
        when(norm_col.isin(["correct", "true", "yes", "1", "1.0"]), 1)
        .when(norm_col.isin(["incorrect", "false", "no", "0", "0.0"]), 0)
        .otherwise(-1)
    ).filter(col("correctness_flag") != -1)


def clean_raw_data(df: DataFrame) -> DataFrame:
    """
    Executes full data cleaning pipeline sequentially.
    """
    df_dedup = remove_duplicates(df)
    df_valid = clean_missing_and_malformed(df_dedup)
    df_time = standardize_timestamps(df_valid)
    df_clean = normalize_correctness(df_time)
    return df_clean
