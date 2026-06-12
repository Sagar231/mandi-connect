# MandiConnect 🥬

A digital local-market (mandi) platform. Customers browse markets and compare **live vendor prices** for produce; vendors manage their shops, stock, and daily prices. API-first with **Django REST Framework**, server-rendered **Django templates** styled with **Tailwind CSS** and made interactive with **vanilla JS + jQuery (AJAX)**. Background work runs on **Celery + Redis**.

No React/Vue/SPA — by design.

## Two journeys

**Customers** sign up at `/register/`, browse markets, open a market to see **what's sold there** with live price ranges, compare the cheapest vendor for any product, favorite vendors, and set price-drop alerts.

**Vendors** sign up at `/sell/` — the form creates their account **and their shop** (name, market, main goods) in one step. The shop stays hidden until an **admin verifies** it, after which the vendor manages daily prices and stock inline from `/dashboard/`. A shared login routes each role to the right place.

Markets, products, and vendors all carry real images: produce uses TheMealDB ingredient icons, markets use Unsplash photos, and shops use generated banners — all hardcoded as URLs in the seed so they render on Railway with **zero media-storage setup** (every `<img>` also has a branded fallback).

---

## Tech stack

| Layer        | Choice                                                      |
|--------------|------------------------------------------------------------|
| Backend      | Python 3.12, Django 5.x, Django REST Framework             |
| Auth         | JWT (`djangorestframework-simplejwt`) — rotation + blacklist |
| Database     | PostgreSQL (SQLite fallback for local/dev)                 |
| Async/tasks  | Celery worker + Celery Beat, broker/result = Redis         |
| Caching      | Redis (`django-redis`) — comparison & trend endpoints      |
| Frontend     | Django templates + Tailwind (CDN) + jQuery AJAX + Chart.js |
| API docs     | drf-spectacular (Swagger/OpenAPI)                          |
| Serving      | Gunicorn + WhiteNoise                                       |
| Deploy       | Railway (Nixpacks) + Docker/`docker-compose` for local     |

---

## App structure

```
config/        project settings, urls, wsgi/asgi, celery
common/        shared abstract models, permissions, tokens
users/         custom email-login User, JWT auth, verification, reset
markets/       Market model + nearby (Haversine) endpoint
vendors/       Vendor model, verification, dashboard stats
catalog/       Category + Product
pricing/       PriceListing (core), PriceHistory, compare & trend (cached)
reviews/       Review/Rating
notifications/ Favorite, PriceAlert, async emails + CSV export
frontend/      server-rendered Tailwind/jQuery template views
templates/     base + pages (home, market, compare, vendor, auth, dashboard)
static/js/     api.js — JWT-aware AJAX helper
tests/         pytest + DRF APIClient
```

## Data models

`User` (email login, role: customer/vendor/admin) · `Market` · `Vendor` (OneToOne user, market FK, `is_verified`, `avg_rating`) · `Category` · `Product` (unit: kg/dozen/litre/piece) · **`PriceListing`** (vendor + product + price + stock + date — the core entity) · `PriceHistory` · `Review` · `Favorite` · `PriceAlert`. Timestamps everywhere; soft-delete on markets, vendors, and listings.

---

