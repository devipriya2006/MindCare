# MindCare Deployment Checklist

## Before pushing to GitHub
- [ ] `.env` is not committed
- [ ] Database files are not committed
- [ ] `__pycache__` is not committed
- [ ] `requirements.txt` contains only packages actually used
- [ ] `render.yaml` has `rootDir: MindCare`
- [ ] `Procfile` contains `web: gunicorn app:app`
- [ ] No real credentials appear in source files

## Render
Environment variables:
- `SECRET_KEY`
- `DATABASE_URL`

Build command:
`pip install -r requirements.txt`

Start command:
`gunicorn app:app`

## Test after deployment
- [ ] Home page
- [ ] Registration
- [ ] Login
- [ ] Mood check-in
- [ ] Journal analysis
- [ ] Result page
- [ ] Dashboard
- [ ] History
- [ ] Logout
- [ ] Database persistence
- [ ] `/api/mood-data`

## Before advanced features
Make sure the current deployed version is stable before adding
multi-question assessment, weekly summaries, chatbot, or voice analysis.
