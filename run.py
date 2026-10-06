"""
Mathematical Problem Solver - Master Launcher
=============================================
One-stop CLI entry point for:
- Synthetic dataset generation
- PySpark ETL execution & Parquet persistence
- Database schema initialization
- Gradio Web Application launch
- Running tests and benchmarks
"""

import os
import sys
import argparse
from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description="Mathematical Problem Solver: Big Data Analysis & Feedback System"
    )
    parser.add_argument(
        "--mode",
        choices=["all", "etl", "app", "generate-data", "benchmark", "test"],
        default="all",
        help="Execution mode: 'all' (runs ETL then launches Gradio UI), 'etl', 'app', 'generate-data', 'benchmark', 'test'"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("APP_PORT", 7860)),
        help="Gradio UI port (default: 7860)"
    )
    parser.add_argument(
        "--records",
        type=int,
        default=12000,
        help="Number of records to generate if data is missing (default: 12,000)"
    )

    args = parser.parse_args()

    raw_data_path = "data/raw/raw_problems.json"

    # Step 1: Ensure raw dataset exists
    if args.mode in ["all", "etl", "generate-data", "benchmark"]:
        if not os.path.exists(raw_data_path) or args.mode == "generate-data":
            print("[*] Generating synthetic raw mathematical dataset...")
            from scripts.generate_data import generate_dataset
            generate_dataset(num_records=args.records)

    # Step 2: Run PySpark ETL Pipeline
    if args.mode in ["all", "etl"]:
        print("\n[*] Starting PySpark Big Data ETL Pipeline...")
        from scripts.run_etl import run_pipeline
        run_pipeline(raw_file_path=raw_data_path, file_format="json")

    # Step 3: Run Benchmark
    if args.mode == "benchmark":
        print("\n[*] Executing Performance Benchmark (Pandas vs PySpark)...")
        from scripts.benchmark_pandas_vs_spark import run_benchmark
        run_benchmark()

    # Step 4: Run Tests
    if args.mode == "test":
        print("\n[*] Running project test suite...")
        import unittest
        loader = unittest.TestLoader()
        suite = loader.discover(start_dir="tests", pattern="test_*.py")
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite)

    # Step 5: Launch Gradio Web Application
    if args.mode in ["all", "app"]:
        print(f"\n[*] Launching Gradio Web Interface on http://localhost:{args.port}...")
        from app.gradio_app import create_app
        app = create_app()
        app.launch(server_name="0.0.0.0", server_port=args.port, share=False)


if __name__ == "__main__":
    main()
