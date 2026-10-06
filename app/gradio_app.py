"""
Mathematical Problem Solver - Interactive Gradio Application
============================================================
Provides an end-to-end interface for:
1. Solving mathematical problems using Cohere API & PySpark-enriched prompts
2. Inspecting topic, difficulty, step count, and complexity metrics
3. Submitting user feedback (Correct/Incorrect + Wrong Step tag)
4. Monitoring live Big Data performance analytics and topic error bottlenecks
"""

import os
import uuid
import gradio as gr
import pandas as pd
from dotenv import load_dotenv

from src.etl.feature_engineering import (
    classify_topic_py,
    extract_step_count_py,
    calculate_complexity_score_py,
    derive_difficulty_level_py
)
from src.cohere.client import math_solver
from src.feedback.feedback_processor import feedback_processor
from src.database.postgres import db_manager

load_dotenv()

SAMPLE_PROBLEMS = [
    ["Calculus: Evaluate the indefinite integral of (4x^3 - 3*sin(2x) + e^(5x)) dx"],
    ["Algebra: Solve the quadratic equation 2x^2 + 7x - 15 = 0 for x."],
    ["Linear Algebra: Compute the determinant of matrix A = [[4, 2], [3, 8]] and find if it is invertible."],
    ["Probability: A bag has 5 red and 7 blue balls. Two balls are drawn without replacement. Find P(both red)."],
    ["Trigonometry: Solve for theta in [0, 2*pi): 2*sin^2(theta) - sin(theta) = 0."],
    ["Statistics: Calculate mean, variance, and standard deviation for dataset: [12, 18, 25, 30, 45]."],
    ["Geometry: Calculate surface area and volume of a cylinder with radius 5 cm and height 12 cm."],
    ["Number Theory: Find gcd(144, 84) using the Euclidean algorithm."]
]


def solve_and_analyze(problem_input: str):
    """
    Solves problem, runs feature engineering, and pulls feedback context.
    """
    if not problem_input or not problem_input.strip():
        return (
            "⚠️ Please enter a mathematical problem to solve.",
            "N/A", "N/A", "0/100", "0",
            "N/A", "", gr.update(visible=False), "",
            "None"
        )

    # 1. Feature Engineering & Pre-Classification
    temp_topic = classify_topic_py(problem_input, "")
    temp_steps = 5  # baseline expectation
    complexity_score = calculate_complexity_score_py(problem_input, "", temp_topic, temp_steps)
    difficulty = derive_difficulty_level_py(complexity_score, temp_steps)

    # 2. Retrieve Learning Context from PySpark Analytics / Live Feedback Loop
    learning_ctx = feedback_processor.get_topic_learning_context(temp_topic)

    # 3. Generate Solution via Cohere API
    solver_res = math_solver.solve_problem(
        problem_text=problem_input,
        topic=temp_topic,
        difficulty=difficulty,
        complexity_score=complexity_score,
        learning_context=learning_ctx
    )
    solution_text = solver_res["solution"]

    # 4. Refine Feature Metrics with Generated Solution
    final_topic = classify_topic_py(problem_input, solution_text)
    actual_step_count = extract_step_count_py(solution_text)
    final_complexity = calculate_complexity_score_py(problem_input, solution_text, final_topic, actual_step_count)
    final_difficulty = derive_difficulty_level_py(final_complexity, actual_step_count)

    # Generate unique problem identifier for this session
    problem_id = f"prob_{uuid.uuid4().hex[:10]}"

    learning_badge = (
        f"🎯 **Applied Learning Context for {final_topic}:** Historical Accuracy: {learning_ctx.get('accuracy', 70)}% | "
        f"Monitored Step Vulnerabilities: {', '.join(learning_ctx.get('common_wrong_steps', ['Step 3']))}"
    )

    return (
        solution_text,
        f"📐 {final_topic}",
        f"⚡ {final_difficulty}",
        f"📊 {final_complexity:.1f}/100",
        f"🔢 {actual_step_count} Steps",
        learning_badge,
        problem_id,
        gr.update(visible=True),  # make feedback section visible
        "",  # reset feedback message
        problem_input
    )


