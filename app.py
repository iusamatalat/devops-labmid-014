import sqlite3
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, g, redirect, render_template, request, url_for


FIELDS = {
    "student_name": "Student name",
    "registration_number": "Registration number",
    "assignment_title": "Assignment title",
    "submission_url": "Submission URL",
}


def validate_submission(data):
    """Return an error message, or an empty string when the data is valid."""
    for field, label in FIELDS.items():
        if not data[field]:
            return f"{label} is required."

    url = data["submission_url"]
    try:
        parts = urlsplit(url)
        valid_url = (
            parts.scheme in ("http", "https")
            and bool(parts.hostname)
            and not any(character.isspace() for character in url)
            and "\\" not in url
        )
        # Reading .port also rejects malformed or out-of-range ports.
        parts.port
    except ValueError:
        valid_url = False

    if not valid_url:
        return "Enter a valid http:// or https:// submission URL."
    return ""


def create_app(database_path=None):
    app = Flask(__name__)
    app.config["DATABASE"] = str(
        database_path or Path(__file__).with_name("submissions.db")
    )

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(error):
        database = g.pop("db", None)
        if database is not None:
            database.close()

    with app.app_context():
        database = get_db()
        database.execute(
            """CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY,
                student_name TEXT NOT NULL,
                registration_number TEXT NOT NULL,
                assignment_title TEXT NOT NULL,
                submission_url TEXT NOT NULL
            )"""
        )
        database.commit()

    @app.route("/", methods=["GET", "POST"])
    def index():
        data = {field: "" for field in FIELDS}
        error = ""

        if request.method == "POST":
            data = {
                field: request.form.get(field, "").strip()
                for field in FIELDS
            }
            error = validate_submission(data)
            if not error:
                database = get_db()
                database.execute(
                    """INSERT INTO submissions
                    (student_name, registration_number, assignment_title, submission_url)
                    VALUES (?, ?, ?, ?)""",
                    tuple(data[field] for field in FIELDS),
                )
                database.commit()
                return redirect(url_for("index", saved="1"))

        submissions = get_db().execute(
            "SELECT * FROM submissions ORDER BY id DESC"
        ).fetchall()
        return render_template(
            "index.html",
            data=data,
            error=error,
            saved=request.method == "GET" and request.args.get("saved") == "1",
            submissions=submissions,
        ), 400 if error else 200

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000)
