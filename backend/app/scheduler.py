"""Dev-only automatic trigger for the weekly summary job (see
app/services/weekly_summary_service.py and app/cli.py).

Only runs under the Flask development server (`flask run --debug`, which is
what docker-compose.yml's dev backend service uses) — never under gunicorn.
Production runs multiple gunicorn worker processes; an in-process scheduler
started in each of them would fire the job once per worker instead of once.
Production should instead call `flask send-weekly-summaries` from an
external cron.
"""

import os

from flask import Flask

_scheduler = None


def init_scheduler(app: Flask) -> None:
    global _scheduler
    if _scheduler is not None or app.testing or not app.debug:
        return
    # Werkzeug's reloader re-executes this module in a parent "watcher"
    # process before spawning the real server subprocess — only the
    # subprocess (WERKZEUG_RUN_MAIN=true) should actually own the scheduler.
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return

    from apscheduler.schedulers.background import BackgroundScheduler

    from app.services import weekly_summary_service

    def _run_job() -> None:
        with app.app_context():
            weekly_summary_service.generate_weekly_summaries()

    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(_run_job, trigger="cron", day_of_week="mon", hour=6, minute=0)
    scheduler.start()
    _scheduler = scheduler
