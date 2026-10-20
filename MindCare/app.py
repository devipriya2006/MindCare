import os
from datetime import datetime, timedelta

from flask import (
    Flask, render_template, redirect, url_for,
    request, flash, jsonify
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user,
    login_required, logout_user, current_user
)
from werkzeug.security import (
    generate_password_hash, check_password_hash
)

from analysis import analyze_text, MOOD_VALUES
from face_emotion import analyze_face


# --------------------------------------------------------------------------
# APP / CONFIG
# --------------------------------------------------------------------------

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "dev-secret-change-me"
)

database_url = os.environ.get("DATABASE_URL", "")

# Configure PostgreSQL using the installed psycopg driver.
if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://", "postgresql+psycopg://", 1
    )
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace(
        "postgresql://", "postgresql+psycopg://", 1
    )

database_folder = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "database"
)
os.makedirs(database_folder, exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    database_url
    or "sqlite:///" + os.path.join(database_folder, "mindcare.db")
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"


# --------------------------------------------------------------------------
# WELLNESS SCORE CALCULATION
# --------------------------------------------------------------------------

def calculate_wellness(
    mood, energy, sleep, stress, connection, sentiment
):
    mood_scores = {
        "great": 100,
        "good": 80,
        "okay": 60,
        "low": 35,
        "angry": 35,
        "stressed": 25,
    }

    energy_scores = {
        "high": 100,
        "moderate": 75,
        "low": 45,
        "very_low": 25,
    }

    sleep_scores = {
        "good": 100,
        "okay": 70,
        "poor": 40,
        "very_poor": 20,
    }

    stress_scores = {
        "low": 100,
        "moderate": 70,
        "high": 40,
        "very_high": 20,
    }

    connection_scores = {
        "connected": 100,
        "somewhat": 70,
        "alone": 40,
        "very_alone": 20,
    }

    sentiment_scores = {
        "positive": 100,
        "neutral": 60,
        "negative": 30,
    }

    score = round(
        mood_scores[mood] * 0.30
        + energy_scores[energy] * 0.15
        + sleep_scores[sleep] * 0.15
        + stress_scores[stress] * 0.20
        + connection_scores[connection] * 0.10
        + sentiment_scores.get(
            str(sentiment).lower(), 60
        ) * 0.10
    )

    if score >= 75:
        level = "Positive"
        insight = (
            "Your answers indicate generally positive wellness signals. "
            "Keep supporting your sleep, energy, and social connections."
        )
    elif score >= 50:
        level = "Balanced"
        insight = (
            "Your answers indicate mixed wellness signals. "
            "Notice which areas could use extra care."
        )
    elif score >= 30:
        level = "Needs Attention"
        insight = (
            "Some answers suggest you may benefit from rest, support, "
            "or a small change to your routine."
        )
    else:
        level = "Low Wellness Signals"
        insight = (
            "Several areas may need attention. Consider reaching out "
            "to someone you trust for support."
        )

    return {
        "wellness_score": score,
        "wellness_level": level,
        "wellness_insight": insight,
    }


# --------------------------------------------------------------------------
# DATABASE MODELS
# --------------------------------------------------------------------------

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow
    )

    entries = db.relationship(
        "MoodEntry",
        backref="user",
        lazy=True,
        order_by="desc(MoodEntry.created_at)",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class MoodEntry(db.Model):
    __tablename__ = "mood_entries"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
    )

    # Check-in source and optional facial-expression analysis
    checkin_type = db.Column(db.String(20), nullable=True, default="manual")
    detected_expression = db.Column(db.String(30), nullable=True)
    expression_confidence = db.Column(db.Float, nullable=True)
    confirmed_expression = db.Column(db.String(30), nullable=True)

    # Main mood
    mood = db.Column(db.String(20), nullable=False)
    mood_score = db.Column(db.Integer, nullable=False)

    # Smart check-in answers
    energy = db.Column(db.String(20), nullable=True)
    sleep = db.Column(db.String(20), nullable=True)
    stress = db.Column(db.String(20), nullable=True)
    connection = db.Column(db.String(20), nullable=True)

    # Journal and text analysis
    journal_text = db.Column(db.Text, nullable=True)
    sentiment = db.Column(db.String(20), nullable=False)
    emotion_signal = db.Column(db.String(60), nullable=False)
    support_message = db.Column(db.Text, nullable=False)
    distress_flag = db.Column(
        db.Boolean, default=False, nullable=True
    )

    # Wellness calculation
    wellness_score = db.Column(db.Integer, nullable=True)
    wellness_level = db.Column(db.String(30), nullable=True)
    wellness_insight = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime, default=datetime.utcnow
    )


# --------------------------------------------------------------------------
# LOGIN MANAGER
# --------------------------------------------------------------------------

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Creates missing tables, but does not migrate existing tables.
with app.app_context():
    db.create_all()


# --------------------------------------------------------------------------
# HOME
# --------------------------------------------------------------------------

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    return render_template("index.html")


