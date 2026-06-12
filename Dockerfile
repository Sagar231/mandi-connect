FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for psycopg + Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev libjpeg-dev zlib1g-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Collect static at build time (safe defaults; real env injected at runtime)
RUN DJANGO_SECRET_KEY=build-time DJANGO_DEBUG=False \
    DATABASE_URL=sqlite:///build.sqlite3 REDIS_URL=redis://localhost:6379/0 \
    python manage.py collectstatic --noinput

# Port is resolved inside gunicorn.conf.py (reads $PORT in Python), so this
# command never depends on shell variable expansion.
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi:application -c gunicorn.conf.py"]
