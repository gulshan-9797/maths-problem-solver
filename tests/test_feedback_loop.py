"""
Integration Tests: Feedback Loop & Learning Context
===================================================
Tests user feedback ingestion, database insertion, and dynamic learning context updates.
"""

import unittest
from src.feedback.feedback_processor import FeedbackProcessor
from src.database.postgres import db_manager


class TestFeedbackLoop(unittest.TestCase):

    def setUp(self):
        db_manager.initialize_schema()
        self.processor = FeedbackProcessor()

    def test_record_and_update_learning_context(self):
        # 1. Ingest negative feedback on Step 4 of Calculus
        res = self.processor.record_feedback(
            problem_id="prob_test_001",
            problem_text="Evaluate integral of e^(2x) dx",
            generated_solution="Step 1...\nStep 2...\nStep 3...\nStep 4: Missed factor 1/2.",
            topic="Calculus",
            difficulty="Hard",
            step_count=5,
            complexity_score=80.0,
            user_correctness="Incorrect",
            wrong_step="Step 4",
            feedback_text="Missed 1/2 factor in antiderivative"
        )

        self.assertIn(res["status"], ["success", "db_warning"])
        self.assertTrue(res["feedback_id"].startswith("fb_"))

        # 2. Verify learning context captures the reported wrong step
        ctx = self.processor.get_topic_learning_context("Calculus")
        self.assertIn("Step 4", ctx["common_wrong_steps"])
        self.assertIn("Missed 1/2 factor in antiderivative", ctx["common_feedback"])


if __name__ == "__main__":
    unittest.main()
