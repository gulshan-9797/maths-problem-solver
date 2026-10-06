"""
Mathematical Problem Solver - Synthetic Dataset Generator
==========================================================
Generates a realistic, large-scale dataset (12,000+ records) containing diverse 
mathematical problems, step-by-step solutions, difficulty indicators, 
and user feedback across 8 mathematical topics.

Topics covered:
1. Algebra
2. Calculus
3. Geometry
4. Probability
5. Statistics
6. Trigonometry
7. Number Theory
8. Linear Algebra
"""

import os
import json
import csv
import random
import uuid
from datetime import datetime, timedelta

# Topics and their problem/solution templates with realistic step counts & error patterns
TOPIC_TEMPLATES = {
    "Algebra": [
        {
            "problem": "Solve for x: {a}x^2 + {b}x + {c} = 0",
            "solution_steps": [
                "Step 1: Identify quadratic coefficients a = {a}, b = {b}, c = {c}.",
                "Step 2: Apply the quadratic formula x = (-b +- sqrt(b^2 - 4ac)) / (2a).",
                "Step 3: Compute discriminant Delta = ({b})^2 - 4*({a})*({c}) = {disc}.",
                "Step 4: Calculate square root: sqrt(Delta) = {sqrt_disc:.2f}.",
                "Step 5: Solve for the two roots: x1 = {x1:.2f}, x2 = {x2:.2f}."
            ],
            "final_answer": "x = {x1:.2f} or x = {x2:.2f}",
            "wrong_step_options": ["Step 3", "Step 4", "Step 2"],
            "base_complexity": 45,
            "difficulty": "Medium",
            "keywords": ["equation", "quadratic", "polynomial", "variable", "solve", "roots"]
        },
        {
            "problem": "Solve the system of linear equations: {a}x + {b}y = {c} and {d}x - {e}y = {f}",
            "solution_steps": [
                "Step 1: Express x in terms of y from equation 1: x = ({c} - {b}y) / {a}.",
                "Step 2: Substitute expression for x into equation 2: {d}(({c} - {b}y) / {a}) - {e}y = {f}.",
                "Step 3: Clear denominators and group y terms.",
                "Step 4: Solve for y = {y_val:.2f}.",
                "Step 5: Substitute y back to obtain x = {x_val:.2f}."
            ],
            "final_answer": "(x, y) = ({x_val:.2f}, {y_val:.2f})",
            "wrong_step_options": ["Step 2", "Step 3", "Step 4"],
            "base_complexity": 48,
            "difficulty": "Medium",
            "keywords": ["system", "equations", "linear", "substitution", "variables"]
        },
        {
            "problem": "Simplify the algebraic expression: ({a}x^3 - {b}x) / ({c}x)",
            "solution_steps": [
                "Step 1: Factor out common variable x from numerator: x({a}x^2 - {b}).",
                "Step 2: Cancel out non-zero common factor x in numerator and denominator.",
                "Step 3: Divide remaining terms by {c}: ({a}x^2 - {b}) / {c}."
            ],
            "final_answer": "({a}x^2 - {b}) / {c}",
            "wrong_step_options": ["Step 1", "Step 2"],
            "base_complexity": 25,
            "difficulty": "Easy",
            "keywords": ["simplify", "algebraic", "factor", "expression"]
        }
    ],
    "Calculus": [
        {
            "problem": "Evaluate the indefinite integral: integral of ({a}x^3 - {b}*sin({c}x) + e^({d}x)) dx",
            "solution_steps": [
                "Step 1: Decompose into sum of elementary integrals: {a}*integral(x^3 dx) - {b}*integral(sin({c}x) dx) + integral(e^({d}x) dx).",
                "Step 2: Integrate power term: {a} * (x^4 / 4) = {a4:.2f}x^4.",
                "Step 3: Integrate trigonometric term: -{b} * (-cos({c}x) / {c}) = +({b_c:.2f})cos({c}x).",
                "Step 4: Integrate exponential term: (1/{d}) * e^({d}x).",
                "Step 5: Combine all antiderivative components and append constant of integration + C."
            ],
            "final_answer": "{a4:.2f}x^4 + {b_c:.2f}cos({c}x) + (1/{d})e^({d}x) + C",
            "wrong_step_options": ["Step 3", "Step 4", "Step 2"],
            "base_complexity": 82,
            "difficulty": "Hard",
            "keywords": ["integral", "derivative", "calculus", "antiderivative", "exponential", "trigonometric"]
        },
        {
            "problem": "Find the derivative f'(x) using the product rule for f(x) = ({a}x^2 + {b}) * ln({c}x)",
            "solution_steps": [
                "Step 1: Set u(x) = {a}x^2 + {b} and v(x) = ln({c}x).",
                "Step 2: Differentiate u: u'(x) = 2*{a}x = {two_a}x.",
                "Step 3: Differentiate v: v'(x) = 1/x by chain rule.",
                "Step 4: Apply product rule f'(x) = u'v + uv': ({two_a}x)*ln({c}x) + ({a}x^2 + {b})*(1/x).",
                "Step 5: Simplify algebraic terms: {two_a}x*ln({c}x) + {a}x + {b}/x."
            ],
            "final_answer": "f'(x) = {two_a}x ln({c}x) + {a}x + {b}/x",
            "wrong_step_options": ["Step 3", "Step 4", "Step 5"],
            "base_complexity": 75,
            "difficulty": "Hard",
            "keywords": ["derivative", "product rule", "calculus", "logarithm", "differentiation"]
        },
        {
            "problem": "Evaluate the limit: lim (x -> 0) of (sin({a}x) / ({b}x))",
            "solution_steps": [
                "Step 1: Note indeterminate form 0/0 as x approaches 0.",
                "Step 2: Rewrite using fundamental limit: ({a}/{b}) * [lim (sin({a}x)/{a}x)].",
                "Step 3: Since lim (u->0) sin(u)/u = 1, compute ({a}/{b}) * 1 = {ratio:.2f}."
            ],
            "final_answer": "{ratio:.2f}",
            "wrong_step_options": ["Step 2", "Step 3"],
            "base_complexity": 55,
            "difficulty": "Medium",
            "keywords": ["limit", "calculus", "indeterminate", "lhopital", "trig limit"]
        }
    ],
    "Geometry": [
        {
            "problem": "Calculate the surface area and volume of a right circular cylinder with radius r = {r} cm and height h = {h} cm.",
            "solution_steps": [
                "Step 1: Calculate base area A_base = pi * r^2 = 3.1416 * {r}^2 = {base_area:.2f} cm^2.",
                "Step 2: Calculate lateral surface area A_lat = 2 * pi * r * h = 2 * 3.1416 * {r} * {h} = {lat_area:.2f} cm^2.",
                "Step 3: Sum total surface area: 2*A_base + A_lat = {tot_area:.2f} cm^2.",
                "Step 4: Compute volume V = A_base * h = {vol:.2f} cm^3."
            ],
            "final_answer": "Surface Area = {tot_area:.2f} cm^2, Volume = {vol:.2f} cm^3",
            "wrong_step_options": ["Step 2", "Step 3", "Step 4"],
            "base_complexity": 42,
            "difficulty": "Medium",
            "keywords": ["cylinder", "radius", "height", "surface area", "volume", "geometry", "circle"]
        },
        {
            "problem": "In triangle ABC, side a = {a}, side b = {b}, and included angle C = {angle} degrees. Find side c using the Law of Cosines.",
            "solution_steps": [
                "Step 1: State Law of Cosines: c^2 = a^2 + b^2 - 2ab*cos(C).",
                "Step 2: Convert angle {angle} to radians and calculate cos({angle} deg) = {cos_val:.3f}.",
                "Step 3: Compute a^2 + b^2 = {a}^2 + {b}^2 = {sum_sq}.",
                "Step 4: Compute 2*a*b*cos(C) = 2*{a}*{b}*{cos_val:.3f} = {sub_term:.2f}.",
                "Step 5: Calculate c^2 = {sum_sq} - {sub_term:.2f} = {c_sq:.2f}.",
                "Step 6: Take square root: c = sqrt({c_sq:.2f}) = {c_val:.2f}."
            ],
            "final_answer": "c = {c_val:.2f}",
            "wrong_step_options": ["Step 2", "Step 4", "Step 5"],
            "base_complexity": 62,
            "difficulty": "Hard",
            "keywords": ["triangle", "law of cosines", "geometry", "angle", "sides"]
        }
    ],
    "Probability": [
        {
            "problem": "A box contains {red} red balls and {blue} blue balls. Two balls are drawn without replacement. Find the probability that both are red.",
            "solution_steps": [
                "Step 1: Calculate total number of balls N = {red} + {blue} = {tot_balls}.",
                "Step 2: Probability that 1st ball is red: P(R1) = {red}/{tot_balls}.",
                "Step 3: After drawing 1 red, remaining red balls = {red_minus_1} and total remaining = {tot_minus_1}.",
                "Step 4: Conditional probability P(R2 | R1) = {red_minus_1}/{tot_minus_1}.",
                "Step 5: Multiply joint probability: P(R1 and R2) = P(R1) * P(R2 | R1) = {prob:.4f}."
            ],
            "final_answer": "P(both red) = {prob:.4f}",
            "wrong_step_options": ["Step 3", "Step 4", "Step 5"],
            "base_complexity": 58,
            "difficulty": "Medium",
            "keywords": ["probability", "conditional", "without replacement", "event", "balls", "random"]
        },
        {
            "problem": "Apply Bayes theorem: Given P(A) = {pa:.2f}, P(B|A) = {pba:.2f}, and P(B|A') = {pb_not_a:.2f}, find P(A|B).",
            "solution_steps": [
                "Step 1: Compute P(A') = 1 - P(A) = {p_not_a:.2f}.",
                "Step 2: Compute marginal probability P(B) = P(B|A)P(A) + P(B|A')P(A') = {pb:.4f}.",
                "Step 3: State Bayes Formula: P(A|B) = [P(B|A) * P(A)] / P(B).",
                "Step 4: Calculate numerator: {pba:.2f} * {pa:.2f} = {p_joint:.4f}.",
                "Step 5: Compute posterior probability: {p_joint:.4f} / {pb:.4f} = {p_post:.4f}."
            ],
            "final_answer": "P(A|B) = {p_post:.4f}",
            "wrong_step_options": ["Step 2", "Step 4", "Step 5"],
            "base_complexity": 78,
            "difficulty": "Hard",
            "keywords": ["bayes theorem", "probability", "posterior", "prior", "conditional"]
        }
    ],
    "Statistics": [
        {
            "problem": "Calculate the sample mean, sample variance, and standard deviation for the dataset: [{dataset_str}].",
            "solution_steps": [
                "Step 1: Count number of observations n = {n}.",
                "Step 2: Calculate sum of values: Sigma(x) = {sum_x}.",
                "Step 3: Compute sample mean: x_bar = {sum_x} / {n} = {mean_x:.2f}.",
                "Step 4: Compute squared deviations Sigma((x - x_bar)^2) = {sum_sq_dev:.2f}.",
                "Step 5: Calculate sample variance s^2 = sum_sq_dev / (n - 1) = {var_x:.2f}.",
                "Step 6: Compute standard deviation s = sqrt(s^2) = {std_x:.2f}."
            ],
            "final_answer": "Mean = {mean_x:.2f}, Variance = {var_x:.2f}, Std Dev = {std_x:.2f}",
            "wrong_step_options": ["Step 4", "Step 5", "Step 6"],
            "base_complexity": 52,
            "difficulty": "Medium",
            "keywords": ["statistics", "mean", "variance", "standard deviation", "dataset", "sample"]
        },
        {
            "problem": "A normal distribution has mean mu = {mu} and standard deviation sigma = {sigma}. Calculate the Z-score for value X = {x_val}.",
            "solution_steps": [
                "Step 1: State the Z-score standardization formula: Z = (X - mu) / sigma.",
                "Step 2: Substitute values: ({x_val} - {mu}) / {sigma}.",
                "Step 3: Calculate difference: {diff}.",
                "Step 4: Divide by sigma to get Z = {z_score:.2f}."
            ],
            "final_answer": "Z = {z_score:.2f}",
            "wrong_step_options": ["Step 2", "Step 4"],
            "base_complexity": 30,
            "difficulty": "Easy",
            "keywords": ["z-score", "normal distribution", "mean", "standard deviation", "statistics"]
        }
    ],
    "Trigonometry": [
        {
            "problem": "Solve for theta in [0, 2*pi): {a}*sin^2(theta) - {b}*sin(theta) = 0",
            "solution_steps": [
                "Step 1: Factor trigonometric polynomial: sin(theta) * ({a}*sin(theta) - {b}) = 0.",
                "Step 2: Branch 1: sin(theta) = 0 => theta = 0, pi.",
                "Step 3: Branch 2: sin(theta) = {b}/{a} = {sin_ratio:.2f}.",
                "Step 4: If ratio <= 1, find principal angles theta = arcsin({sin_ratio:.2f}) and pi - arcsin({sin_ratio:.2f}).",
                "Step 5: Consolidate all unique valid angles in [0, 2*pi)."
            ],
            "final_answer": "theta in {{{angles_str}}}",
            "wrong_step_options": ["Step 3", "Step 4", "Step 5"],
            "base_complexity": 68,
            "difficulty": "Hard",
            "keywords": ["trigonometry", "sin", "cos", "theta", "angle", "identity", "arcsin"]
        },
        {
            "problem": "Verify the trigonometric identity: (1 - cos^2(x)) / sin(x) = sin(x)",
            "solution_steps": [
                "Step 1: Apply Pythagorean identity 1 - cos^2(x) = sin^2(x).",
                "Step 2: Substitute into numerator: sin^2(x) / sin(x).",
                "Step 3: Simplify fraction: sin(x) = sin(x). Identity verified."
            ],
            "final_answer": "Verified LHS = RHS = sin(x)",
            "wrong_step_options": ["Step 1", "Step 2"],
            "base_complexity": 32,
            "difficulty": "Easy",
            "keywords": ["identity", "pythagorean", "sin", "cos", "trigonometry"]
        }
    ],
    "Number Theory": [
        {
            "problem": "Find the greatest common divisor gcd({a}, {b}) using the Euclidean algorithm and express as linear combination.",
            "solution_steps": [
                "Step 1: Divide {max_ab} by {min_ab}: {max_ab} = {q1}*{min_ab} + {r1}.",
                "Step 2: Apply Euclidean step with remainder {r1}: {min_ab} = {q2}*{r1} + {r2}.",
                "Step 3: Continue until remainder is 0: Last non-zero remainder = {gcd_val}.",
                "Step 4: Back-substitute to find Bezout coefficients."
            ],
            "final_answer": "gcd({a}, {b}) = {gcd_val}",
            "wrong_step_options": ["Step 2", "Step 3", "Step 4"],
            "base_complexity": 50,
            "difficulty": "Medium",
            "keywords": ["gcd", "euclidean", "number theory", "remainder", "divisor", "bezout"]
        },
        {
            "problem": "Solve linear congruence: {a}x equivalent to {b} (mod {m})",
            "solution_steps": [
                "Step 1: Check solvability: d = gcd({a}, {m}) must divide {b}.",
                "Step 2: Compute modular inverse of {a}/d modulo {m}/d.",
                "Step 3: Multiply inverse to isolate x modulo {m}/d.",
                "Step 4: Generate all d mutually incongruent solutions modulo {m}."
            ],
            "final_answer": "x = {sol} (mod {m})",
            "wrong_step_options": ["Step 2", "Step 3"],
            "base_complexity": 72,
            "difficulty": "Hard",
            "keywords": ["congruence", "modular", "modulo", "number theory", "gcd", "inverse"]
        }
    ],
    "Linear Algebra": [
        {
            "problem": "Compute the determinant of the 2x2 matrix A = [[{a}, {b}], [{c}, {d}]] and determine if it is invertible.",
            "solution_steps": [
                "Step 1: State 2x2 determinant formula: det(A) = ad - bc.",
                "Step 2: Multiply primary diagonal: {a} * {d} = {ad}.",
                "Step 3: Multiply secondary diagonal: {b} * {c} = {bc}.",
                "Step 4: Subtract terms: det(A) = {ad} - {bc} = {det}.",
                "Step 5: Check invertibility: Since det(A) {invert_phrase}, matrix is {inv_status}."
            ],
            "final_answer": "det(A) = {det}, Matrix is {inv_status}",
            "wrong_step_options": ["Step 2", "Step 3", "Step 4"],
            "base_complexity": 40,
            "difficulty": "Medium",
            "keywords": ["matrix", "determinant", "linear algebra", "invertible", "eigenvalue", "vector"]
        },
        {
            "problem": "Find the eigenvalues of matrix A = [[{a}, 0], [{b}, {c}]].",
            "solution_steps": [
                "Step 1: Form characteristic equation det(A - lambda*I) = 0.",
                "Step 2: Set up matrix: [[{a} - lambda, 0], [{b}, {c} - lambda]].",
                "Step 3: Compute triangular determinant: ({a} - lambda)({c} - lambda) = 0.",
                "Step 4: Solve for roots: lambda1 = {a}, lambda2 = {c}."
            ],
            "final_answer": "Eigenvalues are lambda1 = {a}, lambda2 = {c}",
            "wrong_step_options": ["Step 2", "Step 3"],
            "base_complexity": 76,
            "difficulty": "Hard",
            "keywords": ["eigenvalue", "matrix", "characteristic polynomial", "linear algebra", "determinant"]
        }
    ]
}

