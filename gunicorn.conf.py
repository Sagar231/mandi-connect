"""Gunicorn config — resolves the port in Python so we never depend on the
shell expanding $PORT (Railway passes PORT as an env var, not always expanded
in the start command)."""
import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
workers = int(os.environ.get("WEB_CONCURRENCY", "3"))
timeout = 120
accesslog = "-"
errorlog = "-"
