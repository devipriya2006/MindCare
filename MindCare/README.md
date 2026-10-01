# MindCare

## Mental Wellness Support & Mood Tracking Platform

MindCare is a Flask-based wellness-support and mood-tracking platform.
Users can create an account, record moods, write journal entries, receive
sentiment/emotion-related feedback, and view their mood history.

> **Disclaimer:** MindCare is a wellness-support application, not a medical
> diagnostic system. Its analysis provides general sentiment and
> emotion-related signals from user-provided text.

## Features

- User registration and login
- Password hashing
- Mood check-ins
- Journal entries
- Text sentiment analysis
- Emotion-related signals
- Supportive feedback
- Distress flagging
- Personal mood history
- Dashboard and trend data
- PostgreSQL persistence
- SQLite fallback for local development
- Gunicorn production server
- Render deployment support

## Technology Stack

**Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Login, VADER Sentiment, Gunicorn

**Database:** PostgreSQL / Neon, with SQLite fallback locally

**Frontend:** HTML, CSS, JavaScript

**Deployment:** Render

## Project Structure

```text
MindCare/
├── app.py
├── analysis.py
├── requirements.txt
├── render.yaml
├── Procfile
├── README.md
├── DEPLOYMENT_CHECKLIST.md
├── .gitignore
├── .env.example
├── templates/
└── static/
```

## Application Flow

```text
User
  ↓
Registration / Login
  ↓
Mood Check-in + Journal
  ↓
Text Analysis
  ↓
Sentiment + Emotion-related Signal
  ↓
Supportive Feedback
  ↓
PostgreSQL
  ↓
Dashboard + History
```

## Local Setup

```bash
git clone <your-github-repository-url>
cd MindCare/MindCare
python -m venv venv
```

Windows:
```bash
venv\Scripts\activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add local values if required.

Run:
```bash
python app.py
```

Open `http://127.0.0.1:5000`.

If `DATABASE_URL` is not set, the application uses its SQLite fallback.

## Production Deployment

Render configuration:

- Root directory: `MindCare`
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`

Required Render environment variables:

```text
SECRET_KEY
DATABASE_URL
```

Never commit real secrets or database credentials.

## Database

The application reads PostgreSQL from `DATABASE_URL`. If the variable is
not present, it falls back to SQLite for local development.

## Current Analysis

Journal text is analyzed using VADER sentiment analysis and the application's
emotion-related signal logic. Results are intended for wellness support and
must not be interpreted as a clinical diagnosis.

## Planned Enhancements

- Multi-question mood assessment
- Weekly wellness summaries
- Conversational support assistant
- Additional non-diagnostic wellness signals
- Optional voice-based emotion-related signal analysis