# Real-world target topic failure rates (Calculus & Linear Algebra naturally harder)
TOPIC_TARGET_ACCURACY = {
    "Algebra": 0.82,
    "Calculus": 0.62,       # Weakness area for alert demonstration
    "Geometry": 0.78,
    "Probability": 0.68,    # Moderate weakness
    "Statistics": 0.85,
    "Trigonometry": 0.71,
    "Number Theory": 0.74,
    "Linear Algebra": 0.65  # Weakness area
}

RAW_CORRECTNESS_VARIANTS_CORRECT = ["correct", "Correct", "CORRECT", "true", "True", "TRUE", "yes", "YES", "1", "1.0"]
RAW_CORRECTNESS_VARIANTS_INCORRECT = ["incorrect", "Incorrect", "INCORRECT", "false", "False", "FALSE", "no", "NO", "0", "0.0"]

FEEDBACK_COMMENTS_CORRECT = [
    "Solution was concise and completely accurate.",
    "Very clear explanation and all intermediate steps shown.",
    "Great step-by-step breakdown!",
    "Correct final answer, easy to follow.",
    "Helped me understand the underlying formula.",
    "Perfect explanation!"
]

FEEDBACK_COMMENTS_INCORRECT = [
    "Missed negative sign during algebraic substitution in intermediate step.",
    "The step calculation has an arithmetic error.",
    "Skipped explaining the chain rule step.",
    "The formula application in the middle was flawed.",
    "Final answer does not match algebraic simplification.",
    "Denominator integration was handled incorrectly.",
    "Did not explain why this identity was substituted.",
    "Wrong calculation of determinant subtraction."
]


