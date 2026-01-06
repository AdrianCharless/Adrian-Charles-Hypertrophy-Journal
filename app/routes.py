from flask import Blueprint, render_template, request, redirect, url_for
from datetime import date

from .db import get_db

main = Blueprint("main", __name__)

DAY_TYPES = [
    ("CHEST_TRICEP", "Chest & Tricep"),
    ("BACK_BICEP", "Back & Bicep"),
    ("SHOULDERS_ABS", "Shoulders & Abs"),
    ("LEG_DAY", "Leg Day"),
]

@main.get("/")
def home():
    return render_template("home.html", day_types=DAY_TYPES)

@main.get("/workout/start")
def start_workout():
    day_type = request.args.get("day_type")
    if not day_type:
        return "Missing day_type", 400

    today = date.today().isoformat()
    db = get_db()

    # ALWAYS define last_workout first
    last_workout = db.execute(
        """
        SELECT id, date
        FROM workouts
        WHERE day_type = ?
        ORDER BY date DESC
        LIMIT 1
        """,
        (day_type,),
    ).fetchone()

    last_sets = []
    if last_workout is not None:
        last_sets = db.execute(
            """
            SELECT e.name AS exercise_name, s.set_number, s.reps, s.weight
            FROM sets s
            JOIN exercises e ON e.id = s.exercise_id
            WHERE s.workout_id = ?
            ORDER BY e.name, s.set_number
            """,
            (last_workout["id"],),
        ).fetchall()

    day_label = dict(DAY_TYPES).get(day_type, day_type)

    return render_template(
        "workout.html",
        day_type=day_type,
        day_label=day_label,
        today=today,
        last_workout=last_workout,
        last_sets=last_sets,
    )

@main.get("/history/<workout_type>")
def history_day(workout_type):
    db = get_db()

    workouts = db.execute(
        """
        SELECT id, date
        FROM workouts
        WHERE day_type = ?
        ORDER BY date DESC
        """,
        (workout_type,),
    ).fetchall()

    day_label = dict(DAY_TYPES).get(workout_type, workout_type)

    return render_template(
        "history_day.html",
        day_type=workout_type,
        day_label=day_label,
        workouts=workouts,
    )

@main.get("/workout/<int:workout_id>")
def workout_detail(workout_id: int):
    db = get_db()

    workout = db.execute(
        "SELECT id, date, day_type FROM workouts WHERE id = ?",
        (workout_id,),
    ).fetchone()

    if workout is None:
        return "Workout not found", 404
    
    sets_rows = db.execute(
        """
        SELECT e.name AS exercise_name, s.set_number, s.reps, s.weight
        FROM sets s
        JOIN exercises e ON e.id = s.exercise_id
        WHERE s.workout_id = ?
        ORDER BY e.name, s.set_number
        """,
        (workout_id,),
    ).fetchall()

    day_label = dict(DAY_TYPES).get(workout["day_type"], workout["day_type"])

    return render_template(
        "workout_detail.html",
        workout=workout,
        day_label=day_label,
        sets=sets_rows,
    )

@main.post("/workout/save")
def save_workout():
    db = get_db()

    workout_type = request.form.get("day_type")
    workout_date = request.form.get("date") or date.today().isoformat()

    if not workout_type:
        return "Missing workout_type", 400
    
    cur = db.execute(
        "INSERT INTO workouts (date, day_type) VALUES (?, ?)",
        (workout_date, workout_type),
    )
    workout_id = cur.lastrowid

    exercise_names = request.form.getlist("exercise_name")
    set_numbers = request.form.getlist("set_number")
    reps_list = request.form.getlist("reps")
    weights = request.form.getlist("weight")

    if not (len(exercise_names) == len(set_numbers) == len(reps_list) == len(weights)):
        return "Form data mismatch", 400
    
    for ex_name, set_no, reps, weight in zip(exercise_names, set_numbers, reps_list, weights):
        ex_name = (ex_name or "").strip()
        if not ex_name:
            continue  # skip empty rows

        # Upsert exercise by name
        row = db.execute("SELECT id FROM exercises WHERE name = ?", (ex_name,)).fetchone()
        if row:
            exercise_id = row["id"]
        else:
            ex_cur = db.execute("INSERT INTO exercises (name) VALUES (?)", (ex_name,))
            exercise_id = ex_cur.lastrowid

        # Insert set
        db.execute(
            """
            INSERT INTO sets (workout_id, exercise_id, set_number, reps, weight)
            VALUES (?, ?, ?, ?, ?)
            """,
            (workout_id, exercise_id, int(set_no), int(reps), float(weight)),
        )

    db.commit()

    # Redirect back to start page so it becomes “Last time”
    return redirect(url_for("main.start_workout", day_type=workout_type))