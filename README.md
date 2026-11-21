# CarePulse — Vercel-ready Python Flask project

## Deploy to Vercel using GitHub
1. Extract this ZIP.
2. Create a new GitHub repository and upload the contents of the `CarePulse_Python` folder (not the ZIP itself).
3. In Vercel, choose **Add New → Project**, import that GitHub repository, and click **Deploy**.
4. Vercel should detect Flask from `requirements.txt` and the root `app.py`. No build command or output directory is required.

## Run locally (Windows)
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000.

## Run locally (macOS/Linux)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Included
- Flask Python backend and responsive CarePulse UI
- Symptom guidance for fever, cough, headache, acidity, loose motion and cold
- Warning-sign phrase checks
- Local SQLite consultation logging when run outside Vercel
- Vercel `public/` assets and Python 3.12 selection

## Important deployment limitation
Vercel Functions do not provide a persistent writable project filesystem. On Vercel, symptom checks work, but SQLite consultation logging is deliberately disabled and `/admin/consultations` will show no stored records. Add a hosted PostgreSQL database (for example, Neon or Supabase) before enabling persistent consultation history.

The admin route is a demo and has no authentication. Do not expose private health data or use it as a production admin panel without authentication, authorization, privacy controls and security review. This educational guide is not a diagnostic tool or a substitute for professional medical care.


## Vercel template-path fix
This package places `app.py` and `templates/` at the same repository root and configures Flask with absolute template/static paths. Set Vercel Root Directory to `./`.
