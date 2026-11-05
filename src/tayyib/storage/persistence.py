from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, date, datetime

from sqlmodel import Session, select

from tayyib.ranking import MomentumScore, TargetEntry
from tayyib.screening.aaoifi import AaoifiScreeningResult
from tayyib.storage.engine import get_session
from tayyib.storage.models import (
    FactorScore,
    PipelineRun,
    ScreeningResult,
    TargetPortfolio,
)


@contextmanager
def _resolve_session(session: Session | None) -> Iterator[Session]:
    owns_session = session is None
    session = session or get_session()
    try:
        yield session
    finally:
        if owns_session:
            session.close()


def start_pipeline_run(step_name: str, session: Session | None = None) -> PipelineRun:
    with _resolve_session(session) as session:
        run = PipelineRun(step_name=step_name, status="started", started_at=datetime.now(UTC))
        session.add(run)
        session.commit()
        session.refresh(run)
        return run


def complete_pipeline_run(run_id: int, session: Session | None = None) -> PipelineRun:
    with _resolve_session(session) as session:
        run = session.get(PipelineRun, run_id)
        run.status = "completed"
        run.completed_at = datetime.now(UTC)
        session.add(run)
        session.commit()
        session.refresh(run)
        return run


def fail_pipeline_run(run_id: int, reason: str, session: Session | None = None) -> PipelineRun:
    with _resolve_session(session) as session:
        run = session.get(PipelineRun, run_id)
        run.status = "incomplete"
        run.completed_at = datetime.now(UTC)
        run.failure_reason = reason
        session.add(run)
        session.commit()
        session.refresh(run)
        return run


def persist_screening_result(
    run_id: int,
    ticker: str,
    screening_date: date,
    result: AaoifiScreeningResult,
    session: Session | None = None,
) -> ScreeningResult:
    with _resolve_session(session) as session:
        row = ScreeningResult(
            pipeline_run_id=run_id,
            ticker=ticker,
            screening_date=screening_date,
            debt_ratio=result.debt_ratio,
            non_permissible_income_ratio=result.non_permissible_income_ratio,
            classification=result.classification,
            reasons=list(result.reasons),
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return row


def latest_compliant_tickers(session: Session | None = None) -> list[str]:
    with _resolve_session(session) as session:
        run = session.exec(
            select(PipelineRun)
            .where(PipelineRun.step_name == "screening", PipelineRun.status == "completed")
            .order_by(PipelineRun.id.desc())
        ).first()
        if run is None:
            raise LookupError("no completed screening run found")
        rows = session.exec(
            select(ScreeningResult).where(
                ScreeningResult.pipeline_run_id == run.id,
                ScreeningResult.classification == "compliant",
            )
        ).all()
        return sorted(row.ticker for row in rows)


def persist_factor_score(
    run_id: int, score_date: date, item: MomentumScore, session: Session | None = None
) -> FactorScore:
    with _resolve_session(session) as session:
        row = FactorScore(
            pipeline_run_id=run_id,
            ticker=item.ticker,
            score_date=score_date,
            score=item.score,
            reason=item.reason,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return row


def persist_target(
    run_id: int, target_date: date, entry: TargetEntry, session: Session | None = None
) -> TargetPortfolio:
    with _resolve_session(session) as session:
        row = TargetPortfolio(
            pipeline_run_id=run_id,
            target_date=target_date,
            ticker=entry.ticker,
            rank=entry.rank,
            score=entry.score,
            weight=entry.weight,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return row
