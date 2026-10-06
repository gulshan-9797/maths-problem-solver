"""
Unit Tests: Cohere Client & Prompt Builder
==========================================
Tests prompt enrichment with Big Data metrics and graceful fallback solver functionality.
"""

import unittest
from src.cohere.prompt_builder import build_enhanced_math_prompt
from src.cohere.client import CohereMathSolver


class TestCohereIntegration(unittest.TestCase):

    def test_prompt_builder_injections(self):
        ctx = {
            "accuracy": 61.5,
            "avg_steps": 8,
            "common_wrong_steps": ["Step 3", "Step 4"],
            "common_feedback": ["Explain integral substitution clearly"]
        }
        sys_prompt, user_query = build_enhanced_math_prompt(
            problem_text="Evaluate integral of x*sin(x) dx",
            topic="Calculus",
            difficulty="Hard",
            complexity_score=82.0,
            learning_context=ctx
        )

        self.assertIn("Calculus", sys_prompt)
        self.assertIn("82.0/100", sys_prompt)
        self.assertIn("61.5%", sys_prompt)
        self.assertIn("Step 3, Step 4", sys_prompt)
        self.assertIn("Evaluate integral of x*sin(x) dx", user_query)

    def test_solver_fallback_execution(self):
        # Instantiate solver without key
        solver = CohereMathSolver(api_key="mock_invalid_key_for_test")
        res = solver.solve_problem(
            problem_text="Find roots of 2x^2 + 5x - 3 = 0",
            topic="Algebra",
            difficulty="Medium",
            complexity_score=45.0
        )
        self.assertIn("solution", res)
        self.assertIn("Step 1", res["solution"])
        self.assertTrue(res["prompt_enhanced"])


if __name__ == "__main__":
    unittest.main()
