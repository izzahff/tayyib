from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from tayyib.config import settings
from tayyib.data.fmp import FinancialStatementFigures

DEBT_RATIO_EXCEEDED = "debt ratio exceeded"
NON_PERMISSIBLE_INCOME_EXCEEDED = "non-permissible income exceeded"
INSUFFICIENT_DEBT_RATIO_DATA = "insufficient data for debt ratio calculation"
INSUFFICIENT_NON_PERMISSIBLE_INCOME_DATA = (
    "insufficient data for non-permissible income calculation"
)
REVENUE_ZERO = "revenue is zero, cannot compute non-permissible income ratio"

Classification = Literal["compliant", "non-compliant", "unscreened"]


@dataclass(frozen=True)
class AaoifiScreeningResult:
    classification: Classification
    debt_ratio: float | None
    non_permissible_income_ratio: float | None
    reasons: tuple[str, ...] = ()


def screen_aaoifi_compliance(
    figures: FinancialStatementFigures,
    debt_ratio_threshold: float | None = None,
    non_permissible_income_threshold: float | None = None,
) -> AaoifiScreeningResult:
    if debt_ratio_threshold is None:
        debt_ratio_threshold = settings.debt_ratio_threshold
    if non_permissible_income_threshold is None:
        non_permissible_income_threshold = settings.non_permissible_income_threshold

    debt_ratio, debt_ratio_data_reason = _compute_debt_ratio(figures)
    npi_ratio, npi_data_reason = _compute_non_permissible_income_ratio(figures)

    data_reasons = tuple(r for r in (debt_ratio_data_reason, npi_data_reason) if r is not None)
    if data_reasons:
        return AaoifiScreeningResult(
            classification="unscreened",
            debt_ratio=debt_ratio,
            non_permissible_income_ratio=npi_ratio,
            reasons=data_reasons,
        )

    exceed_reasons = []
    if debt_ratio > debt_ratio_threshold:
        exceed_reasons.append(DEBT_RATIO_EXCEEDED)
    if npi_ratio > non_permissible_income_threshold:
        exceed_reasons.append(NON_PERMISSIBLE_INCOME_EXCEEDED)

    return AaoifiScreeningResult(
        classification="compliant" if not exceed_reasons else "non-compliant",
        debt_ratio=debt_ratio,
        non_permissible_income_ratio=npi_ratio,
        reasons=tuple(exceed_reasons),
    )


def _compute_debt_ratio(figures: FinancialStatementFigures) -> tuple[float | None, str | None]:
    if figures.total_assets is None or figures.total_liabilities is None:
        return None, INSUFFICIENT_DEBT_RATIO_DATA
    return figures.total_liabilities / figures.total_assets, None


def _compute_non_permissible_income_ratio(
    figures: FinancialStatementFigures,
) -> tuple[float | None, str | None]:
    if figures.revenue is None or figures.revenue == 0:
        return None, REVENUE_ZERO
    if figures.interest_income is None or figures.other_non_operating_income is None:
        return None, INSUFFICIENT_NON_PERMISSIBLE_INCOME_DATA
    non_permissible_income = figures.interest_income + figures.other_non_operating_income
    return non_permissible_income / figures.revenue, None
