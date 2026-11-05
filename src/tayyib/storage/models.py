from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import ARRAY, JSON, String
from sqlmodel import Field, SQLModel


class PipelineRun(SQLModel, table=True):
    __tablename__ = "pipeline_runs"

    id: int | None = Field(default=None, primary_key=True)
    step_name: str
    status: str = "started"
    started_at: datetime
    completed_at: datetime | None = None
    failure_reason: str | None = None


class ScreeningResult(SQLModel, table=True):
    __tablename__ = "screening_results"

    id: int | None = Field(default=None, primary_key=True)
    pipeline_run_id: int = Field(foreign_key="pipeline_runs.id")
    ticker: str
    screening_date: date
    debt_ratio: float | None = None
    non_permissible_income_ratio: float | None = None
    classification: str
    reasons: list[str] = Field(
        default_factory=list,
        sa_type=ARRAY(String).with_variant(JSON(), "sqlite"),
    )


class FactorScore(SQLModel, table=True):
    __tablename__ = "factor_scores"

    id: int | None = Field(default=None, primary_key=True)
    pipeline_run_id: int = Field(foreign_key="pipeline_runs.id")
    ticker: str
    score_date: date
    factor_name: str = "momentum"
    score: float | None = None
    reason: str | None = None


class TargetPortfolio(SQLModel, table=True):
    __tablename__ = "target_portfolio"

    id: int | None = Field(default=None, primary_key=True)
    pipeline_run_id: int = Field(foreign_key="pipeline_runs.id")
    target_date: date
    ticker: str
    rank: int
    score: float
    weight: float
