import os
from datetime import datetime, timedelta

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

from analysis import analyze_text, MOOD_VALUES

# --------------------------------------------------------------------------
# App / Config
# --------------------------------------------------------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

database_url = os.environ.get("DATABASE_URL", "")
if database_url.startswith("postgres://"):
    # Render provides postgres:// but SQLAlchemy needs postgresql://
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///" + os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "database", "mindcare.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "database"), exist_ok=True)

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"


# --------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    entries = db.relationship("MoodEntry", backref="user", lazy=True,
                               order_by="desc(MoodEntry.created_at)")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class MoodEntry(db.Model):
    __tablename__ = "mood_entries"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    mood = db.Column(db.String(20), nullable=False)
    mood_score = db.Column(db.Integer, nullable=False)
    journal_text = db.Column(db.Text, nullable=True)
    sentiment = db.Column(db.String(20), nullable=False)
    emotion_signal = db.Column(db.String(60), nullable=False)
    support_message = db.Column(db.Text, nullable=False)
    distress_flag = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()


# --------------------------------------------------------------------------
# Auth routes
# --------------------------------------------------------------------------
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Please fill in all fields.", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
            return render_template("register.html")

        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Welcome to MindCare! Your account has been created.", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


# --------------------------------------------------------------------------
# Core app routes
# --------------------------------------------------------------------------
@app.route("/checkin", methods=["GET", "POST"])
@login_required
def checkin():
    if request.method == "POST":
        mood = request.form.get("mood")
        journal_text = request.form.get("journal_text", "").strip()

        if mood not in MOOD_VALUES:
            flash("Please select a mood.", "error")
            return render_template("checkin.html")

        result = analyze_text(journal_text)

        entry = MoodEntry(
            user_id=current_user.id,
            mood=mood,
            mood_score=MOOD_VALUES[mood],
            journal_text=journal_text,
            sentiment=result["sentiment"],
            emotion_signal=result["emotion_signal"],
            support_message=result["support_message"],
            distress_flag=result["distress_flag"],
        )
        db.session.add(entry)
        db.session.commit()

        return redirect(url_for("result", entry_id=entry.id))

    return render_template("checkin.html", mood_values=MOOD_VALUES)


@app.route("/result/<int:entry_id>")
@login_required
def result(entry_id):
    entry = MoodEntry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    return render_template("result.html", entry=entry)


@app.route("/dashboard")
@login_required
def dashboard():
    recent_entries = (
        MoodEntry.query.filter_by(user_id=current_user.id)
        .order_by(MoodEntry.created_at.desc())
        .limit(5)
        .all()
    )
    total_entries = MoodEntry.query.filter_by(user_id=current_user.id).count()

    week_ago = datetime.utcnow() - timedelta(days=7)
    week_entries = MoodEntry.query.filter(
        MoodEntry.user_id == current_user.id,
        MoodEntry.created_at >= week_ago,
    ).count()

    latest = recent_entries[0] if recent_entries else None

    return render_template(
        "dashboard.html",
        recent_entries=recent_entries,
        total_entries=total_entries,
        week_entries=week_entries,
        latest=latest,
    )


@app.route("/history")
@login_required
def history():
    entries = (
        MoodEntry.query.filter_by(user_id=current_user.id)
        .order_by(MoodEntry.created_at.desc())
        .all()
    )
    return render_template("history.html", entries=entries)


@app.route("/support")
def support():
    return render_template("support.html")


# --------------------------------------------------------------------------
# JSON API for dashboard charts
# --------------------------------------------------------------------------
@app.route("/api/mood-data")
@login_required
def mood_data():
    entries = (
        MoodEntry.query.filter_by(user_id=current_user.id)
        .order_by(MoodEntry.created_at.asc())
        .limit(30)
        .all()
    )

    trend = [
        {"date": e.created_at.strftime("%b %d"), "score": e.mood_score}
        for e in entries
    ]

    distribution = {"Positive": 0, "Neutral": 0, "Negative": 0}
    for e in entries:
        if e.sentiment in distribution:
            distribution[e.sentiment] += 1

    return jsonify({"trend": trend, "distribution": distribution})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
