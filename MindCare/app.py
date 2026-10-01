import os

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

from analysis import (
    analyze_text,
    calculate_wellness,
    MOOD_VALUES
)


# ============================================================
# APP CONFIGURATION
# ============================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "mindcare-development-secret-key"
)

database_url = os.environ.get("DATABASE_URL", "")

if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql://",
        1
    )

if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mindcare.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# ============================================================
# USER MODEL
# ============================================================

class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    mood_entries = db.relationship(
        "MoodEntry",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(
            self.password_hash,
            password
        )


# ============================================================
# MOOD ENTRY MODEL
# ============================================================

class MoodEntry(db.Model):

    __tablename__ = "mood_entries"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    mood = db.Column(
        db.String(30),
        nullable=False
    )

    journal_text = db.Column(
        db.Text,
        nullable=True
    )

    sentiment = db.Column(
        db.String(30),
        nullable=True
    )

    emotion_signal = db.Column(
        db.String(50),
        nullable=True
    )

    support_message = db.Column(
        db.Text,
        nullable=True
    )

    distress_flag = db.Column(
        db.Boolean,
        default=False
    )

    # --------------------------------------------------------
    # SMART CHECK-IN FIELDS
    # --------------------------------------------------------

    energy = db.Column(
        db.String(20),
        nullable=True
    )

    sleep = db.Column(
        db.String(20),
        nullable=True
    )

    stress = db.Column(
        db.String(20),
        nullable=True
    )

    connection = db.Column(
        db.String(20),
        nullable=True
    )

    # --------------------------------------------------------
    # WELLNESS ANALYSIS
    # --------------------------------------------------------

    wellness_score = db.Column(
        db.Integer,
        nullable=True
    )

    wellness_level = db.Column(
        db.String(30),
        nullable=True
    )

    wellness_insight = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )


# ============================================================
# LOGIN MANAGER
# ============================================================

@login_manager.user_loader
def load_user(user_id):

    return db.session.get(
        User,
        int(user_id)
    )


# ============================================================
# HOME
# ============================================================

@app.route("/")
def index():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    return render_template("index.html")