## Quick start (local, no Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # has USE_LOCMEM_CACHE/EAGER on, so no Redis needed locally
python manage.py migrate
python manage.py seed_data      # sample markets/vendors/products/prices
python manage.py createsuperuser
python manage.py runserver
```

Open:
- App: http://localhost:8000/
- Swagger: http://localhost:8000/api/docs/
- Admin: http://localhost:8000/admin/

Run Celery in two more terminals (needs Redis running):

```bash
celery -A config worker -l info
celery -A config beat -l info
```

### Seed accounts (after `seed_data`)

| Role     | Email                          | Password       |
|----------|--------------------------------|----------------|
| Admin    | admin@mandiconnect.local       | admin12345     |
| Customer | customer@mandiconnect.local    | customer12345  |
| Vendor   | vendor1@mandiconnect.local …   | vendor12345    |

---

## Run with Docker Compose (full stack)

Brings up `web`, `db` (Postgres), `redis`, `celery-worker`, `celery-beat`:

```bash
docker compose up --build
# first run, in another shell:
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_data
```

App on http://localhost:8000/.

---

## Deploy to Railway

This repo is **Railway-first**. Railway auto-detects the app via `nixpacks.toml` / `Procfile`.

1. **Create a project** and add two plugins: **PostgreSQL** and **Redis**. Railway injects `DATABASE_URL` and `REDIS_URL` automatically.
2. **Deploy the web service** from this repo. The `Procfile` `release` phase runs migrations; `web` runs Gunicorn.
3. **Set variables** on the service (see below).
4. **Add a worker service** (same repo) with start command `celery -A config worker -l info`.
5. **Add a beat service** (same repo) with start command `celery -A config beat -l info`.

All three services share the same Postgres + Redis plugins.

### Required environment variables

| Variable                | Notes                                                       |
|-------------------------|-------------------------------------------------------------|
| `DJANGO_SECRET_KEY`     | long random string                                          |
| `DJANGO_DEBUG`          | `False` in production                                       |
| `DJANGO_ALLOWED_HOSTS`  | e.g. `.railway.app,yourdomain.com`                          |
| `CSRF_TRUSTED_ORIGINS`  | e.g. `https://*.railway.app`                                |
| `DATABASE_URL`          | provided by Railway Postgres plugin                         |
| `REDIS_URL`             | provided by Railway Redis plugin                            |
| `FRONTEND_BASE_URL`     | your public URL (used in verification/reset email links)   |
| `EMAIL_BACKEND` + SMTP  | set a real SMTP backend for production emails               |
| `LISTING_STALE_DAYS`    | default `3`                                                 |

`collectstatic` runs automatically during the Nixpacks build; WhiteNoise serves the files.

---

## API overview

Base path: `/api/`

**Auth** (`/api/auth/`): `register/` (customer), `register/vendor/` (vendor account **+ shop** in one step, pending verification), `login/` (role-routed), `token/refresh/`, `logout/` (blacklist), `me/`, `verify-email/`, `password/reset/`, `password/reset/confirm/`

**Markets**: `markets/` (list/detail), `markets/nearby/?lat=&lng=&radius_km=`, `markets/{id}/products/` (what's sold here + price ranges)
**Catalog**: `categories/`, `products/` (search/filter by category, unit)
**Vendors**: `vendors/` (verified-only public), `vendors/me/`, `vendors/{id}/verify/` (admin), `vendors/dashboard_stats/`
**Pricing**: `price-listings/` (CRUD, vendor-scoped writes), `compare/?product=&market=` (cached), `price-trend/?product=&days=` (cached)
**Reviews**: `reviews/`
**Customer**: `favorites/`, `price-alerts/`, `price-alerts/export-csv/`

All public endpoints paginate, support ordering/search filters, and are throttled.

---

## Celery tasks

**Scheduled (Beat):**
- `pricing.tasks.snapshot_active_prices` — nightly snapshot of active prices → `PriceHistory`
- `pricing.tasks.expire_stale_listings` — deactivate listings older than `LISTING_STALE_DAYS`
- `reviews.tasks.recompute_vendor_ratings` — recompute all vendor average ratings

**On-demand:**
- `notifications.tasks.send_verification_email`, `send_password_reset_email`
- `notifications.tasks.check_price_alerts` — fired on price change; emails users whose threshold is met
- `notifications.tasks.export_price_list_csv` — emails a CSV price-list export

---

## Tests

```bash
pytest          # uses config.settings_test (in-memory sqlite, eager Celery, locmem cache)
```

Covers auth (register/login/logout-blacklist), role permissions, the comparison & trend endpoints, nearby markets, and the Celery tasks.

---

## Build order (how this was assembled)

models & migrations → auth → core API (markets/products/pricing) → comparison & trends → Celery tasks → frontend templates → tests → Docker/Railway.
