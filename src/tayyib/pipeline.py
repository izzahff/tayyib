from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Session

from tayyib.data import fmp
from tayyib.data.fmp import FmpRequestError
from tayyib.screening.aaoifi import (
    FINANCIAL_DATA_FETCH_FAILED,
    AaoifiScreeningResult,
    screen_aaoifi_compliance,
)
from tayyib.storage import persistence
from tayyib.storage.models import PipelineRun


def run_screening_pipeline(tickers: list[str], session: Session | None = None) -> PipelineRun:
    run = persistence.start_pipeline_run("screening", session=session)
    screening_date = datetime.now(UTC).date()

    try:
        for ticker in tickers:
            try:
                figures = fmp.fetch_financial_statement_figures(ticker)
            except FmpRequestError:
                result = AaoifiScreeningResult(
                    classification="unscreened",
                    debt_ratio=None,
                    non_permissible_income_ratio=None,
                    reasons=(FINANCIAL_DATA_FETCH_FAILED,),
                )
            else:
                result = screen_aaoifi_compliance(figures)

            persistence.persist_screening_result(
                run.id, ticker, screening_date, result, session=session
            )
    except Exception as exc:
        return persistence.fail_pipeline_run(run.id, reason=str(exc), session=session)

    return persistence.complete_pipeline_run(run.id, session=session)
