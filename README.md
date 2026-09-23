# InfoPlex

Django LMS for secondary school through CSE & EEE — courses, YouTube embeds, module quizzes, student dashboard, and manual bKash checkout.

## Stack

- Django + templates + CSS + JS
- SQLite by default (set `DATABASE_URL` for PostgreSQL)
- Brevo email when `BREVO_API_KEY` is set; otherwise console/mock
- Manual bKash payment (admin approves transactions)

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
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

## Environment

Copy `.env.example`. Optional keys:

- `DATABASE_URL` — PostgreSQL connection string
- `BREVO_API_KEY` / `BREVO_SENDER_EMAIL`
- `BKASH_ACCOUNT_NUMBER` / `BKASH_ACCOUNT_NAME`
- `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`

## Theme

Light and dark modes via CSS variables. Header sun/moon toggle persists to `localStorage` (`infoplex-theme`); first visit follows `prefers-color-scheme`. An early inline script sets `data-theme` before paint to avoid flash.

## Features

Homepage (hero, categories, search) · catalog filters & pagination · course detail · signup/login · checkout + coupons + bKash · student dashboard · course player · timed quizzes · full Django Admin · optional roadmap/prerequisites · light/dark theme