# --------------------------------------------------------------------------
# REGISTER
# --------------------------------------------------------------------------

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
            flash(
                "Password must be at least 6 characters.",
                "error",
            )
            return render_template("register.html")

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash(
                "An account with that email already exists.",
                "error",
            )
            return render_template("register.html")

        user = User(name=name, email=email)
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            app.logger.exception("Registration failed")
            flash("Could not create your account. Please try again.", "error")
            return render_template("register.html")

        login_user(user)
        flash(
            "Welcome to MindCare! Your account has been created.",
            "success",
        )
        return redirect(url_for("dashboard"))

    return render_template("register.html")


# --------------------------------------------------------------------------
# LOGIN
# --------------------------------------------------------------------------

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


# --------------------------------------------------------------------------
# LOGOUT
# --------------------------------------------------------------------------

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


# --------------------------------------------------------------------------
# SMART MOOD CHECK-IN
# --------------------------------------------------------------------------

@app.route("/checkin", methods=["GET", "POST"])
@login_required
def checkin():
    if request.method == "POST":
        # Read every answer submitted by the HTML form.
        mood = request.form.get("mood", "").strip().lower()
        energy = request.form.get("energy", "").strip().lower()
        sleep = request.form.get("sleep", "").strip().lower()
        stress = request.form.get("stress", "").strip().lower()
        connection = request.form.get("connection", "").strip().lower()
        journal_text = request.form.get("journal_text", "").strip()

        # Allowed values must match the check-in form.
        allowed_answers = {
            "energy": {"high", "moderate", "low", "very_low"},
            "sleep": {"good", "okay", "poor", "very_poor"},
            "stress": {"low", "moderate", "high", "very_high"},
            "connection": {
                "connected", "somewhat", "alone", "very_alone"
            },
        }

        if mood not in MOOD_VALUES:
            flash("Please select a valid mood.", "error")
            return render_template(
                "checkin.html", mood_values=MOOD_VALUES
            )

        submitted_answers = {
            "energy": energy,
            "sleep": sleep,
            "stress": stress,
            "connection": connection,
        }

        for field, valid_values in allowed_answers.items():
            if submitted_answers[field] not in valid_values:
                flash(
                    f"Please select a valid answer for {field}.",
                    "error",
                )
                return render_template(
                    "checkin.html", mood_values=MOOD_VALUES
                )

        # Analyze journal text.
        result = analyze_text(journal_text)

        # Calculate wellness from all check-in answers.
        wellness = calculate_wellness(
            mood=mood,
            energy=energy,
            sleep=sleep,
            stress=stress,
            connection=connection,
            sentiment=result["sentiment"],
        )

        # Save all answers and calculated results.
        entry = MoodEntry(
            user_id=current_user.id,
            checkin_type="manual",
            mood=mood,
            mood_score=MOOD_VALUES[mood],
            energy=energy,
            sleep=sleep,
            stress=stress,
            connection=connection,
            journal_text=journal_text,
            sentiment=result["sentiment"],
            emotion_signal=result["emotion_signal"],
            support_message=result["support_message"],
            distress_flag=result["distress_flag"],
            wellness_score=wellness["wellness_score"],
            wellness_level=wellness["wellness_level"],
            wellness_insight=wellness["wellness_insight"],
        )

        try:
            db.session.add(entry)
            db.session.commit()
        except Exception:
            db.session.rollback()
            app.logger.exception("Failed to save mood check-in")
            flash(
                "Could not save your check-in. Please try again.",
                "error",
            )
            return render_template(
                "checkin.html", mood_values=MOOD_VALUES
            )

        return redirect(url_for("result", entry_id=entry.id))

    return render_template(
        "checkin.html",
        mood_values=MOOD_VALUES,
    )




# --------------------------------------------------------------------------
# AUTOMATIC FACIAL-EXPRESSION CHECK-IN
# --------------------------------------------------------------------------

@app.route("/automatic-checkin")
@login_required
def automatic_checkin():
    return render_template("automatic_checkin.html")


@app.route("/api/analyze-face", methods=["POST"])
@login_required
def analyze_face_api():
    image = request.files.get("image")
    if image is None or not image.filename:
        return jsonify({
            "success": False,
            "error": "Please capture an image first.",
        }), 400

    image_bytes = image.read()
    if not image_bytes:
        return jsonify({
            "success": False,
            "error": "The captured image was empty. Please try again.",
        }), 400

    # Keep uploads small and do not save them to permanent storage.
    if len(image_bytes) > 5 * 1024 * 1024:
        return jsonify({
            "success": False,
            "error": "The image is too large. Please try again.",
        }), 413

    try:
        result = analyze_face(image_bytes)
        return jsonify({
            "success": True,
            "expression": result["expression"],
            "confidence": result["confidence"],
        })
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except RuntimeError:
        app.logger.exception("Facial-expression analysis failed")
        return jsonify({
            "success": False,
            "error": "The AI could not analyze this image. Please try again.",
        }), 500


