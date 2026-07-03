from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
from datetime import date
from itertools import groupby as _groupby

from .db import get_db
from .auth import login_required

main = Blueprint("main", __name__)


def get_user_splits():
    return get_db().execute(
        "SELECT id, name FROM split_days WHERE user_id = ? ORDER BY id",
        (session["user_id"],),
    ).fetchall()


@main.get("/")
@login_required
def home():
    return render_template("home.html", splits=get_user_splits())


@main.post("/split/add")
@login_required
def split_add():
    name = (request.form.get("name") or "").strip()
    if name:
        get_db().execute(
            "INSERT INTO split_days (user_id, name) VALUES (?, ?)",
            (session["user_id"], name),
        )
        get_db().commit()
    return redirect(url_for("main.home"))


@main.get("/workout/start")
@login_required
def start_workout():
    split_id = request.args.get("split_id", type=int)
    if not split_id:
        return "Missing split_id", 400

    db = get_db()
    split = db.execute(
        "SELECT id, name FROM split_days WHERE id = ? AND user_id = ?",
        (split_id, session["user_id"]),
    ).fetchone()
    if split is None:
        return "Not found", 404

    today = date.today().isoformat()

    # Last 5 sets per exercise across all sessions for this split,
    # ordered so the most-recently-done exercises appear first.
    raw_rows = db.execute(
        """
        SELECT exercise_name, weight, reps, set_number, date
        FROM (
            SELECT
                e.name  AS exercise_name,
                s.weight,
                s.reps,
                s.set_number,
                w.date,
                ROW_NUMBER() OVER (
                    PARTITION BY s.exercise_id
                    ORDER BY w.date DESC, s.set_number DESC
                ) AS rn,
                MAX(w.date) OVER (PARTITION BY s.exercise_id) AS last_date
            FROM sets s
            JOIN exercises e ON e.id = s.exercise_id
            JOIN workouts w  ON w.id = s.workout_id
            WHERE w.split_day_id = ? AND w.user_id = ?
        )
        WHERE rn <= 5
        ORDER BY last_date DESC, exercise_name, date DESC, set_number
        """,
        (split_id, session["user_id"]),
    ).fetchall()

    exercise_history = [
        (ex_name, list(rows))
        for ex_name, rows in _groupby(raw_rows, key=lambda r: r["exercise_name"])
    ]

    return render_template(
        "workout.html",
        split=split,
        today=today,
        exercise_history=exercise_history,
    )


@main.post("/workout/save")
@login_required
def save_workout():
    db = get_db()

    split_id = request.form.get("split_id", type=int)
    workout_date = request.form.get("date") or date.today().isoformat()

    if not split_id:
        return "Missing split_id", 400

    split = db.execute(
        "SELECT id, name FROM split_days WHERE id = ? AND user_id = ?",
        (split_id, session["user_id"]),
    ).fetchone()
    if split is None:
        return "Not found", 404

    cur = db.execute(
        "INSERT INTO workouts (date, day_type, user_id, split_day_id) VALUES (?, ?, ?, ?)",
        (workout_date, split["name"], session["user_id"], split_id),
    )
    workout_id = cur.lastrowid

    exercise_names = request.form.getlist("exercise_name")
    set_numbers    = request.form.getlist("set_number")
    reps_list      = request.form.getlist("reps")
    weights        = request.form.getlist("weight")

    if not (len(exercise_names) == len(set_numbers) == len(reps_list) == len(weights)):
        return "Form data mismatch", 400

    for ex_name, set_no, reps, weight in zip(exercise_names, set_numbers, reps_list, weights):
        ex_name = (ex_name or "").strip()
        if not ex_name:
            continue

        row = db.execute("SELECT id FROM exercises WHERE name = ?", (ex_name,)).fetchone()
        if row:
            exercise_id = row["id"]
        else:
            ex_cur = db.execute("INSERT INTO exercises (name) VALUES (?)", (ex_name,))
            exercise_id = ex_cur.lastrowid

        db.execute(
            "INSERT INTO sets (workout_id, exercise_id, set_number, reps, weight) VALUES (?, ?, ?, ?, ?)",
            (workout_id, exercise_id, int(set_no), int(reps), float(weight)),
        )

    db.commit()
    return redirect(url_for("main.start_workout", split_id=split_id))


@main.get("/history/<int:split_id>")
@login_required
def history_day(split_id: int):
    db = get_db()

    split = db.execute(
        "SELECT id, name FROM split_days WHERE id = ? AND user_id = ?",
        (split_id, session["user_id"]),
    ).fetchone()
    if split is None:
        return "Not found", 404

    workouts = db.execute(
        "SELECT id, date FROM workouts WHERE split_day_id = ? AND user_id = ? ORDER BY date DESC",
        (split_id, session["user_id"]),
    ).fetchall()

    return render_template("history_day.html", split=split, workouts=workouts)


@main.get("/workout/<int:workout_id>")
@login_required
def workout_detail(workout_id: int):
    db = get_db()

    workout = db.execute(
        "SELECT id, date, day_type, split_day_id FROM workouts WHERE id = ? AND user_id = ?",
        (workout_id, session["user_id"]),
    ).fetchone()
    if workout is None:
        return "Not found", 404

    split = db.execute(
        "SELECT id, name FROM split_days WHERE id = ?",
        (workout["split_day_id"],),
    ).fetchone()

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

    return render_template(
        "workout_detail.html",
        workout=workout,
        split=split,
        sets=sets_rows,
    )


@main.get("/progress")
@login_required
def progress():
    db = get_db()
    splits = get_user_splits()
    exercises = db.execute(
        """
        SELECT DISTINCT e.id, e.name
        FROM exercises e
        JOIN sets s ON s.exercise_id = e.id
        JOIN workouts w ON w.id = s.workout_id
        WHERE w.user_id = ?
        ORDER BY e.name
        """,
        (session["user_id"],),
    ).fetchall()
    return render_template("progress.html", splits=splits, exercises=exercises)


@main.get("/api/progress")
@login_required
def progress_api():
    db = get_db()
    split_id   = request.args.get("split_id", type=int)
    exercise_id = request.args.get("exercise_id")
    metric      = request.args.get("metric", "top_weight")

    if not exercise_id:
        return jsonify({"error": "Missing exercise_id"}), 400

    params = [int(exercise_id), session["user_id"]]
    split_filter = ""
    if split_id:
        split_filter = " AND w.split_day_id = ? "
        params.append(split_id)

    rows = db.execute(
        f"""
        SELECT
            w.date AS date,
            MAX(s.weight) AS top_weight,
            MAX(s.weight * (1.0 + (s.reps / 30.0))) AS e1rm
        FROM sets s
        JOIN workouts w ON w.id = s.workout_id
        WHERE s.exercise_id = ? AND w.user_id = ?
        {split_filter}
        GROUP BY w.id
        ORDER BY w.date
        """,
        tuple(params),
    ).fetchall()

    key = "top_weight" if metric == "top_weight" else "e1rm"
    return jsonify({
        "dates":  [r["date"] for r in rows],
        "values": [r[key] for r in rows],
        "metric": key,
    })
