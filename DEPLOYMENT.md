# Deployment Guide — ATS Resume Score Checker

This guide deploys the existing ATS Resume Score Checker to:

* **Backend**: Render (FastAPI)
* **Database**: Render PostgreSQL
* **Frontend**: Vercel (React + Vite)
* **Source**: GitHub

No application code was rebuilt. Only deployment configuration files were added.

---

## Prerequisites

* GitHub account with the repository pushed
* Render account (render.com)
* Vercel account (vercel.com)
* PowerShell (Windows) or terminal

---

## Step 0 — Verify everything locally (do this first)

Run these commands in PowerShell from the repository root (`F:\ATS resume ANalyzer`):

```powershell
# Backend tests (set ENVIRONMENT=development so config uses SQLite fallback)
cd backend
$env:ENVIRONMENT="development"
$env:DATABASE_URL="sqlite+aiosqlite:///./test.db"
python -m pytest tests/ -v --tb=short

# Frontend tests
cd ../frontend
npm run test:run

# Frontend production build (VITE_API_URL required for prod builds)
$env:VITE_API_URL="https://placeholder-backend.onrender.com"
npm run build
```

Expected results: backend 51/53 (2 pre-existing failures unrelated to deployment), frontend 19/19, build succeeds.

---

## Step 1 — Push to GitHub

From the repository root:

```powershell
git add -A
git commit -m "Add deployment configuration for Render and Vercel"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

Replace `YOUR_USERNAME` and `YOUR_REPO` with your GitHub values.

Do not commit `.env` files — they are already in `.gitignore`.

---

## Step 2 — Render PostgreSQL database

1. Log in to [Render](https://render.com).
2. Click **New +** → **PostgreSQL**.
3. Configure:
   * **Name**: `ats-resume-checker-db`
   * **Database name**: `ats_resume_checker`
   * **User**: `ats_resume_user`
   * **Plan**: Starter (free tier)
4. Click **Create Database**.
5. Wait for it to become **Available**.
6. Copy the **External Database URL** (it starts with `postgresql://`).

> **Important**: Render's connection string uses `postgresql://`. This app uses asyncpg, which requires `postgresql+asyncpg://`. When you set `DATABASE_URL` in the backend service (Step 3), replace `postgresql://` with `postgresql+asyncpg://`.

---

## Step 3 — Render backend (FastAPI)

### Option A: Using render.yaml (recommended)

The repository includes `render.yaml`. In the Render dashboard:

1. Click **New +** → **Blueprint**.
2. Connect your GitHub repository.
3. Select the `render.yaml` blueprint.
4. Render will create the web service and database automatically.

### Option B: Manual dashboard setup

1. Click **New +** → **Web Service**.
2. Connect your GitHub repository.
3. Configure:

| Setting | Value |
|---|---|
| **Runtime** | Python |
| **Build command** | `pip install -r requirements.txt` |
| **Start command** | `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Plan** | Starter |

4. Add environment variables (Environment tab):

| Name | Value | Purpose |
|---|---|---|
| `ENVIRONMENT` | `production` | Enables production validation |
| `DEBUG` | `false` | Disables debug mode |
| `DATABASE_URL` | `postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DBNAME` | Production database (convert `postgresql://` → `postgresql+asyncpg://`) |
| `JWT_SECRET_KEY` | `python -c "import secrets; print(secrets.token_urlsafe(64))"` | JWT signing secret (min 32 chars) |
| `ALLOWED_ORIGINS` | `https://YOUR_FRONTEND.vercel.app` | CORS — your Vercel frontend URL |
| `SENTENCE_TRANSFORMER_MODEL` | `all-MiniLM-L6-v2` | NLP model (TF-IDF fallback if unavailable) |
| `SPACY_MODEL` | `en_core_web_sm` | spaCy model (optional, graceful fallback) |
| `LOG_LEVEL` | `INFO` | Log level |
| `MAX_FILE_SIZE_MB` | `10` | Max upload size |
| `RATE_LIMIT_ENABLED` | `true` | Enable rate limiting |
| `WEIGHT_*` | As desired | Scoring weights (must sum to 100) |

5. Click **Create Web Service**.
6. Wait for deployment. The `alembic upgrade head` in the start command runs migrations automatically on every deploy.

7. After deployment, note your backend URL: `https://YOUR_BACKEND.onrender.com`

---

## Step 4 — Vercel frontend (React)

