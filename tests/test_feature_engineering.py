"""
Unit Tests: Feature Engineering Functions
==========================================
Tests topic classification NLP, step extraction, difficulty determination,
and 0-100 complexity score calculation formulas.
"""

import unittest
from src.etl.feature_engineering import (
    classify_topic_py,
    extract_step_count_py,
    calculate_complexity_score_py,
    derive_difficulty_level_py
)


class TestFeatureEngineering(unittest.TestCase):

    def test_topic_classification(self):
        # Calculus
        calc_topic = classify_topic_py("Evaluate the indefinite integral of sin(x) dx", "Apply antiderivative rules.")
        self.assertEqual(calc_topic, "Calculus")

        # Linear Algebra
        la_topic = classify_topic_py("Find the determinant of matrix A = [[1, 2], [3, 4]]", "det(A) = ad - bc")
        self.assertEqual(la_topic, "Linear Algebra")

        # Geometry
        geom_topic = classify_topic_py("Find volume and surface area of a cylinder with radius r and height h", "V = pi * r^2 * h")
        self.assertEqual(geom_topic, "Geometry")

        # Probability
        prob_topic = classify_topic_py("Calculate P(A|B) using Bayes theorem with prior probability", "Posterior probability calculation.")
        self.assertEqual(prob_topic, "Probability")

    def test_step_count_extraction(self):
        sol_with_tags = (
            "Step 1: Form characteristic equation.\n"
            "Step 2: Solve quadratic polynomial.\n"
            "Step 3: Extract eigenvalues.\n"
            "Final Answer: lambda = 3, 5"
        )
        self.assertEqual(extract_step_count_py(sol_with_tags), 3)

        sol_with_numbered_lines = (
            "1. Identify terms.\n"
            "2. Integrate both sides.\n"
            "3. Add integration constant C.\n"
            "4. Verify result.\n"
        )
        self.assertEqual(extract_step_count_py(sol_with_numbered_lines), 4)

        # Empty fallback
        self.assertGreaterEqual(extract_step_count_py(""), 1)

    def test_complexity_score_bounds(self):
        # High complexity problem
        high_comp = calculate_complexity_score_py(
            "Evaluate integral of (x^3 * e^(2x) + matrix determinant det(A)) dx with lambda eigenvalues",
            "Step 1 to Step 8 with multiple integral and differential expansions",
            "Calculus",
            8
        )
        self.assertGreaterEqual(high_comp, 65.0)
        self.assertLessEqual(high_comp, 100.0)

        # Low complexity problem
        low_comp = calculate_complexity_score_py(
            "Simplify 2x + 3x",
            "Combine like terms: 5x",
            "Algebra",
            1
        )
        self.assertLessEqual(low_comp, 40.0)
        self.assertGreaterEqual(low_comp, 0.0)

    def test_difficulty_derivation(self):
        self.assertEqual(derive_difficulty_level_py(25.0, 2), "Easy")
        self.assertEqual(derive_difficulty_level_py(50.0, 4), "Medium")
        self.assertEqual(derive_difficulty_level_py(78.0, 7), "Hard")


if __name__ == "__main__":
    unittest.main()
