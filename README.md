# Amar Bangladesh

A bilingual, mobile-first public-service information prototype built with Flask and SQLite.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000.

## Admin setup

Set `ADMIN_EMAIL` before signing up with that email address. The matching account is assigned the admin role. Never publish a default admin password. Set a strong `SECRET_KEY` in production.

## Render deployment

Create a new Render Web Service from this GitHub repository. Render can use the included `render.yaml`. Set `ADMIN_EMAIL` in the Render environment settings. For production, attach persistent storage and set `DATABASE_PATH` to a file on that disk; otherwise SQLite data may be lost on redeploy.

## Data accuracy

The GDP Growth Rate entry is a historical dataset reference for 1980–2015, not live data. The app labels it accordingly. Add current government datasets only when a verified official API/feed and update schedule are available.

## Security notes

Passwords are hashed, sessions use a secret key, and form submissions use CSRF tokens. Before public launch, configure HTTPS, a persistent database, backups, rate limiting, and a reviewed admin account. This is a prototype, not a certified government service.
