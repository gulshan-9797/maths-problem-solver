"""
PySpark Load Module
===================
Persists processed mathematical analytics DataFrame into:
1. Columnar Apache Parquet storage for high-performance Big Data analytics
2. Relational Database (PostgreSQL / SQLite) for Grafana dashboards & application queries
"""

import os
from pyspark.sql import DataFrame
from src.database.postgres import db_manager


def save_as_parquet(df: DataFrame, output_path: str = "data/processed/problem_analytics.parquet"):
    """
    Saves the cleaned and enriched PySpark DataFrame into Apache Parquet format.
    Uses Snappy compression for balanced disk size and read speed.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"[*] Writing PySpark DataFrame to Parquet: {output_path}...")
    
    try:
        df.write \
            .mode("overwrite") \
            .option("compression", "snappy") \
            .parquet(output_path)
    except Exception as e:
        import shutil
        print(f"[*] Spark Native Hadoop committer encountered Windows file permission notice: {e}")
        print("[*] Persisting Parquet with Snappy compression via PyArrow columnar engine...")
        if os.path.exists(output_path) and os.path.isdir(output_path):
            try:
                shutil.rmtree(output_path)
            except Exception:
                pass
        pdf = df.toPandas()
        pdf.to_parquet(output_path, engine="pyarrow", compression="snappy", index=False)
        
    print(f"[+] Successfully persisted Parquet dataset to: {output_path}")


def load_analytics_to_db(df: DataFrame, table_name: str = "processed_problem_analytics"):
    """
    Loads PySpark DataFrame into the relational database table for Grafana visualization.
    """
    print(f"[*] Loading processed analytics into relational database ({db_manager.engine_type.upper()})...")
    
    # Convert Spark DataFrame sample / batch to pandas for DB loading
    # In large distributed clusters, spark.read.format("jdbc") is used.
    # Here we convert via PyArrow for fast and universal database ingestion across environments.
    pdf = df.toPandas()
    db_manager.load_pandas_dataframe(pdf, table_name=table_name, if_exists="replace")
    print(f"[+] Loaded {len(pdf):,} records to database table '{table_name}'")
