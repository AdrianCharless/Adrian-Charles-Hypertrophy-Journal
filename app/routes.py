from flask import Blueprint, render_template, request
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
    """
    Shows:
        - last logs for this day type
        - a place to start new logs for workout
    """
    workout_day = request.arg.get("day_type")
    if not workout_day:
        return "Missing day_type", 400
    
    # get current day
    today = date.today().isoformat()
    db = get_db()

    last_workout = db.execute(
        """
        SELECT id, date
        FROM workouts
        WHERE day_type = ?
        ORDER BY date DESC
        LIMIT 1
        """,(last_workout,),
    ).fetchone()

    last_sets = []
    if last_workout:
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
    
    day_label = dict(DAY_TYPES).get(last_workout, last_workout)

    return render_template(
        "workout.html",
        day_type=workout_day,
        day_label=day_label,
        today=today,
        last_workout=last_workout,
        last_sets=last_sets,
    )