def generate_single_record(record_index, start_time, end_time):
    topic = random.choices(
        list(TOPIC_TEMPLATES.keys()),
        weights=[0.20, 0.18, 0.12, 0.10, 0.12, 0.10, 0.08, 0.10],
        k=1
    )[0]
    
    template = random.choice(TOPIC_TEMPLATES[topic])
    
    # Generate random parameters
    a = random.randint(1, 9)
    b = random.randint(1, 9)
    c = random.randint(1, 9)
    d = random.randint(1, 9)
    e = random.randint(1, 9)
    f = random.randint(1, 9)
    r = random.randint(2, 15)
    h = random.randint(5, 25)
    angle = random.choice([30, 45, 60, 90, 120])
    red = random.randint(3, 10)
    blue = random.randint(3, 10)
    pa = round(random.uniform(0.1, 0.9), 2)
    pba = round(random.uniform(0.1, 0.9), 2)
    pb_not_a = round(random.uniform(0.1, 0.9), 2)
    
    disc = b**2 - 4*a*c
    sqrt_disc = abs(disc)**0.5
    x1 = (-b + sqrt_disc) / (2*a)
    x2 = (-b - sqrt_disc) / (2*a)
    
    y_val = 2.5
    x_val = 3.0
    a4 = a / 4.0
    b_c = b / max(c, 1)
    two_a = 2 * a
    ratio = a / max(b, 1)
    
    base_area = 3.1416 * (r**2)
    lat_area = 2 * 3.1416 * r * h
    tot_area = 2 * base_area + lat_area
    vol = base_area * h
    
    cos_val = 0.5
    sum_sq = a**2 + b**2
    sub_term = 2 * a * b * cos_val
    c_sq = max(1.0, sum_sq - sub_term)
    c_val = c_sq**0.5
    
    tot_balls = red + blue
    red_minus_1 = max(1, red - 1)
    tot_minus_1 = max(1, tot_balls - 1)
    prob = (red / tot_balls) * (red_minus_1 / tot_minus_1)
    
    p_not_a = 1.0 - pa
    pb = (pba * pa) + (pb_not_a * p_not_a)
    p_joint = pba * pa
    p_post = p_joint / max(0.0001, pb)
    
    dataset_vals = [random.randint(10, 90) for _ in range(5)]
    dataset_str = ", ".join(map(str, dataset_vals))
    n = len(dataset_vals)
    sum_x = sum(dataset_vals)
    mean_x = sum_x / n
    sum_sq_dev = sum((v - mean_x)**2 for v in dataset_vals)
    var_x = sum_sq_dev / max(1, n - 1)
    std_x = var_x**0.5
    
    mu = random.randint(50, 100)
    sigma = random.randint(5, 15)
    x_val_stat = mu + random.randint(-20, 20)
    diff = x_val_stat - mu
    z_score = diff / sigma
    
    sin_ratio = min(1.0, b / max(a, 1))
    angles_str = "0, pi, 0.52 rad, 2.62 rad"
    
    max_ab = max(a*12, b*8)
    min_ab = max(1, min(a*12, b*8))
    q1 = max_ab // min_ab
    r1 = max_ab % min_ab
    q2 = 1
    r2 = 0
    gcd_val = max(1, r1 if r1 > 0 else min_ab)
    sol = (b * 2) % max(3, a)
    
    ad = a * d
    bc = b * c
    det = ad - bc
    invert_phrase = "!= 0" if det != 0 else "= 0"
    inv_status = "Invertible" if det != 0 else "Singular"
    
    context = {
        "a": a, "b": b, "c": c, "d": d, "e": e, "f": f,
        "r": r, "h": h, "angle": angle, "red": red, "blue": blue,
        "pa": pa, "pba": pba, "pb_not_a": pb_not_a,
        "disc": disc, "sqrt_disc": sqrt_disc, "x1": x1, "x2": x2,
        "x_val": x_val, "y_val": y_val, "a4": a4, "b_c": b_c, "two_a": two_a, "ratio": ratio,
        "base_area": base_area, "lat_area": lat_area, "tot_area": tot_area, "vol": vol,
        "cos_val": cos_val, "sum_sq": sum_sq, "sub_term": sub_term, "c_sq": c_sq, "c_val": c_val,
        "tot_balls": tot_balls, "red_minus_1": red_minus_1, "tot_minus_1": tot_minus_1, "prob": prob,
        "p_not_a": p_not_a, "pb": pb, "p_joint": p_joint, "p_post": p_post,
        "dataset_str": dataset_str, "n": n, "sum_x": sum_x, "mean_x": mean_x,
        "sum_sq_dev": sum_sq_dev, "var_x": var_x, "std_x": std_x,
        "mu": mu, "sigma": sigma, "x_val_stat": x_val_stat, "diff": diff, "z_score": z_score,
        "sin_ratio": sin_ratio, "angles_str": angles_str,
        "max_ab": max_ab, "min_ab": min_ab, "q1": q1, "r1": r1, "q2": q2, "r2": r2, "gcd_val": gcd_val, "m": max(5, a+b), "sol": sol,
        "ad": ad, "bc": bc, "det": det, "invert_phrase": invert_phrase, "inv_status": inv_status
    }
    
    # Format problem and solution
    problem_text = template["problem"].format(**context)
    rendered_steps = [s.format(**context) for s in template["solution_steps"]]
    solution_text = "\n".join(rendered_steps) + f"\n\nFinal Answer: {template['final_answer'].format(**context)}"
    
    # Determine correctness based on topic target accuracy
    is_correct = random.random() < TOPIC_TARGET_ACCURACY[topic]
    
    if is_correct:
        raw_correctness = random.choice(RAW_CORRECTNESS_VARIANTS_CORRECT)
        wrong_step = ""
        feedback_text = random.choice(FEEDBACK_COMMENTS_CORRECT) if random.random() < 0.65 else ""
    else:
        raw_correctness = random.choice(RAW_CORRECTNESS_VARIANTS_INCORRECT)
        wrong_step = random.choice(template["wrong_step_options"])
        feedback_text = random.choice(FEEDBACK_COMMENTS_INCORRECT)
        
    # Timestamp over last 60 days
    delta_seconds = random.randint(0, int((end_time - start_time).total_seconds()))
    timestamp = start_time + timedelta(seconds=delta_seconds)
    
    # Generate UUIDs
    problem_id = f"prob_{record_index:06d}_{uuid.uuid4().hex[:8]}"
    user_id = f"user_{random.randint(100, 999)}"
    
    return {
        "problem_id": problem_id,
        "user_id": user_id,
        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "problem_text": problem_text,
        "generated_solution": solution_text,
        "correctness": raw_correctness,
        "feedback": feedback_text,
        "wrong_step": wrong_step
    }


