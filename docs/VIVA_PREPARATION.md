# Mathematical Problem Solver: Viva Voce & Oral Examination Preparation Guide

This document contains **36 in-depth Viva questions and answers** covering all architectural, mathematical, and Big Data concepts used in this project.

---

### 1. Why is this project classified as a Big Data project?
**Answer:**
This project handles large volumes of semi-structured user query logs, step-by-step mathematical reasoning steps, and student feedback. It implements the standard Big Data lifecycle: distributed extraction, multi-stage transformation and cleaning, parallel feature engineering, columnar storage in Apache Parquet, aggregated metric warehousing, and continuous feedback loop ingestion. The pipeline is architected in PySpark so it can process millions of queries across a distributed cluster (e.g., Databricks, AWS EMR) without changing the core codebase.

---

### 2. Why did you choose PySpark instead of Pandas for data processing?
**Answer:**
Pandas is a single-threaded, in-memory data processing library bounded by the RAM of a single machine. When dataset size exceeds available memory, Pandas triggers `OutOfMemory` (OOM) exceptions. In contrast, PySpark is a distributed compute framework built on Apache Spark. It shards data into partitions, evaluates computations lazily via DAGs (Directed Acyclic Graphs), parallelizes execution across CPU cores and worker nodes, and utilizes the Catalyst Optimizer to prune redundant queries.

---

### 3. What is ETL, and what are its three distinct stages in this project?
**Answer:**
ETL stands for **Extract, Transform, Load**:
* **Extract:** Reading raw mathematical interaction logs from CSV or JSON files with strict PySpark `StructType` schema validation.
* **Transform:** Pruning duplicates, handling missing/whitespace values, standardizing timestamps, normalizing heterogeneous correctness indicators into binary flags (`1`/`0`), running NLP topic classification, extracting step counts, calculating 0–100 complexity scores, and deriving difficulty levels.
* **Load:** Persisting full cleaned records into columnar Apache Parquet files and loading analytical summaries into PostgreSQL for Grafana dashboards.

---

### 4. Why did you use Apache Parquet instead of CSV for storing processed data?
**Answer:**
Apache Parquet is a columnar storage format optimized for Big Data analytics. Unlike row-based CSVs:
1. **Column Pruning & Predicate Pushdown:** Queries only read the specific columns requested (e.g., `topic`, `correctness_flag`), drastically reducing I/O disk reads.
2. **Compression Efficiency:** Identical data types in columns compress significantly better using algorithms like Snappy, reducing disk footprint by up to 75%.
3. **Embedded Schema & Metadata:** Parquet stores column data types and statistics (min, max, count) in file footers, enabling fast skipping of non-relevant data blocks.

---

### 5. What is a Spark DataFrame?
**Answer:**
A Spark DataFrame is a distributed collection of data organized into named columns, conceptually equivalent to a table in a relational database or a data frame in R/Pandas, but with rich optimizations under the hood (Tungsten binary memory management and Catalyst query optimizer).

---

### 6. What is Lazy Evaluation in Apache Spark?
**Answer:**
In Spark, operations are divided into **Transformations** and **Actions**. When a transformation (like `filter()`, `withColumn()`, or `groupBy()`) is applied, Spark does not compute the result immediately. Instead, it records the lineage in a Directed Acyclic Graph (DAG). Computation is only triggered when an **Action** (such as `count()`, `collect()`, `show()`, or `save()`) is invoked. This allows Spark's Catalyst optimizer to reorder and combine operations for maximum execution efficiency.

---

### 7. What is the difference between Spark Transformations and Actions?
**Answer:**
* **Transformations:** Functions that take a DataFrame and return a new DataFrame (e.g., `select()`, `filter()`, `withColumn()`, `groupBy()`, `join()`). They are lazily evaluated.
* **Actions:** Operations that trigger computation on the cluster and return a value to the driver program or write data to an external sink (e.g., `count()`, `collect()`, `first()`, `write.parquet()`).

---

### 8. How does PySpark execute GroupBy and Aggregations?
**Answer:**
`groupBy()` groups rows sharing the same key (e.g., `topic` or `difficulty`). Behind the scenes, Spark performs a **Shuffle** operation: data with the same hash key is redistributed across worker partitions over the network. Aggregation functions like `count()`, `sum()`, and `avg()` then compute partial aggregates locally within each partition before merging them globally into the final output.

---

