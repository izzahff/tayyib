from __future__ import annotations

import httpx

from tayyib.config import settings
from tayyib.storage.models import PipelineRun

TELEGRAM_TIMEOUT_SECONDS = 10.0


def send_telegram_message(text: str) -> bool:
    token = settings.telegram_bot_token
    chat_id = settings.telegram_chat_id
    if not token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        response = httpx.post(
            url,
            json={"chat_id": chat_id, "text": text},
            timeout=TELEGRAM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        return False
    return True


def format_failure_alert(run: PipelineRun) -> str:
    return f"Tayyib pipeline run {run.id} failed\nStep {run.step_name}\nReason {run.failure_reason}"
