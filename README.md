# InfoPlex

Django LMS for secondary school through CSE & EEE — courses, YouTube embeds, module quizzes, student dashboard, and manual bKash checkout.

## Stack

- Django + templates + CSS + JS
- SQLite by default (set `DATABASE_URL` for PostgreSQL)
- Gunicorn + WhiteNoise for production (Render)
- Brevo email when `BREVO_API_KEY` is set; otherwise console/mock
- Manual bKash payment (admin approves transactions)

## Quick start (local)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional; or export DJANGO_DEBUG=True
export DJANGO_DEBUG=True
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 0.0.0.0:8765
```

Open http://127.0.0.1:8765/

### Demo credentials

| Role    | Username  | Password    |
|---------|-----------|-------------|
| Admin   | `admin`   | `admin123`  |
| Student | `student` | `student123`|

Coupons: `WELCOME20` (20% off), `BKASH100` (৳10 off), `FREELEARN` (100% off — instant enroll).

Admin: http://127.0.0.1:8765/admin/ — approve pending **Transactions** to unlock paid enrollments.

## Deploy on Render

Production target is [Render](https://render.com). This repo includes `render.yaml` (Blueprint), a `Procfile`, and production settings (WhiteNoise, `DATABASE_URL`, proxy SSL).

### Option A — Blueprint (recommended)

1. Push this branch (or merge to `main`) to GitHub: `taifur-rahaman/Infoplex_live`.
2. In the [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**.
3. Connect the GitHub account/org if needed, then select **Infoplex_live**.
4. Confirm the Blueprint from `render.yaml` (web service **infoplex** + Postgres **infoplex-db**, free plan).
5. Apply. Render will:
   - Generate `SECRET_KEY`
   - Set `DEBUG=false`, `PYTHON_VERSION`, `WEB_CONCURRENCY`, `ALLOWED_HOSTS`
   - Link `DATABASE_URL` from the Postgres instance
   - Build: `pip install` + `collectstatic`
   - Pre-deploy: `migrate` + `seed_demo` (idempotent demo data)
   - Start: `gunicorn config.wsgi`

After the first deploy, open the service URL (`https://infoplex-….onrender.com`). Log in with the demo credentials above, or create a production superuser:

```bash
# Render Shell →
python manage.py createsuperuser
```

### Option B — Manual New Web Service

1. **New** → **Web Service** → connect `Infoplex_live`.
2. Runtime: **Python**. Build command:

   ```text
   pip install -r requirements.txt && python manage.py collectstatic --no-input
   ```

3. Start command:

   ```text
   gunicorn config.wsgi --log-file -
   ```

4. **New** → **PostgreSQL** (free). Copy the **Internal Database URL**.
5. Web service **Environment**:

   | Key | Value |
   |-----|--------|
   | `PYTHON_VERSION` | `3.12.8` |
   | `SECRET_KEY` | Generate (Render “generate” or a long random string) |
   | `DEBUG` | `false` |
   | `WEB_CONCURRENCY` | `2` |
   | `ALLOWED_HOSTS` | `.onrender.com` |
   | `DATABASE_URL` | Internal Database URL from the Postgres service |

6. Optional **Pre-Deploy Command**:

   ```text
   python manage.py migrate --no-input && python manage.py seed_demo
   ```

   Or migrate only, then `createsuperuser` in the Shell (see notes below).

### Environment variables

| Variable | Required | Notes |
|----------|----------|--------|
| `SECRET_KEY` | Yes (prod) | Also accepts `DJANGO_SECRET_KEY` |
| `DEBUG` / `DJANGO_DEBUG` | Prod: `false` | Default is `False` if unset |
| `DATABASE_URL` | Prod | From Render Postgres; omit locally → SQLite |
| `ALLOWED_HOSTS` / `DJANGO_ALLOWED_HOSTS` | Prod | `.onrender.com` is enough; `RENDER_EXTERNAL_HOSTNAME` is auto-added |
| `CSRF_TRUSTED_ORIGINS` | Optional | Auto-adds `https://$RENDER_EXTERNAL_HOSTNAME` and `https://*.onrender.com` |
| `WEB_CONCURRENCY` | Optional | Gunicorn workers (Blueprint default `2`) |
| `PYTHON_VERSION` | Render | e.g. `3.12.8` |
| `BREVO_API_KEY` / `BREVO_SENDER_EMAIL` | Optional | Email; console fallback without key |
| `BKASH_ACCOUNT_NUMBER` / `BKASH_ACCOUNT_NAME` | Optional | Manual payment display |

Do **not** commit secrets, `.env` files, or PATs.

### Seed note

`seed_demo` is safe to re-run for demo content (users/courses/coupons use `get_or_create` / `update_or_create`). Re-runs may add extra quiz-attempt rows for the demo student. For a clean production site without demo passwords, use **migrate only** and `createsuperuser` instead of `seed_demo`.

## Environment (local)

Copy `.env.example`. Optional keys:

- `DATABASE_URL` — PostgreSQL connection string
- `BREVO_API_KEY` / `BREVO_SENDER_EMAIL`
- `BKASH_ACCOUNT_NUMBER` / `BKASH_ACCOUNT_NAME`
- `SECRET_KEY` or `DJANGO_SECRET_KEY`, `DEBUG` / `DJANGO_DEBUG`, `ALLOWED_HOSTS` / `DJANGO_ALLOWED_HOSTS`

## Theme

Light and dark modes via CSS variables. Header sun/moon toggle persists to `localStorage` (`infoplex-theme`); first visit follows `prefers-color-scheme`. An early inline script sets `data-theme` before paint to avoid flash.

## Features

Homepage (hero, categories, search) · catalog filters & pagination · course detail · signup/login · checkout + coupons + bKash · student dashboard · course player · timed quizzes · full Django Admin · optional roadmap/prerequisites · light/dark theme
