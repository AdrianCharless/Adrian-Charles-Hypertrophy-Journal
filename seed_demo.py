"""
Creates a demo account with 10 weeks of Push/Pull/Leg sessions
showing progressive overload. Run from the project root:
    python seed_demo.py
"""
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

DB_PATH = Path("instance/gym_journal.sqlite")
USERNAME = "demo"
PASSWORD = "demo1234"

# ---------------------------------------------------------------------------
# Workout data
# Each exercise entry is a list of 10 (weight, reps) tuples — one per session.
# 3 sets are generated per session; the 3rd set drops 1 rep to simulate fatigue.
# ---------------------------------------------------------------------------

PUSH_EXERCISES = {
    "Bench Press":          [(135,10),(135,12),(140,10),(140,12),(145,10),(145,12),(150,10),(150,10),(155,8),(155,10)],
    "Chest Smith Machine":  [(115,12),(120,10),(120,12),(125,10),(125,12),(130,10),(130,12),(135,10),(135,12),(140,10)],
    "Incline DB Press":     [(60,10), (60,12), (65,10), (65,12), (70,10), (70,12), (75,10), (75,10), (80,8), (80,10)],
    "Shoulder Press":       [(95,10), (95,12), (100,10),(100,12),(105,10),(105,12),(110,8), (110,10),(115,8),(115,10)],
    "Lateral Raises":       [(20,15), (20,15), (25,12), (25,15), (30,12), (30,12), (30,15), (35,12), (35,12),(35,15)],
    "Tricep Pushdown":      [(50,12), (55,10), (55,12), (60,10), (60,12), (65,10), (65,12), (70,10), (70,12),(75,10)],
}

PULL_EXERCISES = {
    "Barbell Row":    [(115,10),(120,8),(120,10),(125,8),(125,10),(130,8),(130,10),(135,8),(135,10),(140,8)],
    "Lat Pulldown":   [(110,12),(115,10),(115,12),(120,10),(120,12),(125,10),(125,12),(130,10),(130,12),(135,10)],
    "Pull Ups":       [(0,5),  (0,6),  (0,7),  (0,8),  (0,8),  (0,9),  (0,9),  (0,10), (10,6), (10,8)],
    "Bicep Curl":     [(35,12),(35,15),(40,12),(40,12),(40,15),(45,12),(45,12),(45,15),(50,10),(50,12)],
    "Face Pulls":     [(40,15),(45,12),(45,15),(50,12),(50,15),(55,12),(55,15),(60,12),(60,12),(60,15)],
}

LEG_EXERCISES = {
    "Squat":                [(155,10),(160,8),(160,10),(165,8),(165,10),(170,8),(170,10),(175,8),(175,8),(180,6)],
    "Leg Press":            [(270,12),(280,10),(280,12),(290,10),(290,12),(300,10),(300,12),(310,10),(310,12),(320,10)],
    "Romanian Deadlift":    [(135,10),(140,8),(140,10),(145,8),(145,10),(150,8),(150,10),(155,8),(155,10),(160,8)],
    "Leg Extension":        [(100,12),(105,12),(110,10),(110,12),(115,10),(115,12),(120,10),(120,12),(125,10),(125,12)],
    "Calf Raises":          [(150,15),(155,15),(160,12),(160,15),(165,12),(165,15),(170,12),(170,15),(175,12),(175,15)],
}

# 10 sessions per split, roughly every 7 days
PUSH_DATES = ["2026-04-01","2026-04-08","2026-04-15","2026-04-22","2026-04-29",
              "2026-05-06","2026-05-13","2026-05-20","2026-05-27","2026-06-03"]
PULL_DATES = ["2026-04-03","2026-04-10","2026-04-17","2026-04-24","2026-05-01",
              "2026-05-08","2026-05-15","2026-05-22","2026-05-29","2026-06-05"]
LEG_DATES  = ["2026-04-05","2026-04-12","2026-04-19","2026-04-26","2026-05-03",
              "2026-05-10","2026-05-17","2026-05-24","2026-05-31","2026-06-07"]

SPLITS = [
    ("Push Day", PUSH_DATES, PUSH_EXERCISES),
    ("Pull Day", PULL_DATES, PULL_EXERCISES),
    ("Leg Day",  LEG_DATES,  LEG_EXERCISES),
]


def seed():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    # ── user ──
    existing = conn.execute("SELECT id FROM users WHERE username = ?", (USERNAME,)).fetchone()
    if existing:
        print(f"User '{USERNAME}' already exists — wiping their data and re-seeding.")
        user_id = existing["id"]
        # Remove their workouts and splits so we start clean
        workout_ids = [r["id"] for r in conn.execute(
            "SELECT id FROM workouts WHERE user_id = ?", (user_id,)).fetchall()]
        for wid in workout_ids:
            conn.execute("DELETE FROM sets WHERE workout_id = ?", (wid,))
        conn.execute("DELETE FROM workouts WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM split_days WHERE user_id = ?", (user_id,))
    else:
        cur = conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (USERNAME, generate_password_hash(PASSWORD, method="pbkdf2:sha256")),
        )
        user_id = cur.lastrowid
        print(f"Created user '{USERNAME}' (id={user_id})")

    # ── exercise cache (exercises are global) ──
    ex_cache = {}

    def get_or_create_exercise(name):
        if name in ex_cache:
            return ex_cache[name]
        row = conn.execute("SELECT id FROM exercises WHERE name = ?", (name,)).fetchone()
        if row:
            ex_cache[name] = row["id"]
        else:
            cur = conn.execute("INSERT INTO exercises (name) VALUES (?)", (name,))
            ex_cache[name] = cur.lastrowid
        return ex_cache[name]

    # ── insert sessions ──
    total_workouts = 0
    for split_name, dates, exercises in SPLITS:
        split_cur = conn.execute(
            "INSERT INTO split_days (user_id, name) VALUES (?, ?)",
            (user_id, split_name),
        )
        split_id = split_cur.lastrowid

        for session_idx, date in enumerate(dates):
            w_cur = conn.execute(
                "INSERT INTO workouts (date, day_type, user_id, split_day_id) VALUES (?, ?, ?, ?)",
                (date, split_name, user_id, split_id),
            )
            workout_id = w_cur.lastrowid
            total_workouts += 1

            for ex_name, progression in exercises.items():
                weight, reps = progression[session_idx]
                ex_id = get_or_create_exercise(ex_name)
                for set_no in range(1, 4):  # 3 sets
                    # slight rep drop on set 3 to simulate fatigue
                    actual_reps = reps if set_no < 3 else max(reps - 1, 1)
                    conn.execute(
                        "INSERT INTO sets (workout_id, exercise_id, set_number, reps, weight) VALUES (?,?,?,?,?)",
                        (workout_id, ex_id, set_no, actual_reps, float(weight)),
                    )

    conn.commit()
    conn.close()

    print(f"Seeded {total_workouts} workouts across 3 splits.")
    print(f"\nLogin: username='{USERNAME}'  password='{PASSWORD}'")


if __name__ == "__main__":
    seed()
