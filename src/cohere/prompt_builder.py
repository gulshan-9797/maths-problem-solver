"""
Feedback-Driven Prompt Builder Module
======================================
Constructs dynamic, pedagogical prompts for the Cohere LLM by injecting:
1. Topic classification & calculated complexity score
2. Historical failure patterns & error rates computed by PySpark
3. High-risk step warnings (e.g. Step 3/Step 4) identified from user feedback
4. Pedagogical explanation directives tailored to difficulty level
"""

from typing import Dict, Any, Optional


def build_enhanced_math_prompt(
    problem_text: str,
    topic: str,
    difficulty: str,
    complexity_score: float,
    learning_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Constructs an enriched prompt providing learning guidance to Cohere.
    """
    if learning_context is None:
        learning_context = {
            "accuracy": 72.0,
            "avg_steps": 5,
            "common_wrong_steps": ["Step 3"],
            "common_feedback": ["Check intermediate signs and arithmetic"]
        }

    accuracy = learning_context.get("accuracy", 70.0)
    common_wrong_steps = ", ".join(learning_context.get("common_wrong_steps", ["Step 3"]))
    feedbacks = "; ".join(learning_context.get("common_feedback", ["Show all steps clearly"])[:2])

    system_guidance = f"""You are an expert mathematical problem solver and pedagogical tutor.
Your mission is to provide an crystal-clear, step-by-step rigorous solution to the user's mathematical problem.

--- HISTORICAL ANALYTICS CONTEXT (from PySpark ETL) ---
* Detected Mathematical Topic: {topic}
* Derived Difficulty Level: {difficulty}
* Mathematical Complexity Score: {complexity_score}/100
* System Historical Accuracy for {topic}: {accuracy}%
* High-Risk Vulnerable Steps for this Topic: {common_wrong_steps}
* Common User Feedback / Past Errors: {feedbacks}

--- PEDAGOGICAL INSTRUCTIONS ---
1. Break down the solution into explicit, clearly labeled steps: "Step 1: ...", "Step 2: ...", etc.
2. Pay special attention to {common_wrong_steps} where historical students/users frequently encounter errors.
3. Explicitly state each formula, theorem, or identity BEFORE applying it.
4. Show all intermediate calculations, factorizations, and sign changes without skipping steps.
5. Provide a clear, bold "Final Answer: ..." at the conclusion of your solution.
6. Verify the final answer by substituting back or applying an alternative sanity check.
"""

    user_query = f"""Please solve the following mathematical problem step-by-step:

{problem_text}
"""
    return system_guidance, user_query