def toggle_feedback_fields(choice: str):
    """Shows wrong step selector only when 'Incorrect' is selected."""
    if choice == "Incorrect":
        return gr.update(visible=True), gr.update(visible=True)
    return gr.update(visible=False), gr.update(visible=True)


def submit_user_feedback(
    problem_id: str,
    problem_text: str,
    generated_solution: str,
    topic_str: str,
    diff_str: str,
    step_count_str: str,
    complexity_str: str,
    correctness_choice: str,
    wrong_step_choice: str,
    feedback_comments: str
):
    """Submits user feedback into the persistent database and triggers learning loop."""
    if not problem_id or not generated_solution:
        return "⚠️ No active solution to submit feedback for."

    # Parse clean values
    topic = topic_str.replace("📐 ", "").strip()
    difficulty = diff_str.replace("⚡ ", "").strip()
    try:
        step_count = int(step_count_str.replace("🔢 ", "").replace(" Steps", "").strip())
    except Exception:
        step_count = 5
    try:
        complexity = float(complexity_str.replace("📊 ", "").replace("/100", "").strip())
    except Exception:
        complexity = 50.0

    wrong_step = wrong_step_choice if correctness_choice == "Incorrect" else ""

    res = feedback_processor.record_feedback(
        problem_id=problem_id,
        problem_text=problem_text,
        generated_solution=generated_solution,
        topic=topic,
        difficulty=difficulty,
        step_count=step_count,
        complexity_score=complexity,
        user_correctness=correctness_choice,
        wrong_step=wrong_step,
        feedback_text=feedback_comments
    )

    return f"✅ Feedback submitted successfully (ID: `{res['feedback_id']}`). PySpark feedback loop updated!"


def load_analytics_tables():
    """Fetches real-time analytics tables from database for UI dashboard."""
    try:
        topic_df = db_manager.query_df("SELECT topic, total_problems, accuracy_percentage, error_rate_percentage, avg_step_count, avg_complexity_score, needs_improvement FROM topic_analytics_summary ORDER BY accuracy_percentage ASC")
    except Exception:
        topic_df = pd.DataFrame(columns=["topic", "total_problems", "accuracy_percentage", "error_rate_percentage", "avg_step_count", "avg_complexity_score", "needs_improvement"])

    try:
        diff_df = db_manager.query_df("SELECT difficulty, total_problems, accuracy_percentage, error_rate_percentage, avg_step_count, avg_complexity_score FROM difficulty_analytics_summary")
    except Exception:
        diff_df = pd.DataFrame(columns=["difficulty", "total_problems", "accuracy_percentage", "error_rate_percentage", "avg_step_count", "avg_complexity_score"])

    try:
        kpi_df = db_manager.query_df("SELECT COUNT(*) as total_problems, ROUND(AVG(correctness_flag)*100, 2) as accuracy, ROUND(AVG(complexity_score), 2) as avg_complexity, ROUND(AVG(step_count), 2) as avg_steps FROM processed_problem_analytics")
        if not kpi_df.empty and kpi_df.iloc[0]["total_problems"] > 0:
            kpi_text = (
                f"### 📊 Big Data Analytics Summary\n"
                f"- **Total Problems Processed by PySpark:** {int(kpi_df.iloc[0]['total_problems']):,}\n"
                f"- **Overall System Accuracy:** {kpi_df.iloc[0]['accuracy']}%\n"
                f"- **Average Problem Complexity:** {kpi_df.iloc[0]['avg_complexity']}/100\n"
                f"- **Average Solution Steps:** {kpi_df.iloc[0]['avg_steps']} steps"
            )
        else:
            kpi_text = "### 📊 Big Data Analytics Summary\nRun the PySpark ETL pipeline (`python scripts/run_etl.py`) to populate summary metrics."
    except Exception:
        kpi_text = "### 📊 Analytics database initialized."

    return kpi_text, topic_df, diff_df


