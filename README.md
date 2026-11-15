# Amar Bangladesh

A bilingual (Bangla and English) mobile-friendly web app prototype for finding useful information about healthcare, jobs, education, government services, local services, and emergency contacts in Bangladesh.

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Deploy
This repository includes a `render.yaml` Blueprint configuration. Connect the repository to Render and deploy the Blueprint.

## Important notes
- This is an early prototype; verify all public information with its original source.
- Government live-data APIs are not connected yet; the Open Data page links to public portals only.
- Set a strong `SECRET_KEY` in the hosting environment. Use persistent storage for SQLite before relying on user accounts in production.
- No admin account or default password is created.