@app.route("/automatic-checkin/save", methods=["POST"])
@login_required
def save_automatic_checkin():
    detected_expression = request.form.get(
        "detected_expression", ""
    ).strip().lower()
    confirmed_expression = request.form.get(
        "confirmed_expression", ""
    ).strip().lower()
    confidence_raw = request.form.get("expression_confidence", "").strip()

    allowed_expressions = {
        "angry", "disgust", "fear", "happy",
        "sad", "surprise", "neutral",
    }

    if (
        detected_expression not in allowed_expressions
        or confirmed_expression not in allowed_expressions
    ):
        flash("Please analyze and confirm a valid facial expression.", "error")
        return redirect(url_for("automatic_checkin"))

    try:
        confidence = float(confidence_raw)
        if not 0 <= confidence <= 100:
            raise ValueError
    except (TypeError, ValueError):
        flash("The expression confidence was invalid. Please try again.", "error")
        return redirect(url_for("automatic_checkin"))

    # Existing schema requires mood and mood_score. Store the confirmed
    # expression there for compatibility, and also keep explicit expression
    # fields so analytics can separate face results from self-reported moods.
    fallback_score = 60
    entry = MoodEntry(
        user_id=current_user.id,
        checkin_type="automatic",
        mood=confirmed_expression,
        mood_score=MOOD_VALUES.get(confirmed_expression, fallback_score),
        energy=None,
        sleep=None,
        stress=None,
        connection=None,
        journal_text=None,
        sentiment="Neutral",
        emotion_signal=f"Facial expression estimate: {confirmed_expression}",
        support_message=(
            "This is an estimate of a visible facial expression, not a diagnosis "
            "or proof of how you feel. You can use the manual check-in to record "
            "your own experience."
        ),
        distress_flag=False,
        wellness_score=None,
        wellness_level=None,
        wellness_insight=None,
        detected_expression=detected_expression,
        expression_confidence=confidence,
        confirmed_expression=confirmed_expression,
    )

    try:
        db.session.add(entry)
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception("Failed to save automatic check-in")
        flash(
            "Could not save the automatic check-in. Please try again.",
            "error",
        )
        return redirect(url_for("automatic_checkin"))

    flash("Your confirmed expression was saved to history.", "success")
    return redirect(url_for("history"))


# --------------------------------------------------------------------------
# RESULT
# --------------------------------------------------------------------------

@app.route("/result/<int:entry_id>")
@login_required
def result(entry_id):
    entry = MoodEntry.query.filter_by(
        id=entry_id,
        user_id=current_user.id,
    ).first_or_404()

    return render_template("result.html", entry=entry)


# --------------------------------------------------------------------------
# DASHBOARD
# --------------------------------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():
    user_entries = MoodEntry.query.filter_by(
        user_id=current_user.id
    )

    recent_entries = (
        user_entries
        .order_by(MoodEntry.created_at.desc())
        .limit(5)
        .all()
    )

    total_entries = user_entries.count()

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


# --------------------------------------------------------------------------
# HISTORY
# --------------------------------------------------------------------------

@app.route("/history")
@login_required
def history():
    entries = (
        MoodEntry.query
        .filter_by(user_id=current_user.id)
        .order_by(MoodEntry.created_at.desc())
        .all()
    )

    return render_template("history.html", entries=entries)


# --------------------------------------------------------------------------
# SUPPORT / RESOURCES
# --------------------------------------------------------------------------

@app.route("/support")
def support():
    return render_template("support.html")


# --------------------------------------------------------------------------
# JSON API FOR DASHBOARD CHARTS
# --------------------------------------------------------------------------

@app.route("/api/mood-data")
@login_required
def mood_data():
    entries = (
        MoodEntry.query
        .filter_by(user_id=current_user.id)
        .order_by(MoodEntry.created_at.asc())
        .limit(30)
        .all()
    )

    trend = [
        {
            "date": (
                entry.created_at.strftime("%b %d")
                if entry.created_at else ""
            ),
            "score": entry.mood_score,
            "wellness_score": entry.wellness_score,
            "wellness_level": entry.wellness_level,
        }
        for entry in entries
    ]

    distribution = {
        "Positive": 0,
        "Neutral": 0,
        "Negative": 0,
    }

    for entry in entries:
        if entry.sentiment in distribution:
            distribution[entry.sentiment] += 1

    facial_distribution = {
        "angry": 0,
        "disgust": 0,
        "fear": 0,
        "happy": 0,
        "sad": 0,
        "surprise": 0,
        "neutral": 0,
    }
    for entry in entries:
        if entry.checkin_type == "automatic" and entry.confirmed_expression:
            if entry.confirmed_expression in facial_distribution:
                facial_distribution[entry.confirmed_expression] += 1

    return jsonify({
        "trend": trend,
        "distribution": distribution,
        "facial_distribution": facial_distribution,
    })


# --------------------------------------------------------------------------
# RUN APP
# --------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
