"""
PySpark Feature Engineering Module
==================================
Extracts analytical features from mathematical queries and solutions:
1. Topic Classification (Rule-based NLP & Keyword Scoring)
2. Step Count Extraction (Regex-based structural parsing)
3. Complexity Score Calculation (Deterministic 0-100 normalized formula)
4. Difficulty Level Derivation (Easy, Medium, Hard)
"""

try:
    from pyspark.sql import DataFrame
    from pyspark.sql.functions import udf, col, when
    from pyspark.sql.types import StringType, IntegerType, DoubleType
    HAS_PYSPARK = True
except ImportError:
    DataFrame = Any = object
    HAS_PYSPARK = False

# Keyword dictionaries for topic classification
TOPIC_KEYWORDS = {
    "Calculus": [
        "integral", "derivative", "differentiate", "antiderivative", "limit",
        "dx", "dy/dx", "chain rule", "product rule", "lhopital", "calculus"
    ],
    "Linear Algebra": [
        "matrix", "determinant", "eigenvalue", "eigenvector", "linear algebra",
        "invertible", "characteristic equation", "characteristic polynomial", "det(a)"
    ],
    "Probability": [
        "probability", "bayes", "conditional probability", "without replacement",
        "random", "posterior", "prior", "p(a", "p(b", "balls"
    ],
    "Statistics": [
        "z-score", "standard deviation", "variance", "sample mean", "mean",
        "normal distribution", "median", "mode", "dataset", "statistics"
    ],
    "Trigonometry": [
        "sin", "cos", "tan", "arcsin", "arccos", "arctan", "theta",
        "trigonometric", "pythagorean identity", "radians"
    ],
    "Geometry": [
        "surface area", "volume", "cylinder", "radius", "height", "triangle",
        "circle", "law of cosines", "perimeter", "geometry", "angle"
    ],
    "Number Theory": [
        "gcd", "lcm", "euclidean", "congruence", "modulo", "bezout",
        "divisor", "prime", "number theory"
    ],
    "Algebra": [
        "quadratic", "polynomial", "equation", "roots", "factor", "system",
        "simplify", "algebraic", "solve for x", "variable"
    ]
}

TOPIC_BASE_WEIGHTS = {
    "Calculus": 35.0,
    "Linear Algebra": 30.0,
    "Probability": 25.0,
    "Trigonometry": 25.0,
    "Number Theory": 22.0,
    "Geometry": 20.0,
    "Statistics": 18.0,
    "Algebra": 15.0
}


def classify_topic_py(problem_text: str, solution_text: str) -> str:
    """Rule-based topic classifier scoring keyword frequencies in text."""
    combined_text = f"{problem_text} {solution_text}".lower()
    
    scores = {}
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(combined_text.count(kw) for kw in keywords)
        scores[topic] = score
        
    best_topic = max(scores, key=scores.get)
    if scores[best_topic] == 0:
        return "Algebra"  # Default generic fallback
    return best_topic


def extract_step_count_py(solution_text: str) -> int:
    """Robust step extractor detecting 'Step X' tags, numbered lines, or structural delimiters."""
    if not solution_text or not solution_text.strip():
        return 1
        
    step_matches = re.findall(r'(?i)\bstep\s*\d+[:\.]?', solution_text)
    if step_matches:
        return len(step_matches)
        
    # Fallback 1: Numbered lines (e.g., '1.', '2.', '3.')
    numbered_lines = re.findall(r'(?m)^\s*\d+[\.\)]\s+', solution_text)
    if numbered_lines:
        return len(numbered_lines)
        
    # Fallback 2: Count distinct non-empty line segments with equations or reasoning
    lines = [line.strip() for line in solution_text.split("\n") if len(line.strip()) > 5]
    return max(1, min(len(lines), 12))


def calculate_complexity_score_py(
    problem_text: str,
    solution_text: str,
    topic: str,
    step_count: int
) -> float:
    """
    Computes a transparent, deterministic mathematical complexity score (0-100).
    
    Formula components:
    1. Base Topic Weight (15 - 35 points)
    2. Step Count Contribution (5 points per step, max 30 points)
    3. Mathematical Operator & Symbol Density (max 25 points)
    4. Variable & Equation Structure (max 10 points)
    """
    combined = f"{problem_text} {solution_text}".lower()
    
    # 1. Base topic weight
    base_weight = TOPIC_BASE_WEIGHTS.get(topic, 20.0)
    
    # 2. Step complexity (5 pts per step up to 30 pts)
    step_weight = min(float(step_count) * 5.0, 30.0)
    
    # 3. Mathematical operators & advanced notation
    advanced_operators = [
        "^", "sqrt", "integral", "derivative", "ln", "exp", "e^", "sigma",
        "lambda", "det", "pi", "theta", "matrix", "arcsin", "congruence", "delta"
    ]
    operator_count = sum(combined.count(op) for op in advanced_operators)
    operator_weight = min(float(operator_count) * 2.5, 25.0)
    
    # 4. Equation / Variable density
    eq_count = combined.count("=") + combined.count("+") + combined.count("-")
    equation_weight = min(float(eq_count) * 1.0, 10.0)
    
    # Total combined score bounded between 0.0 and 100.0
    total_score = base_weight + step_weight + operator_weight + equation_weight
    return round(min(100.0, max(5.0, total_score)), 2)


def derive_difficulty_level_py(complexity_score: float, step_count: int) -> str:
    """Categorizes problem into Easy, Medium, or Hard based on complexity score and steps."""
    if complexity_score >= 65.0 or step_count >= 6:
        return "Hard"
    elif complexity_score >= 40.0 or step_count >= 4:
        return "Medium"
    else:
        return "Easy"


import re

# Register PySpark UDFs if available
if HAS_PYSPARK:
    classify_topic_udf = udf(classify_topic_py, StringType())
    extract_step_count_udf = udf(extract_step_count_py, IntegerType())
    calculate_complexity_score_udf = udf(calculate_complexity_score_py, DoubleType())
    derive_difficulty_level_udf = udf(derive_difficulty_level_py, StringType())
else:
    classify_topic_udf = None
    extract_step_count_udf = None
    calculate_complexity_score_udf = None
    derive_difficulty_level_udf = None


def engineer_features(df: DataFrame) -> DataFrame:
    """
    Applies complete feature engineering pipeline to PySpark DataFrame.
    """
    # 1. Topic classification
    df_topic = df.withColumn(
        "topic",
        classify_topic_udf(col("problem_text"), col("generated_solution"))
    )
    
    # 2. Step count extraction
    df_steps = df_topic.withColumn(
        "step_count",
        extract_step_count_udf(col("generated_solution"))
    )
    
    # 3. Complexity score calculation
    df_complexity = df_steps.withColumn(
        "complexity_score",
        calculate_complexity_score_udf(
            col("problem_text"),
            col("generated_solution"),
            col("topic"),
            col("step_count")
        )
    )
    
    # 4. Difficulty classification
    df_features = df_complexity.withColumn(
        "difficulty",
        derive_difficulty_level_udf(col("complexity_score"), col("step_count"))
    )
    
    # 5. Weakness / Needs Improvement flag (Configurable threshold)
    # Flagged if complexity is high or correctness flag indicates failure
    df_final = df_features.withColumn(
        "needs_improvement",
        when((col("correctness_flag") == 0) | (col("complexity_score") > 70.0), True)
        .otherwise(False)
    )
    
    return df_final
