"""
Scheduler — cron-like task scheduler for Silver Team.
Uses APScheduler for weekly reports, daily stats, and per-agent tasks.
Gracefully degrades if APScheduler is not installed.
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
    from apscheduler.triggers.cron import CronTrigger  # type: ignore

    _APScheduler_AVAILABLE = True
except ImportError:  # pragma: no cover
    _APScheduler_AVAILABLE = False
    logger.warning("APScheduler not installed — scheduler will run in manual mode only.")


SETTINGS_PATH = Path(__file__).parent.parent / "config" / "settings.json"


def _load_settings() -> Dict[str, Any]:
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


class ScheduledJob:
    """Represents a registered job."""

    def __init__(
        self,
        job_id: str,
        name: str,
        func: Callable,
        trigger: str = "interval",
        kwargs: Optional[Dict] = None,
        **trigger_kwargs: Any,
    ) -> None:
        self.job_id = job_id
        self.name = name
        self.func = func
        self.trigger = trigger
        self.kwargs = kwargs or {}
        self.trigger_kwargs = trigger_kwargs
        self.last_run: Optional[str] = None
        self.run_count: int = 0
        self.errors: int = 0

    def run(self) -> None:
        """Execute the job and update stats."""
        self.last_run = datetime.utcnow().isoformat()
        self.run_count += 1
        try:
            self.func(**self.kwargs)
            logger.info("Job '%s' completed successfully.", self.name)
        except Exception as exc:  # noqa: BLE001
            self.errors += 1
            logger.error("Job '%s' failed: %s", self.name, exc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "name": self.name,
            "trigger": self.trigger,
            "trigger_kwargs": self.trigger_kwargs,
            "last_run": self.last_run,
            "run_count": self.run_count,
            "errors": self.errors,
        }


class Scheduler:
    """
    Silver Team scheduler.

    When APScheduler is available, jobs run in background threads automatically.
    Otherwise, jobs can be triggered manually via `run_job(job_id)`.
    """

    def __init__(self) -> None:
        self._jobs: Dict[str, ScheduledJob] = {}
        self._lock = threading.Lock()
        self._scheduler: Optional[Any] = None
        self._running = False

        settings = _load_settings()
        sched_cfg = settings.get("scheduler", {})
        self._enabled: bool = sched_cfg.get("enabled", True)
        self._weekly_day: str = sched_cfg.get("weekly_report_day", "monday")
        self._weekly_hour: int = sched_cfg.get("weekly_report_hour", 9)
        self._weekly_minute: int = sched_cfg.get("weekly_report_minute", 0)
        self._daily_hour: int = sched_cfg.get("daily_stats_hour", 23)
        self._daily_minute: int = sched_cfg.get("daily_stats_minute", 30)

    # ------------------------------------------------------------------ #
    # Registration                                                         #
    # ------------------------------------------------------------------ #

    def register_job(
        self,
        job_id: str,
        name: str,
        func: Callable,
        trigger: str = "interval",
        func_kwargs: Optional[Dict] = None,
        **trigger_kwargs: Any,
    ) -> ScheduledJob:
        """Register a new job. Does not start the scheduler."""
        job = ScheduledJob(
            job_id=job_id,
            name=name,
            func=func,
            trigger=trigger,
            kwargs=func_kwargs or {},
            **trigger_kwargs,
        )
        with self._lock:
            self._jobs[job_id] = job
        logger.debug("Registered job '%s' (%s).", name, job_id)
        return job

    def register_weekly_report(self, func: Callable) -> ScheduledJob:
        """Convenience: register the weekly report job."""
        return self.register_job(
            job_id="weekly_report",
            name="Weekly Report Generation",
            func=func,
            trigger="cron",
            day_of_week=self._weekly_day[:3],
            hour=self._weekly_hour,
            minute=self._weekly_minute,
        )

    def register_daily_stats(self, func: Callable) -> ScheduledJob:
        """Convenience: register the daily stats job."""
        return self.register_job(
            job_id="daily_stats",
            name="Daily Stats Update",
            func=func,
            trigger="cron",
            hour=self._daily_hour,
            minute=self._daily_minute,
        )

    # ------------------------------------------------------------------ #
    # Start / Stop                                                         #
    # ------------------------------------------------------------------ #

    def start(self) -> bool:
        """Start the background scheduler. Returns True if started."""
        if not self._enabled:
            logger.info("Scheduler disabled in settings.")
            return False
        if not _APScheduler_AVAILABLE:
            logger.warning("APScheduler not available — cannot start background scheduler.")
            return False
        if self._running:
            return True

        self._scheduler = BackgroundScheduler(timezone="UTC")

        with self._lock:
            for job in self._jobs.values():
                self._add_to_apscheduler(job)

        self._scheduler.start()
        self._running = True
        logger.info("Background scheduler started with %d jobs.", len(self._jobs))
        return True

    def _add_to_apscheduler(self, job: ScheduledJob) -> None:
        """Add a ScheduledJob to the APScheduler instance."""
        if self._scheduler is None:
            return
        try:
            if job.trigger == "cron":
                trigger = CronTrigger(**job.trigger_kwargs)
            else:
                trigger = job.trigger  # type: ignore[assignment]

            self._scheduler.add_job(
                func=job.run,
                trigger=trigger,
                id=job.job_id,
                name=job.name,
                replace_existing=True,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to schedule job '%s': %s", job.name, exc)

    def stop(self) -> None:
        """Stop the background scheduler."""
        if self._scheduler and self._running:
            self._scheduler.shutdown(wait=False)
            self._running = False
            logger.info("Scheduler stopped.")

    # ------------------------------------------------------------------ #
    # Manual execution                                                     #
    # ------------------------------------------------------------------ #

    def run_job(self, job_id: str) -> bool:
        """Manually trigger a job by ID. Returns True if found and run."""
        job = self._jobs.get(job_id)
        if job is None:
            logger.warning("Job '%s' not found.", job_id)
            return False
        job.run()
        return True

    def run_all(self) -> None:
        """Manually trigger all registered jobs in sequence."""
        for job in list(self._jobs.values()):
            job.run()

    # ------------------------------------------------------------------ #
    # Introspection                                                        #
    # ------------------------------------------------------------------ #

    def list_jobs(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [j.to_dict() for j in self._jobs.values()]

    @property
    def is_running(self) -> bool:
        return self._running

    def __repr__(self) -> str:
        return (
            f"<Scheduler running={self._running} jobs={list(self._jobs.keys())}>"
        )