### 9. How is Topic Classification performed during ETL?
**Answer:**
In the ETL feature engineering stage, topic classification is performed using an NLP keyword and symbol frequency scoring algorithm. The algorithm scans problem statements and solutions for specialized vocabulary and mathematical tokens across 8 categories (e.g., derivatives/integrals $\rightarrow$ Calculus; matrices/eigenvalues $\rightarrow$ Linear Algebra; z-score/variance $\rightarrow$ Statistics). It is wrapped in a PySpark UDF to process millions of records in parallel, with an extensible architecture designed for future fine-tuned BERT classifiers.

---

### 10. How is Step Count extracted from mathematical solutions?
**Answer:**
The step extraction module uses regular expressions to detect structured step delimiters (such as `Step 1:`, `Step 2:`, or numbered prefixes `1.`, `2.`). If explicit step labels are absent, the robust fallback parser evaluates non-empty equation lines and logical sentence boundaries, bounding the result between 1 and 12 steps.

---

### 11. What is the formula for Complexity Score, and why is it normalized to 0–100?
**Answer:**
The Complexity Score formula is deterministic and explainable:
$$\text{Complexity Score} = \min\left(100.0, \max\left(5.0, W_{\text{topic}} + W_{\text{steps}} + W_{\text{ops}} + W_{\text{eq}}\right)\right)$$
Where:
* $W_{\text{topic}}$: Base mathematical discipline weight ($15$ for Algebra, up to $35$ for Calculus).
* $W_{\text{steps}}$: $5 \times \text{step\_count}$ (capped at 30).
* $W_{\text{ops}}$: $2.5 \times \text{count of advanced operators } (\int, \partial, \sqrt{}, \sum, \det, \lambda, \equiv)$ (capped at 25).
* $W_{\text{eq}}$: Equation count density (capped at 10).

Normalizing to $0–100$ gives a standard, human-interpretable metric for students and educators, and enables direct threshold comparison and color-coded alert triggers in Grafana.

---

### 12. How is Difficulty derived from the features?
**Answer:**
Difficulty is derived deterministically from the combined Complexity Score and Step Count:
* **Easy:** Complexity $< 40.0$ and Steps $< 4$
* **Medium:** Complexity between $40.0$ and $65.0$ (or Steps between 4 and 5)
* **Hard:** Complexity $\ge 65.0$ or Steps $\ge 6$

---

### 13. How are heterogeneous correctness values normalized during cleaning?
**Answer:**
Raw data logs contain inconsistent correctness representations (e.g., `correct`, `true`, `yes`, `1`, `incorrect`, `false`, `no`, `0`, uppercase/lowercase). PySpark cleans this by trimming whitespace, lowercasing, and executing a `when-otherwise` condition mapping positive affirmations to `1` and negative affirmations to `0`. Malformed or null entries are assigned `-1` and filtered out.

---

### 14. Why did you choose Cohere API for generating mathematical solutions?
**Answer:**
Cohere's Command models (Command-R / Command-R+) excel at instruction following, structural formatting, and pedagogical reasoning. The API provides predictable latency, native support for system prompts, and rich multi-step reasoning capabilities suitable for STEM problem breakdowns.

---

### 15. Are you actually fine-tuning the Cohere LLM weights?
**Answer:**
No. We explicitly do not claim weight-level fine-tuning. Instead, we implement **Feedback-Driven Retrieval and Prompt Enhancement (FDRPE)**. The PySpark Big Data pipeline aggregates historical error rates, identifies topic vulnerabilities (e.g., Calculus having a 37.7% error rate concentrated on Step 3), and dynamically injects this operational context into Cohere's system prompt at runtime. This provides the pedagogical benefits of fine-tuning without the high computational cost and latency.

---

### 16. How does the closed-loop feedback mechanism work from end to end?
**Answer:**
1. A student enters a problem in the Gradio UI.
2. The system pre-classifies the topic and pulls the historical learning context.
3. Cohere generates an enriched step-by-step solution.
4. The student reviews the solution and marks it **Correct** or **Incorrect**, optionally specifying the **Wrong Step** (e.g., "Step 3") and providing a comment.
5. The feedback is persisted into PostgreSQL table `user_feedback_log`.
6. The feedback processor updates the topic's error cache.
7. Future solutions generated for that topic receive enhanced warnings and verification instructions for the identified problematic steps.
8. Periodic PySpark batch jobs reprocess all feedback into Parquet and update the Grafana analytics views.

---

