import httpx

from core.config import settings
from core.logging import log


def notify_task_submitted(task_id: str, submitted_by: str | None, submitter_ip: str | None):
    """Fire-and-forget Discord alert. Never raises — a notification failure
    must never break task submission."""
    if not settings.discord_webhook_url:
        return

    content = (
        f"**New task submitted**\n"
        f"Task ID: `{task_id}`\n"
        f"Submitted by: `{submitted_by or 'anonymous'}`\n"
        f"IP: `{submitter_ip or 'unknown'}`"
    )
    try:
        httpx.post(settings.discord_webhook_url, json={"content": content}, timeout=5)
    except Exception as e:
        log.warning("discord_notify_failed", error=str(e))