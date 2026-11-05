from __future__ import annotations

from sqlmodel import Session

from tayyib import alerts
from tayyib.pipeline import run_ranking_pipeline, run_screening_pipeline
from tayyib.storage import persistence
from tayyib.storage.models import PipelineRun
from tayyib.universe import resolve_universe


def run_weekly(
    session: Session | None = None,
) -> tuple[PipelineRun, PipelineRun | None]:
    """Screen the universe, rank compliant tickers, then send the summary.

    Ranking runs only if screening completed. The summary is sent only if ranking completed.
    """
    screening = run_screening_pipeline(resolve_universe(), session=session)
    if screening.status != "completed":
        return screening, None

    ranking = run_ranking_pipeline(session=session)
    if ranking.status == "completed":
        targets = persistence.current_targets(ranking.id, session=session)
        previous = persistence.previous_target_tickers(ranking.id, session=session)
        alerts.send_telegram_message(alerts.format_weekly_summary(targets, previous))
    return screening, ranking


def main() -> None:
    screening, ranking = run_weekly()
    print(f"Screening run {screening.id} {screening.status}")
    if ranking is not None:
        print(f"Ranking run {ranking.id} {ranking.status}")


if __name__ == "__main__":
    main()