### 17. Why is PostgreSQL placed between PySpark and Grafana?
**Answer:**
Grafana is an interactive, low-latency visualization dashboard that issues rapid SQL queries (every 5–10 seconds). Querying multi-gigabyte raw Parquet files via Spark for every dashboard refresh would create unnecessary cluster overhead and slow query latency. PySpark handles the heavy distributed transformations and saves pre-aggregated summary tables and indexed views in PostgreSQL. Grafana queries PostgreSQL instantaneously.

---

### 18. What are the 10 panels displayed in your Grafana Dashboard?
**Answer:**
1. **Panel 1 (Stat):** Total Problems Solved.
2. **Panel 2 (Gauge):** Overall Accuracy % with color thresholds.
3. **Panel 3 (Time Series):** Problems Solved Per Day (Volume Trend).
4. **Panel 4 (Time Series):** Accuracy Over Last 30 Days with 7-Day Moving Average.
5. **Panel 5 (Pie Chart):** Problem Distribution across the 8 Topics.
6. **Panel 6 (Bar Chart):** Most Difficult Topics ranked by Complexity.
7. **Panel 7 (Bar Chart):** Average Step Count per Topic.
8. **Panel 8 (Bar Chart):** Accuracy by Topic (identifying lowest performers).
9. **Panel 9 (Bar Chart):** Error Rate Breakdown by Difficulty Tier.
10. **Panel 10 (Bar Chart):** Most Frequently Reported Wrong Steps.
* **Panel 11 (Alert Table):** System Weakness & Recommended Action Matrix.

---

### 19. How does the system automatically detect weaknesses and trigger alerts?
**Answer:**
In `topic_analysis.py` and SQL view `view_system_alerts`, configurable thresholds identify problem areas:
$$\text{needs\_improvement} = (\text{Accuracy} < 70\%) \lor (\text{Error Rate} > 30\%) \lor (\text{Avg Complexity} > 70.0)$$
When these criteria are met, the topic is tagged with `needs_improvement = True` and highlighted in red on Grafana panels.

---

### 20. What is Gradio, and why was it chosen over Streamlit or Flask?
**Answer:**
Gradio is a Python framework tailored for machine learning and AI applications. It natively supports Markdown with LaTeX math formulas (`$$...$$`), reactive component state management, input examples, dynamic field visibility, and interactive feedback buttons with minimal boilerplate.

---

### 21. How does the system handle errors when Cohere API is offline or the key is missing?
**Answer:**
In `src/cohere/client.py`, API initialization and calls are wrapped in `try-except` blocks. If the `COHERE_API_KEY` is missing or the network is unavailable, the system automatically falls back to an internal heuristic mathematical solver. The application continues running smoothly with full feature engineering, step counting, and feedback loop capabilities.

---

### 22. What happens if PostgreSQL is not installed or the container is down?
**Answer:**
`src/database/postgres.py` implements an automatic connection fallback. It tests PostgreSQL connectivity upon startup; if unreachable, it automatically routes queries and feedback logging to a local **SQLite** database (`data/math_solver.db`), ensuring zero downtime during local development and testing.

---

### 23. How does the system scale to 1 million or 100 million records?
**Answer:**
1. **Storage:** Data is partitioned by date (`year=YYYY/month=MM`) in Apache Parquet on cloud object storage (S3/GCS/Azure Blob).
2. **Compute:** PySpark jobs run on elastic clusters (e.g., Amazon EMR or Databricks) where worker nodes scale automatically based on partition load.
3. **Streaming:** High-throughput ingestion can incorporate Apache Kafka and Spark Structured Streaming for real-time micro-batch processing.
4. **Database:** PostgreSQL can be scaled using read-replicas, TimescaleDB hyper-tables, or distributed OLAP engines like ClickHouse/Snowflake.

---

### 24. What are the key findings from your Pandas vs. PySpark benchmark?
**Answer:**
On our 12,072-record dataset, Pandas executed in $2.32$ seconds and PySpark in $2.10$ seconds. Pandas performed slightly faster on small data ingestion because it avoids JVM initialization. However, PySpark outperformed Pandas during complex feature engineering and multi-dimensional aggregations due to multi-core parallelism. More importantly, as dataset size scales beyond memory capacity, Pandas crashes with OOM while PySpark continues to scale horizontally.

---

