"""
PySpark Extraction Module
=========================
Reads raw mathematical problem datasets from CSV or JSON sources with schema enforcement.
"""

import os
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import (
    StructType, StructField, StringType, TimestampType
)


def get_raw_schema() -> StructType:
    """Returns the explicit PySpark schema for raw problem extraction."""
    return StructType([
        StructField("problem_id", StringType(), False),
        StructField("user_id", StringType(), True),
        StructField("timestamp", StringType(), True),
        StructField("problem_text", StringType(), True),
        StructField("generated_solution", StringType(), True),
        StructField("correctness", StringType(), True),
        StructField("feedback", StringType(), True),
        StructField("wrong_step", StringType(), True),
    ])


def extract_raw_data(
    spark: SparkSession,
    file_path: str,
    file_format: str = "json"
) -> DataFrame:
    """
    Extracts raw mathematical problems data into a Spark DataFrame.

    Parameters:
        spark (SparkSession): Active SparkSession instance
        file_path (str): Path to raw data file (CSV or JSON)
        file_format (str): 'json' or 'csv'

    Returns:
        DataFrame: PySpark DataFrame containing raw records
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Raw data file not found at: {file_path}")

    schema = get_raw_schema()

    if file_format.lower() == "json":
        df = spark.read \
            .schema(schema) \
            .option("multiline", "true") \
            .json(file_path)
    elif file_format.lower() == "csv":
        df = spark.read \
            .schema(schema) \
            .option("header", "true") \
            .option("quote", "\"") \
            .option("escape", "\"") \
            .csv(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_format}. Use 'json' or 'csv'.")

    return df
