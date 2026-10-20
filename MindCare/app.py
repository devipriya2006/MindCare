
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
