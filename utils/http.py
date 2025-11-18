from __future__ import annotations

import asyncio
from typing import Optional
from aiohttp import ClientSession, ClientTimeout
import aiohttp
import logging

logger = logging.getLogger(__name__)


async def fetch_text(
    session: ClientSession,
    url: str,
    *,
    timeout: float = 15.0,
    user_agent: Optional[str] = None,
    retries: int = 2,
) -> Optional[str]:
    """
    Fetch a URL and return body text. Returns None on failure after retries.
    """
    headers = {}
    if user_agent:
        headers["User-Agent"] = user_agent

    last_exc: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            async with session.get(url, headers=headers, timeout=ClientTimeout(total=timeout)) as resp:
                resp.raise_for_status()
                return await resp.text()
        except Exception as exc:  # broad catch to keep crawler moving
            last_exc = exc
            logger.debug("fetch_text attempt %s failed for %s: %r", attempt + 1, url, exc)
            await asyncio.sleep(min(2 ** attempt, 5))
    logger.warning("fetch_text failed for %s after %s attempts: %r", url, retries + 1, last_exc)
    return None


def create_session() -> ClientSession:
    """
    Create a shared aiohttp ClientSession.
    """
    # Note: caller is responsible for closing the session (await session.close()).
    connector = aiohttp.TCPConnector(limit=0)  # unlimited; concurrency managed via semaphore
    return aiohttp.ClientSession(connector=connector)