def generate_dataset(num_records=12000, output_dir="data/raw"):
    os.makedirs(output_dir, exist_ok=True)
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=60)
    
    print(f"[*] Generating {num_records:,} realistic mathematical records...")
    records = []
    
    for i in range(1, num_records + 1):
        record = generate_single_record(i, start_time, end_time)
        records.append(record)
        
        # Inject ~0.5% intentionally dirty/duplicate records to demonstrate PySpark data cleaning capabilities
        if i % 200 == 0:
            duplicate_record = record.copy()
            records.append(duplicate_record)
        elif i % 500 == 0:
            dirty_record = record.copy()
            dirty_record["problem_id"] = f"prob_dirty_{i}"
            dirty_record["problem_text"] = "   "  # whitespace to be cleaned
            dirty_record["correctness"] = "unknown_null"
            records.append(dirty_record)
            
    # Save as JSON and CSV
    json_path = os.path.join(output_dir, "raw_problems.json")
    csv_path = os.path.join(output_dir, "raw_problems.csv")
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
        
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
        
    print(f"[+] Successfully saved {len(records):,} records to:")
    print(f"    - JSON: {json_path}")
    print(f"    - CSV:  {csv_path}")
    return json_path, csv_path


if __name__ == "__main__":
    generate_dataset(num_records=12000)