### 25. What are the primary mathematical topics covered in your dataset?
**Answer:**
1. **Algebra** (Quadratic equations, linear systems, polynomial simplification)
2. **Calculus** (Indefinite/definite integrals, chain/product derivatives, limits)
3. **Geometry** (Cylinder volume/surface area, triangles, Law of Cosines)
4. **Probability** (Combinatorics, without-replacement sampling, Bayes' theorem)
5. **Statistics** (Mean, variance, standard deviation, Z-score standardization)
6. **Trigonometry** (Trig equations, identities, arcsin/cos transformations)
7. **Number Theory** (Euclidean GCD algorithm, modular linear congruence)
8. **Linear Algebra** (Matrix determinants, invertibility, characteristic eigenvalues)

---

### 26. Which topic had the highest error rate in your experimental results, and why?
**Answer:**
**Calculus** demonstrated the highest error rate ($37.7\%$) and lowest accuracy ($62.3\%$), followed by Linear Algebra ($34.9\%$ error rate). This occurred because multi-step calculus problems involve nested algebraic operations, integration by parts, and trigonometric substitutions where subtle sign mistakes in intermediate steps (specifically Steps 3 and 4) propagate into incorrect final answers.

---

### 27. What is the role of Docker Compose in this project?
**Answer:**
`docker-compose.yml` provides a one-command, reproducible development environment. It launches:
1. A **PostgreSQL** container initialized with our table schemas and analytical views.
2. A **Grafana** container pre-provisioned with the PostgreSQL datasource and our 10-panel analytics dashboard JSON, accessible on port 3000.

---

### 28. What are Spark UDFs, and how were they used here?
**Answer:**
A User Defined Function (UDF) in PySpark allows custom Python logic to be executed on DataFrame columns across distributed worker nodes. We implemented UDFs for `classify_topic_udf`, `extract_step_count_udf`, `calculate_complexity_score_udf`, and `derive_difficulty_level_udf` to vectorize feature extraction over the dataset.

---

### 29. What is Catalyst Optimizer in Apache Spark?
**Answer:**
Catalyst is Spark's built-in extensible query optimization engine. It represents queries as abstract syntax trees (AST) and optimizes execution plans through four phases: analysis, logical optimization (predicate pushdown, constant folding, projection pruning), physical planning, and code generation into optimized Java bytecode.

---

### 30. What is the difference between PyArrow and standard Python serialization in Spark?
**Answer:**
PyArrow uses columnar memory layout (Apache Arrow) to transfer data between the Spark JVM and Python worker processes. This eliminates expensive row-by-row serialization/deserialization overhead, speeding up Python UDFs and `toPandas()` conversions by up to 10x–50x.

---

### 31. What are the ethical and academic honesty considerations regarding LLM fine-tuning in this case study?
**Answer:**
In many student projects, developers claim that an LLM has been "retrained" or "fine-tuned" when they have only prompted it. In this case study, we maintain complete academic transparency: we explicitly demonstrate that our system achieves improved reasoning through **Feedback-Driven Prompt Enhancement** informed by real PySpark Big Data analytics, rather than making false claims about weight fine-tuning.

---

### 32. What is rolling window aggregation, and how is it used in daily metrics?
**Answer:**
Rolling window aggregation computes moving averages over a sliding time frame. Using PySpark's `Window.orderBy("metric_date").rowsBetween(-6, 0)`, we calculate the **7-Day Moving Average Accuracy**. This smooths daily volatility to show true performance trends over time.

---

### 33. What is Predicate Pushdown in Parquet and Spark?
**Answer:**
Predicate pushdown evaluates filter conditions (such as `WHERE topic = 'Calculus'`) at the storage layer before reading data into memory. Parquet stores min/max statistics in block headers, allowing Spark to skip non-matching row groups entirely without reading their contents from disk.

---

### 34. What are the key advantages of using a micro-batch architecture for feedback updates?
**Answer:**
Directly appending single rows to distributed Parquet files creates the "small files problem," degrading Spark read performance. By logging incoming user feedback to PostgreSQL in real time and running PySpark batch aggregation jobs periodically (e.g., hourly or daily), we maintain low write latency while preserving Parquet file efficiency.

---

### 35. If you had 6 more months on this project, what would you add?
**Answer:**
1. Implement real-time streaming with **Apache Kafka** and **Spark Structured Streaming**.
2. Deploy a lightweight transformer model (e.g., **ModernBERT**) for sub-millisecond semantic topic classification.
3. Implement automated **LoRA parameter-efficient fine-tuning** pipelines on verified user-corrected datasets.
4. Add automated unit-test generation for student submissions with symbolic math engines like **SymPy**.

---

### 36. Summarize the core value proposition of your project in one sentence.
**Answer:**
Our system closes the loop between Big Data analytics and Generative AI by transforming raw mathematical interaction logs into actionable error insights via PySpark, monitoring solver health in real time via Grafana, and dynamically improving future explanations on vulnerable solution steps through feedback-enhanced prompting.