# ============================================================
# REGISTER
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not username or not email or not password:
            flash(
                "Please fill in all fields.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        if password != confirm_password:
            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        existing_username = User.query.filter_by(
            username=username
        ).first()

        if existing_username:
            flash(
                "Username already exists.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        existing_email = User.query.filter_by(
            email=email
        ).first()

        if existing_email:
            flash(
                "Email already exists.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        user = User(
            username=username,
            email=email
        )

        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash(
            "Registration successful. Please login.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template("register.html")


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = User.query.filter_by(
            email=email
        ).first()

        if user and user.check_password(password):

            login_user(user)

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid email or password.",
            "danger"
        )

    return render_template("login.html")


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(
        url_for("index")
    )


# ============================================================
# CHECK-IN
# ============================================================

@app.route("/checkin", methods=["GET", "POST"])
@login_required
def checkin():

    if request.method == "POST":

        # ----------------------------------------------------
        # GET ALL CHECK-IN VALUES
        # ----------------------------------------------------

        mood = request.form.get(
            "mood",
            ""
        ).strip().lower()

        energy = request.form.get(
            "energy",
            ""
        ).strip().lower()

        sleep = request.form.get(
            "sleep",
            ""
        ).strip().lower()

        stress = request.form.get(
            "stress",
            ""
        ).strip().lower()

        connection = request.form.get(
            "connection",
            ""
        ).strip().lower()

        journal_text = request.form.get(
            "journal_text",
            ""
        ).strip()

        # ----------------------------------------------------
        # DEBUG
        # ----------------------------------------------------

        print("======================================")
        print("MINDCARE CHECK-IN")
        print("======================================")
        print("Mood       :", mood)
        print("Energy     :", energy)
        print("Sleep      :", sleep)
        print("Stress     :", stress)
        print("Connection :", connection)
        print("Journal    :", journal_text)
        print("======================================")

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not mood:
            flash(
                "Please select your mood.",
                "danger"
            )

            return redirect(
                url_for("checkin")
            )

        if not energy:
            flash(
                "Please select your energy level.",
                "danger"
            )

            return redirect(
                url_for("checkin")
            )

        if not sleep:
            flash(
                "Please select your sleep quality.",
                "danger"
            )

            return redirect(
                url_for("checkin")
            )

        if not stress:
            flash(
                "Please select your stress level.",
                "danger"
            )

            return redirect(
                url_for("checkin")
            )

        if not connection:
            flash(
                "Please select your connection level.",
                "danger"
            )

            return redirect(
                url_for("checkin")
            )

        # ----------------------------------------------------
        # JOURNAL / TEXT ANALYSIS
        # ----------------------------------------------------

        result = analyze_text(
            journal_text
        )

        print("TEXT SENTIMENT:", result["sentiment"])
        print("EMOTION SIGNAL:", result["emotion_signal"])
        print("DISTRESS FLAG:", result["distress_flag"])

        # ----------------------------------------------------
        # COMBINED WELLNESS CALCULATION
        #
        # IMPORTANT:
        # This uses ALL 6 inputs:
        #
        # Mood       = 30%
        # Energy     = 15%
        # Sleep      = 15%
        # Stress     = 20%
        # Connection = 10%
        # Journal    = 10%
        # ----------------------------------------------------

        wellness = calculate_wellness(
            mood=mood,
            energy=energy,
            sleep=sleep,
            stress=stress,
            connection=connection,
            sentiment=result["sentiment"]
        )

        wellness_score = wellness["wellness_score"]
        wellness_level = wellness["wellness_level"]
        wellness_insight = wellness["wellness_insight"]

        print("======================================")
        print("WELLNESS CALCULATION")
        print("======================================")
        print("Wellness Score :", wellness_score)
        print("Wellness Level :", wellness_level)
        print("Wellness Insight:", wellness_insight)
        print("======================================")

        # ----------------------------------------------------
        # SAVE EVERYTHING TO DATABASE
        # ----------------------------------------------------

        entry = MoodEntry(

            user_id=current_user.id,

            mood=mood,

            journal_text=journal_text,

            sentiment=result["sentiment"],

            emotion_signal=result["emotion_signal"],

            support_message=result["support_message"],

            distress_flag=result["distress_flag"],

            energy=energy,

            sleep=sleep,

            stress=stress,

            connection=connection,

            wellness_score=wellness_score,

            wellness_level=wellness_level,

            wellness_insight=wellness_insight
        )

        db.session.add(entry)

        db.session.commit()

        print("ENTRY SAVED:", entry.id)

        return redirect(
            url_for(
                "result",
                entry_id=entry.id
            )
        )

    return render_template(
        "checkin.html"
    )


# ============================================================
# RESULT
# ============================================================

@app.route("/result/<int:entry_id>")
@login_required
def result(entry_id):

    entry = MoodEntry.query.filter_by(
        id=entry_id,
        user_id=current_user.id
    ).first_or_404()

    return render_template(
        "result.html",
        entry=entry
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
@login_required
def dashboard():

    entries = MoodEntry.query.filter_by(
        user_id=current_user.id
    ).order_by(
        MoodEntry.created_at.desc()
    ).all()

    return render_template(
        "dashboard.html",
        entries=entries
    )


# ============================================================
# HISTORY
# ============================================================

@app.route("/history")
@login_required
def history():

    entries = MoodEntry.query.filter_by(
        user_id=current_user.id
    ).order_by(
        MoodEntry.created_at.desc()
    ).all()

    return render_template(
        "history.html",
        entries=entries
    )


# ============================================================
# SUPPORT / RESOURCES
# ============================================================

@app.route("/support")
def support():

    return render_template(
        "support.html"
    )


# ============================================================
# MOOD DATA API
# ============================================================

@app.route("/api/mood-data")
@login_required
def mood_data():

    entries = MoodEntry.query.filter_by(
        user_id=current_user.id
    ).order_by(
        MoodEntry.created_at.asc()
    ).all()

    data = []

    for entry in entries:

        data.append({
            "date": (
                entry.created_at.strftime("%Y-%m-%d")
                if entry.created_at
                else ""
            ),

            "mood": entry.mood,

            "mood_value": MOOD_VALUES.get(
                entry.mood,
                0
            ),

            "sentiment": entry.sentiment,

            "wellness_score": (
                entry.wellness_score
                if entry.wellness_score is not None
                else 0
            ),

            "wellness_level": (
                entry.wellness_level
                if entry.wellness_level
                else ""
            )
        })

    return jsonify(data)


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

with app.app_context():

    db.create_all()


# ============================================================
# RUN APP
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
