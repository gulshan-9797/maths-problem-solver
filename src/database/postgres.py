"""
Database Manager Module
=======================
Handles connection, table creation, view initialization, and data ingestion
for both PostgreSQL (primary storage for Grafana) and SQLite (automatic zero-config fallback).
"""

import os
import sqlite3
from typing import Optional, List, Dict, Any
import pandas as pd
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "math_solver_analytics")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "math_solver.db")


class DatabaseManager:
    """Manages database connectivity, migrations, and analytics ingestion."""

    def __init__(self, force_sqlite: bool = False):
        self.force_sqlite = force_sqlite
        self.engine_type = "sqlite" if force_sqlite else self._detect_backend()
        os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)

    def _detect_backend(self) -> str:
        """Tests PostgreSQL connectivity; falls back to SQLite if PostgreSQL is unavailable."""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                dbname=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                connect_timeout=2
            )
            conn.close()
            return "postgres"
        except Exception:
            return "sqlite"

    def get_connection(self):
        """Returns active DB connection object."""
        if self.engine_type == "postgres":
            import psycopg2
            return psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                dbname=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD
            )
        else:
            return sqlite3.connect(SQLITE_DB_PATH)

    def get_sqlalchemy_uri(self) -> str:
        """Returns SQLAlchemy connection string."""
        if self.engine_type == "postgres":
            return f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        else:
            return f"sqlite:///{SQLITE_DB_PATH}"

    def initialize_schema(self, schema_file: str = "sql/schema.sql", views_file: str = "sql/analytics_views.sql"):
        """Executes schema and analytical view scripts on the active database."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            if os.path.exists(schema_file):
                with open(schema_file, "r", encoding="utf-8") as f:
                    schema_sql = f.read()
                    if self.engine_type == "sqlite":
                        # Adapt postgres specifics for sqlite
                        schema_sql = schema_sql.replace("DOUBLE PRECISION", "REAL")
                        schema_sql = schema_sql.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
                        schema_sql = schema_sql.replace("CASCADE", "")
                        cursor.executescript(schema_sql)
                    else:
                        cursor.execute(schema_sql)
                conn.commit()

            if os.path.exists(views_file) and self.engine_type == "postgres":
                with open(views_file, "r", encoding="utf-8") as f:
                    views_sql = f.read()
                    cursor.execute(views_sql)
                conn.commit()
                
            print(f"[+] Database schema initialized successfully on engine: {self.engine_type.upper()}")
        except Exception as e:
            conn.rollback()
            print(f"[!] Error initializing database schema: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    def insert_feedback(self, record: Dict[str, Any]) -> bool:
        """Inserts a user feedback record into user_feedback_log table."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            query = """
            INSERT INTO user_feedback_log 
            (feedback_id, problem_id, problem_text, generated_solution, topic, difficulty, 
             step_count, complexity_score, user_correctness, wrong_step, feedback_text, is_processed_in_spark)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """ if self.engine_type == "sqlite" else """
            INSERT INTO user_feedback_log 
            (feedback_id, problem_id, problem_text, generated_solution, topic, difficulty, 
             step_count, complexity_score, user_correctness, wrong_step, feedback_text, is_processed_in_spark)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                record.get("feedback_id"),
                record.get("problem_id"),
                record.get("problem_text"),
                record.get("generated_solution"),
                record.get("topic"),
                record.get("difficulty"),
                record.get("step_count"),
                record.get("complexity_score"),
                record.get("user_correctness"),
                record.get("wrong_step"),
                record.get("feedback_text"),
                False
            ))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"[!] Error inserting feedback: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    def load_pandas_dataframe(self, df: pd.DataFrame, table_name: str, if_exists: str = "replace"):
        """Loads a pandas DataFrame into target database table."""
        from sqlalchemy import create_engine
        engine = create_engine(self.get_sqlalchemy_uri())
        df.to_sql(table_name, engine, if_exists=if_exists, index=False)
        print(f"[+] Loaded {len(df):,} records into database table '{table_name}' ({self.engine_type.upper()})")

    def query_df(self, query: str) -> pd.DataFrame:
        """Executes SQL query and returns results as a pandas DataFrame."""
        conn = self.get_connection()
        try:
            return pd.read_sql_query(query, conn)
        finally:
            conn.close()


# Default singleton instance
db_manager = DatabaseManager()
