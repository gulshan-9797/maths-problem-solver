"""
Performance Benchmark: PySpark vs Pandas
=========================================
Runs real, measured wall-clock execution benchmarks comparing Pandas vs PySpark
on the identical mathematical dataset for:
1. Data Ingestion & Schema Extraction
2. Cleaning & Correctness Normalization
3. Feature Engineering (Topic NLP, Step Parsing, Complexity 0-100)
4. Multi-Dimensional Aggregations & Grouping
"""

import os
import sys
import time

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
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

from src.etl.feature_engineering import (
    classify_topic_py,
    extract_step_count_py,
    calculate_complexity_score_py,
    derive_difficulty_level_py
)

load_dotenv()


def benchmark_pandas(file_path: str):
    """Executes full ETL workload using Pandas."""
    t0 = time.perf_counter()
    
    # 1. Ingestion
    df = pd.read_json(file_path)
    t_ingest = time.perf_counter() - t0
    
    # 2. Cleaning & Deduplication
    t1 = time.perf_counter()
    df = df.drop_duplicates(subset=["problem_id"])
    df = df[df["problem_text"].str.strip().str.len() > 3]
    
    valid_correct = {"correct", "true", "yes", "1", "1.0"}
    valid_incorrect = {"incorrect", "false", "no", "0", "0.0"}
    
    def norm_correctness(val):
        s = str(val).strip().lower()
        if s in valid_correct:
            return 1
        elif s in valid_incorrect:
            return 0
        return -1
        
    df["correctness_flag"] = df["correctness"].apply(norm_correctness)
    df = df[df["correctness_flag"] != -1]
    t_clean = time.perf_counter() - t1
    
    # 3. Feature Engineering
    t2 = time.perf_counter()
    df["topic"] = df.apply(lambda r: classify_topic_py(str(r["problem_text"]), str(r["generated_solution"])), axis=1)
    df["step_count"] = df["generated_solution"].apply(lambda s: extract_step_count_py(str(s)))
    df["complexity_score"] = df.apply(
        lambda r: calculate_complexity_score_py(str(r["problem_text"]), str(r["generated_solution"]), r["topic"], r["step_count"]),
        axis=1
    )
    df["difficulty"] = df.apply(lambda r: derive_difficulty_level_py(r["complexity_score"], r["step_count"]), axis=1)
    t_features = time.perf_counter() - t2
    
    # 4. Multi-level Aggregation
    t3 = time.perf_counter()
    topic_summary = df.groupby("topic").agg(
        total_problems=("problem_id", "count"),
        accuracy=("correctness_flag", "mean"),
        avg_complexity=("complexity_score", "mean"),
        avg_steps=("step_count", "mean")
    )
    t_agg = time.perf_counter() - t3
    
    total_time = time.perf_counter() - t0
    return {
        "engine": "Pandas (Single Core / In-Memory)",
        "record_count": len(df),
        "ingest_time_sec": round(t_ingest, 3),
        "clean_time_sec": round(t_clean, 3),
        "feature_time_sec": round(t_features, 3),
        "agg_time_sec": round(t_agg, 3),
        "total_time_sec": round(total_time, 3),
        "throughput_rec_per_sec": round(len(df) / max(0.001, total_time), 1)
    }


def benchmark_pyspark(file_path: str):
    """Executes full ETL workload using PySpark."""
    from pyspark.sql import SparkSession
    from src.etl.extract import extract_raw_data
    from src.etl.transform import clean_raw_data
    from src.etl.feature_engineering import engineer_features
    from src.analytics.topic_analysis import compute_topic_summary

    t0 = time.perf_counter()
    
    spark = SparkSession.builder \
        .appName("BenchmarkPySpark") \
        .master("local[*]") \
        .config("spark.driver.memory", "4g") \
        .config("spark.sql.shuffle.partitions", "8") \
        .config("spark.default.parallelism", "8") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")

    # 1. Ingestion
    raw_df = extract_raw_data(spark, file_path, "json")
    count_raw = raw_df.count()
    t_ingest = time.perf_counter() - t0

    # 2. Cleaning
    t1 = time.perf_counter()
    clean_df = clean_raw_data(raw_df)
    clean_count = clean_df.count()
    t_clean = time.perf_counter() - t1

    # 3. Feature Engineering
    t2 = time.perf_counter()
    feat_df = engineer_features(clean_df).cache()
    feat_count = feat_df.count()
    t_features = time.perf_counter() - t2

    # 4. Aggregations
    t3 = time.perf_counter()
    topic_summary = compute_topic_summary(feat_df)
    topic_rows = topic_summary.collect()
    t_agg = time.perf_counter() - t3

    total_time = time.perf_counter() - t0
    return {
        "engine": "PySpark (Distributed / Multi-Core Parallelized)",
        "record_count": feat_count,
        "ingest_time_sec": round(t_ingest, 3),
        "clean_time_sec": round(t_clean, 3),
        "feature_time_sec": round(t_features, 3),
        "agg_time_sec": round(t_agg, 3),
        "total_time_sec": round(total_time, 3),
        "throughput_rec_per_sec": round(feat_count / max(0.001, total_time), 1)
    }


def run_benchmark():
    file_path = "data/raw/raw_problems.json"
    if not os.path.exists(file_path):
        from scripts.generate_data import generate_dataset
        generate_dataset(12000)

    print("\n" + "=" * 80)
    print("      MEASURED PERFORMANCE BENCHMARK: PANDAS vs PYSPARK")
    print("=" * 80)

    print("\n[1/2] Running benchmark on Pandas...")
    pandas_res = benchmark_pandas(file_path)
    print(f"  -> Pandas Total Execution Time: {pandas_res['total_time_sec']}s ({pandas_res['throughput_rec_per_sec']} rec/s)")

    print("\n[2/2] Running benchmark on PySpark...")
    spark_res = benchmark_pyspark(file_path)
    print(f"  -> PySpark Total Execution Time: {spark_res['total_time_sec']}s ({spark_res['throughput_rec_per_sec']} rec/s)")

    print("\n" + "=" * 80)
    print("                    ACTUAL MEASURED BENCHMARK RESULTS")
    print("=" * 80)
    
    results = [pandas_res, spark_res]
    res_df = pd.DataFrame(results)
    print(res_df.to_string(index=False))

    print("\n--- Big Data Architectural Takeaways ---")
    print("1. Small Data (< 100K): Pandas runs within a single memory space without JVM/serialization overhead.")
    print("2. Big Data Scale (> 1M - 1B+ records): Pandas fails due to OOM (Out-Of-Memory) limits on a single node.")
    print("3. PySpark Scales Linearly: Sharding partitions across worker nodes and executing lazy transformations with Catalyst Optimizer.")


if __name__ == "__main__":
    run_benchmark()
