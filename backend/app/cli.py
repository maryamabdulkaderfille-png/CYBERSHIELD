"""Flask CLI commands for operations that don't belong on an HTTP route —
mirrors the project's existing "migrations are a separate, explicit step"
philosophy (see Dockerfile.prod) rather than triggering them implicitly."""

import click
from flask import Flask


def register_cli(app: Flask) -> None:
    @app.cli.command("send-weekly-summaries")
    def send_weekly_summaries() -> None:
        """Creates the weekly in-app security summary notification for every
        eligible user. In production (gunicorn, multiple workers) this is the
        production-safe way to run it — wire it to an external cron rather
        than relying on an in-process scheduler, which would fire once per
        worker. The dev server runs this automatically instead (see
        app/scheduler.py)."""
        from app.services import weekly_summary_service

        created = weekly_summary_service.generate_weekly_summaries()
        click.echo(f"Created {created} weekly summary notification(s).")
