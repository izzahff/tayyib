from __future__ import annotations

import httpx

from tayyib.config import settings
from tayyib.storage.models import PipelineRun, TargetPortfolio

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


def format_weekly_summary(
    targets: list[TargetPortfolio], previous_tickers: list[str] | None
) -> str:
    if not targets:
        return "Tayyib weekly summary\nNo compliant ticker could be ranked this week."

    lines = ["Tayyib weekly summary", "Top momentum picks among compliant stocks"]
    for target in targets:
        lines.append(
            f"{target.rank}. {target.ticker} score {target.score * 100:.1f}% "
            f"weight {target.weight * 100:.1f}%"
        )

    current = {target.ticker for target in targets}
    if previous_tickers is None:
        lines.append("First run, so there is no previous list to compare.")
    else:
        previous = set(previous_tickers)
        entered = sorted(current - previous)
        left = sorted(previous - current)
        lines.append("Entered " + (", ".join(entered) if entered else "none"))
        lines.append("Left " + (", ".join(left) if left else "none"))
    lines.append("Alert only. Check each stock yourself before you trade.")
    return "\n".join(lines)