1. Log in to [Vercel](https://vercel.com).
2. Click **Add New** → **Project**.
3. Import your GitHub repository.
4. Configure:

| Setting | Value |
|---|---|
| **Framework preset** | Vite |
| **Build command** | `npm run build` |
| **Output directory** | `dist` |
| **Install command** | `npm install` |
| **Root directory** | `frontend` (if your repo root contains `frontend/`) |

5. Add environment variable:

| Name | Value |
|---|---|
| `VITE_API_URL` | `https://YOUR_BACKEND.onrender.com` |

> This URL is baked into the build at build time. If you change it, redeploy the frontend.

6. Click **Deploy**.
7. After deployment, note your frontend URL: `https://YOUR_FRONTEND.vercel.app`

---

## Step 5 — Connect frontend to backend

1. In the Render dashboard, go to your backend service → **Environment**.
2. Add/update `ALLOWED_ORIGINS`:
   ```
   https://YOUR_FRONTEND.vercel.app
   ```
3. Save changes. Render will redeploy automatically.

4. Test the live site:
   * Open `https://YOUR_FRONTEND.vercel.app`
   * Upload a resume and paste a job description
   * Verify the score result loads
   * Register/login and check history

---

## Files changed

| File | Change | Reason |
|---|---|---|
| `frontend/vercel.json` | New | Required for Vercel SPA routing (React Router). Without it, page refresh on `/upload`, `/results/:id`, etc. returns 404. |
| `render.yaml` | New | Render blueprint defining backend web service and PostgreSQL database. Makes deployment reproducible. |
| `backend/app/database/connection.py` | Modified | Converts `postgresql://` → `postgresql+asyncpg://` so Render's default connection string works with SQLAlchemy asyncpg. |
| `backend/.env.example` | Modified | Added `PORT=8000` documentation for local dev. |
| `DEPLOYMENT.md` | New | This deployment guide. |

No application logic, UI, tests, or features were modified.

---

## Environment variables (no secret values)

### Backend (Render)

| Name | Purpose | Required in production |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string (`postgresql+asyncpg://...`) | Yes |
| `JWT_SECRET_KEY` | JWT token signing secret (min 32 chars, not a default value) | Yes |
| `ENVIRONMENT` | Set to `production` | Yes |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins (your Vercel URL) | Yes |
| `DEBUG` | Set to `false` | Recommended |
| `PORT` | Port to listen on (Render injects `$PORT`) | Render handles automatically |
| `SENTENCE_TRANSFORMER_MODEL` | NLP model name | No (default OK) |
| `SPACY_MODEL` | spaCy model name | No (optional) |
| `LOG_LEVEL` | Logging level | No |
| `MAX_FILE_SIZE_MB` | Max upload size in MB | No |
| `RATE_LIMIT_ENABLED` | Enable rate limiting | No |
| `WEIGHT_KEYWORD_MATCH`, etc. | Scoring weights (must sum to 100) | No |

### Frontend (Vercel)

| Name | Purpose | Required in production |
|---|---|---|
| `VITE_API_URL` | Backend API URL (baked into build) | Yes |

---

## Migration procedure

Migrations run automatically on every Render deploy via the start command:

```
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

To run migrations manually against a database:

```powershell
cd backend
$env:DATABASE_URL="postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DBNAME"
alembic upgrade head
```

To check current migration version:

```powershell
alembic current
```

---

## Live testing checklist

After deployment:

- [ ] Backend `/healthz` returns `{"status": "ok"}`
- [ ] Backend `/health` returns database `connected`
- [ ] Backend `/readyz` returns `ready`
- [ ] Frontend loads at Vercel URL
- [ ] Page refresh on `/upload`, `/results/1`, `/history`, `/login` works (no 404)
- [ ] Resume upload + analysis completes
- [ ] Register/login works
- [ ] Analysis history is saved and retrievable
- [ ] Demo mode (pasted text) works
- [ ] CORS: frontend can call backend without browser errors

---

## Deployment limitations and costs

### Render

* **Free tier**: Backend sleeps after 15 minutes of inactivity. First request after sleep may take 30+ seconds to wake up.
* **Starter plan (~$7/mo)**: No sleep, always on.
* **PostgreSQL Starter (free)**: Limited connections and storage. Suitable for low-traffic use.
* **Ephemeral disk**: Uploaded files are deleted after analysis (by design). Reports are generated on-the-fly. Nothing critical is stored on local disk.
* **512 MB RAM**: Sentence Transformers is disabled by default (TF-IDF fallback used), so memory usage is low. spaCy model is optional and gracefully falls back.
* **Build time**: Installing `sentence-transformers` (with torch) can be slow. The app works without it due to the fallback.

### Vercel

* **Hobby plan (free)**: Unlimited personal projects, automatic HTTPS, custom domains supported.
* **Build**: `VITE_API_URL` must be set before building. Changing it requires a redeploy.

### Expected monthly cost

| Service | Plan | Est. Cost |
|---|---|---|
| Render Backend | Starter | ~$7/mo (or free with sleep) |
| Render PostgreSQL | Starter | Free |
| Vercel Frontend | Hobby | Free |
| GitHub | Free | Free |

**Total: ~$7/mo** (or $0/mo using Render free tier with backend sleep).
