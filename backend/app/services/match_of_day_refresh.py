"""Background refresh loop for match-of-day cache."""
from __future__ import annotations

import asyncio
import logging

from app.services.match_of_day import MatchOfDayService

logger = logging.getLogger(__name__)

REFRESH_INTERVAL_SECONDS = 900  # 15 minutes

_task: asyncio.Task | None = None


async def _refresh_loop() -> None:
    svc = MatchOfDayService()
    while True:
        try:
            await svc.refresh_cache()
        except Exception:
            logger.exception("Match of day background refresh failed")
        await asyncio.sleep(REFRESH_INTERVAL_SECONDS)


def start_match_of_day_refresh() -> None:
    global _task
    if _task is not None and not _task.done():
        return
    _task = asyncio.create_task(_refresh_loop(), name="match-of-day-refresh")


async def stop_match_of_day_refresh() -> None:
    global _task
    if _task is None:
        return
    _task.cancel()
    try:
        await _task
    except asyncio.CancelledError:
        pass
    _task = None
