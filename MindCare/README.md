# MindCare

A non-diagnostic mental wellness check-in and mood-tracking web app built
with Flask. Users log a daily mood, optionally write a journal entry, and
receive general, supportive (never diagnostic) feedback based on language
patterns. Mood history is visualized on a dashboard.

**This app does not diagnose mental health conditions and is not a
substitute for professional care or emergency services.**

## Features

- Register / login (hashed passwords, Flask-Login sessions)
- Daily mood check-in with optional journal text
- Rule-based + VADER sentiment analysis, labeled as "language patterns"
  (e.g. "Stress-related language"), never as a diagnosis
- Basic distress-phrase detection that routes to a safety/support message
- Mood history log
- Dashboard with a mood trend line chart and sentiment distribution chart
  (Chart.js)
- Support & Resources page with general crisis-support guidance

## Project structure

```
MindCare/
├── app.py                # Flask app, routes, models
├── analysis.py            # Sentiment / emotion-signal logic
├── requirements.txt
├── render.yaml             # Render Blueprint (one-click deploy)
├── Procfile                # Fallback start command
├── templates/               # Jinja2 HTML templates
├── static/
│   ├── css/style.css
│   └── js/dashboard.js
└── database/                # SQLite file lives here locally
```

## Run locally

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Visit http://localhost:5000

By default this uses a local SQLite database at `database/mindcare.db`
(created automatically on first run).

## Deploy to Render

### Option A — One-click Blueprint (recommended)

1. Push this project to a GitHub (or GitLab) repository.
2. In the Render dashboard, click **New > Blueprint**, and point it at
   your repo. Render will read `render.yaml` and create the web service
   automatically, including:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
   - A generated `SECRET_KEY` environment variable
   - A small persistent disk mounted at `database/` so your SQLite file
     survives deploys/restarts (Render's free web services otherwise use
     an ephemeral filesystem)
3. Click **Apply**. Render will build and deploy the app; the first
   request will auto-create the database tables.

### Option B — Manual web service

1. Push the project to GitHub.
2. In Render, click **New > Web Service** and connect the repo.
3. Set:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
4. Add an environment variable `SECRET_KEY` with any random string.
5. (Recommended) Add a **Disk** mounted at `database/` so SQLite data
   persists across deploys — otherwise your data resets each deploy.
6. Deploy.

### Using Postgres instead of SQLite (optional, more robust)

Render's free disks are limited and SQLite doesn't scale well with
multiple instances. For a more production-ready setup:

1. Create a **Render Postgres** database (free tier available).
2. Copy its **Internal Database URL**.
3. Add it to your web service as the `DATABASE_URL` environment variable.
4. Redeploy — `app.py` automatically detects `DATABASE_URL` and uses
   Postgres instead of SQLite (via `psycopg2-binary`, already in
   `requirements.txt`).

## Environment variables

| Variable       | Required | Description                                   |
|----------------|----------|------------------------------------------------|
| `SECRET_KEY`   | Yes      | Flask session signing key                      |
| `DATABASE_URL` | No       | Postgres connection string; falls back to SQLite |
| `PORT`         | No       | Set automatically by Render                    |

## Notes on responsible design

- The app never states or implies a clinical diagnosis (e.g. "you have
  depression"). It only labels general language patterns.
- Messages matching a short list of crisis-related phrases are routed to
  a safety message encouraging the user to contact a trusted person,
  a professional, or emergency services — the app explicitly states that
  automated detection can be wrong and is not an emergency service.
- The Support & Resources page is shown regardless of login state.
