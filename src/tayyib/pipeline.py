from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlmodel import Session

from tayyib import alerts
from tayyib.config import settings
from tayyib.data import fmp
from tayyib.data.fmp import FmpRequestError
from tayyib.ranking import (
    INSUFFICIENT_PRICE_HISTORY,
    PRICE_DATA_FETCH_FAILED,
    MomentumScore,
    momentum_score,
    select_top,
)
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
        failed_run = persistence.fail_pipeline_run(run.id, reason=str(exc), session=session)
        alerts.send_telegram_message(alerts.format_failure_alert(failed_run))
        return failed_run

    return persistence.complete_pipeline_run(run.id, session=session)


PRICE_WINDOW_DAYS = 260


def run_ranking_pipeline(session: Session | None = None) -> PipelineRun:
    run = persistence.start_pipeline_run("ranking", session=session)
    today = datetime.now(UTC).date()
    from_date = today - timedelta(days=PRICE_WINDOW_DAYS)

    try:
        tickers = persistence.latest_compliant_tickers(session=session)
        scores: list[MomentumScore] = []
        for ticker in tickers:
            try:
                rows = fmp.fetch_adjusted_closes(ticker, from_date)
            except FmpRequestError:
                item = MomentumScore(ticker, None, PRICE_DATA_FETCH_FAILED)
            else:
                value = momentum_score(
                    [close for _, close in rows], settings.momentum_lookback_days
                )
                if value is None:
                    item = MomentumScore(ticker, None, INSUFFICIENT_PRICE_HISTORY)
                else:
                    item = MomentumScore(ticker, value)
            scores.append(item)
            persistence.persist_factor_score(run.id, today, item, session=session)

        for entry in select_top(scores, settings.top_n_tickers):
            persistence.persist_target(run.id, today, entry, session=session)
    except Exception as exc:
        failed_run = persistence.fail_pipeline_run(run.id, reason=str(exc), session=session)
        alerts.send_telegram_message(alerts.format_failure_alert(failed_run))
        return failed_run

    return persistence.complete_pipeline_run(run.id, session=session)
