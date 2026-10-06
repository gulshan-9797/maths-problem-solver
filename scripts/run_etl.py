"""
PySpark ETL Pipeline Orchestrator
=================================
Executes the full end-to-end Big Data ETL processing:
1. Initialize SparkSession
2. Extract raw dataset (CSV / JSON)
3. Clean, deduplicate, normalize correctness and timestamps
4. Feature engineering: Topic classification, step counting, difficulty derivation, complexity scoring
5. Persist processed dataset into Apache Parquet columnar storage
6. Compute topic, difficulty, and daily time-series analytical aggregations
7. Load processed analytics and aggregations into PostgreSQL / SQLite database
"""

import os
import sys
import time

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession
from dotenv import load_dotenv

# Ensure PySpark workers use the exact active Python interpreter
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

# Ensure JAVA_HOME is configured if on Windows
if "JAVA_HOME" not in os.environ:
    candidate_paths = [
        r"C:\Program Files\Microsoft\jdk-17.0.20.101-hotspot",
        r"C:\Program Files\Java\jdk-17",
        r"C:\Program Files\Eclipse Adoptium\jdk-17"
    ]
    for p in candidate_paths:
        if os.path.exists(p):
            os.environ["JAVA_HOME"] = p
            os.environ["PATH"] = os.path.join(p, "bin") + os.pathsep + os.environ.get("PATH", "")
            break

from src.etl.extract import extract_raw_data
from src.etl.transform import clean_raw_data
from src.etl.feature_engineering import engineer_features
from src.etl.load import save_as_parquet, load_analytics_to_db
from src.analytics.topic_analysis import compute_topic_summary, compute_wrong_step_frequencies
from src.analytics.difficulty_analysis import compute_difficulty_summary
from src.analytics.performance_analysis import compute_overall_kpis, compute_daily_performance
from src.database.postgres import db_manager

load_dotenv()


def get_spark_session() -> SparkSession:
    """Creates an optimized local SparkSession."""
    spark = SparkSession.builder \
        .appName("MathProblemSolverETL") \
        .master(os.getenv("SPARK_MASTER", "local[*]")) \
        .config("spark.driver.memory", "4g") \
        .config("spark.sql.shuffle.partitions", "8") \
        .config("spark.default.parallelism", "8") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    return spark


def run_pipeline(
    raw_file_path: str = "data/raw/raw_problems.json",
    file_format: str = "json",
    parquet_path: str = "data/processed/problem_analytics.parquet"
):
    start_time = time.time()
    print("=" * 80)
    print("       MATHEMATICAL PROBLEM SOLVER - PYSPARK BIG DATA ETL PIPELINE")
    print("=" * 80)

    # 0. Initialize Database Schema
    print("\n[Stage 0] Initializing Relational Storage...")
    db_manager.initialize_schema()

    # 1. Spark Session
    print("\n[Stage 1] Initializing PySpark Session...")
    spark = get_spark_session()
    print(f"[+] Active Spark Version: {spark.version}")

    # 2. Extract
    print(f"\n[Stage 2] EXTRACT: Reading raw data from '{raw_file_path}' ({file_format.upper()})...")
    raw_df = extract_raw_data(spark, raw_file_path, file_format)
    raw_count = raw_df.count()
    print(f"[+] Extracted {raw_count:,} raw records.")

    # 3. Clean & Transform
    print("\n[Stage 3] TRANSFORM (Cleaning & Normalization)...")
    clean_df = clean_raw_data(raw_df)
    clean_count = clean_df.count()
    print(f"[+] Cleaned Dataset: {clean_count:,} valid records ({raw_count - clean_count:,} duplicates/malformed dropped).")

    # 4. Feature Engineering
    print("\n[Stage 4] FEATURE ENGINEERING (Topic NLP, Difficulty, Steps, Complexity 0-100)...")
    feature_df = engineer_features(clean_df).cache()
    print(f"[+] Feature engineering completed on {feature_df.count():,} records.")

    # 5. Parquet Columnar Load
    print("\n[Stage 5] LOAD (Apache Parquet Columnar Storage)...")
    save_as_parquet(feature_df, parquet_path)

    # 6. Analytics & Summaries
    print("\n[Stage 6] ANALYTICS (Aggregations & Weakness Bottleneck Detection)...")
    
    # Topic Summary
    topic_summary_df = compute_topic_summary(feature_df)
    print("\n--- Topic Performance Summary ---")
    topic_summary_df.show(truncate=False)

    # Difficulty Summary
    diff_summary_df = compute_difficulty_summary(feature_df)
    print("\n--- Difficulty Tier Breakdown ---")
    diff_summary_df.show(truncate=False)

    # Wrong Step Frequencies
    step_freq_df = compute_wrong_step_frequencies(feature_df)
    print("\n--- Most Frequent Failure Steps (Top 5) ---")
    step_freq_df.show(5, truncate=False)

    # Daily Performance
    daily_df = compute_daily_performance(feature_df)

    # High-level KPIs
    overall_kpis = compute_overall_kpis(feature_df)
    print("\n--- High-Level System KPIs ---")
    for k, v in overall_kpis.items():
        print(f"  {k:25s}: {v}")

    # 7. Database Loading for Grafana & UI
    print("\n[Stage 7] LOAD (Persisting Analytics to PostgreSQL / SQLite Database)...")
    load_analytics_to_db(feature_df, "processed_problem_analytics")
    
    # Persist summary tables
    db_manager.load_pandas_dataframe(topic_summary_df.toPandas(), "topic_analytics_summary")
    db_manager.load_pandas_dataframe(diff_summary_df.toPandas(), "difficulty_analytics_summary")
    db_manager.load_pandas_dataframe(step_freq_df.toPandas(), "wrong_step_frequency")
    db_manager.load_pandas_dataframe(daily_df.toPandas(), "daily_performance_metrics")

    elapsed = time.time() - start_time
    print("\n" + "=" * 80)
    print(f"[+] PySpark ETL Pipeline Completed Successfully in {elapsed:.2f} seconds!")
    print("=" * 80)

    return feature_df


if __name__ == "__main__":
    raw_path = "data/raw/raw_problems.json"
    if not os.path.exists(raw_path):
        from scripts.generate_data import generate_dataset
        generate_dataset(12000)
        
    run_pipeline(raw_file_path=raw_path, file_format="json")