# ------------------------------------------------------------------------------
# Build Gradio Blocks Interface
# ------------------------------------------------------------------------------
def create_app() -> gr.Blocks:
    theme = gr.themes.Soft(
        primary_hue="indigo",
        secondary_hue="blue",
        neutral_hue="slate"
    )

    with gr.Blocks(theme=theme, title="Mathematical Problem Solver - Analytics & Feedback System") as app:
        gr.Markdown(
            """
            # 🧮 Mathematical Problem Solver & Performance Monitoring System
            ### *Big Data Analytics (PySpark) • AI Solver (Cohere) • Live Feedback Loop • Monitoring (Grafana)*
            """
        )

        with gr.Tabs():
            # TAB 1: SOLVER & FEEDBACK LOOP
            with gr.TabItem("🚀 Problem Solver & Feedback"):
                with gr.Row():
                    # Left Column: Input
                    with gr.Column(scale=5):
                        gr.Markdown("### 📝 1. Enter Mathematical Problem")
                        problem_input = gr.Textbox(
                            label="Mathematical Query",
                            placeholder="Enter problem (e.g., Evaluate integral of 4x^3 - 3*sin(2x) dx, or solve quadratic equation)...",
                            lines=4,
                            value="Evaluate the indefinite integral: integral of (4x^3 - 3*sin(2x) + e^(5x)) dx"
                        )
                        solve_btn = gr.Button("🔍 Solve Problem", variant="primary", size="lg")

                        gr.Markdown("#### 💡 Quick Examples")
                        gr.Examples(
                            examples=SAMPLE_PROBLEMS,
                            inputs=[problem_input]
                        )

                    # Right Column: Derived Features & Solution
                    with gr.Column(scale=7):
                        gr.Markdown("### 🧠 2. Problem Classification & Generated Solution")
                        
                        with gr.Row():
                            topic_badge = gr.Textbox(label="Detected Topic", interactive=False)
                            diff_badge = gr.Textbox(label="Difficulty Tier", interactive=False)
                            comp_badge = gr.Textbox(label="Complexity Score", interactive=False)
                            step_badge = gr.Textbox(label="Step Count", interactive=False)

                        learning_info = gr.Markdown("Applied Learning Context will appear here after analysis.")
                        solution_output = gr.Markdown(label="Generated Step-by-Step Solution")

                # Section 3: User Feedback Loop
                with gr.Group(visible=False) as feedback_group:
                    gr.Markdown("---")
                    gr.Markdown("### 💬 3. User Feedback & Verification (Continuous Learning Loop)")
                    
                    with gr.Row():
                        correctness_radio = gr.Radio(
                            choices=["Correct", "Incorrect"],
                            value="Correct",
                            label="Was this solution mathematically correct?",
                            interactive=True
                        )
                        wrong_step_dropdown = gr.Dropdown(
                            choices=["Step 1", "Step 2", "Step 3", "Step 4", "Step 5", "Step 6", "Final Answer", "Other"],
                            label="Which step was incorrect / skipped?",
                            value="Step 3",
                            visible=False,
                            interactive=True
                        )

                    feedback_text = gr.Textbox(
                        label="What went wrong / suggestions for improvement? (Optional)",
                        placeholder="e.g., Missed negative sign during substitution in Step 3, skipped intermediate derivative..."
                    )

                    submit_fb_btn = gr.Button("📨 Submit Feedback to PySpark Pipeline", variant="secondary")
                    feedback_status = gr.Markdown("")

                # Hidden State holders
                problem_id_holder = gr.State("")
                original_problem_holder = gr.State("")

                # Wire Events
                solve_btn.click(
                    fn=solve_and_analyze,
                    inputs=[problem_input],
                    outputs=[
                        solution_output,
                        topic_badge,
                        diff_badge,
                        comp_badge,
                        step_badge,
                        learning_info,
                        problem_id_holder,
                        feedback_group,
                        feedback_status,
                        original_problem_holder
                    ]
                )

                correctness_radio.change(
                    fn=toggle_feedback_fields,
                    inputs=[correctness_radio],
                    outputs=[wrong_step_dropdown, feedback_group]
                )

                submit_fb_btn.click(
                    fn=submit_user_feedback,
                    inputs=[
                        problem_id_holder,
                        original_problem_holder,
                        solution_output,
                        topic_badge,
                        diff_badge,
                        step_badge,
                        comp_badge,
                        correctness_radio,
                        wrong_step_dropdown,
                        feedback_text
                    ],
                    outputs=[feedback_status]
                )

            # TAB 2: LIVE BIG DATA ANALYTICS & MONITORING
            with gr.TabItem("📈 Big Data Analytics & System Bottlenecks"):
                gr.Markdown("## 🔍 PySpark Analytics Summary & Performance Bottleneck Detection")
                refresh_btn = gr.Button("🔄 Refresh Analytics from Database", variant="secondary")

                kpi_display = gr.Markdown()

                gr.Markdown("### 🎯 Performance & Error Rates by Mathematical Topic")
                topic_table = gr.DataFrame(label="Topic Performance (PySpark Aggregations)")

                gr.Markdown("### ⚡ Performance Breakdown by Difficulty Tier")
                diff_table = gr.DataFrame(label="Difficulty Tier Metrics")

                refresh_btn.click(
                    fn=load_analytics_tables,
                    inputs=[],
                    outputs=[kpi_display, topic_table, diff_table]
                )
                
                # Load initially
                app.load(
                    fn=load_analytics_tables,
                    inputs=[],
                    outputs=[kpi_display, topic_table, diff_table]
                )

            # TAB 3: SYSTEM ARCHITECTURE & GRAFANA GUIDE
            with gr.TabItem("🏛️ Architecture & Monitoring Guide"):
                gr.Markdown(
                    """
                    ## 🏗️ End-to-End System Architecture

                    ```text
                    User Input (Gradio UI) ──► Feature Engineering (Topic/Difficulty/Complexity)
                                                        │
                                                        ▼
                    Cohere API ◄── Prompt Enhancement (Injected PySpark Analytics Context)
                         │
                         ▼
                    Step-by-Step Solution ──► User Feedback (Correct / Incorrect / Wrong Step)
                                                        │
                                                        ▼
                    Relational Storage (PostgreSQL) ◄── Feedback Ingestion
                                 │
                                 ▼
                    PySpark Big Data ETL Pipeline (Extract -> Clean -> Classify -> Metrics -> Parquet)
                                 │
                                 ▼
                    Aggregated Metrics & Views ──► Grafana Monitoring Dashboard (10 Real-Time Panels)
                    ```

                    ### 📊 Grafana 10-Panel Monitoring Specification
                    * **Panel 1:** Total Problems Solved (Stat)
                    * **Panel 2:** Overall Accuracy Rate % (Stat / Gauge)
                    * **Panel 3:** Problems Solved Per Day (Time Series)
                    * **Panel 4:** Accuracy Over Last 30 Days (Time Series)
                    * **Panel 5:** Problem Distribution by Topic (Bar / Pie)
                    * **Panel 6:** Most Difficult Topics ranked by Complexity (Bar)
                    * **Panel 7:** Average Step Count by Topic (Bar)
                    * **Panel 8:** Accuracy by Topic & Critical Alert Badges (Bar)
                    * **Panel 9:** Error Rate by Difficulty Tier (Bar)
                    * **Panel 10:** Feedback & Most Frequent Wrong Steps (Bar)
                    """
                )

    return app


if __name__ == "__main__":
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=7860, share=False)
