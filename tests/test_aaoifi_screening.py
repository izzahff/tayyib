import pytest

from tayyib.data.fmp import FinancialStatementFigures
from tayyib.screening import aaoifi
from tayyib.screening.aaoifi import (
    DEBT_RATIO_EXCEEDED,
    INSUFFICIENT_DEBT_RATIO_DATA,
    INSUFFICIENT_NON_PERMISSIBLE_INCOME_DATA,
    NON_PERMISSIBLE_INCOME_EXCEEDED,
    REVENUE_ZERO,
    screen_aaoifi_compliance,
)


def make_figures(
    total_assets=1000.0,
    total_liabilities=200.0,
    revenue=1000.0,
    interest_income=10.0,
    other_non_operating_income=5.0,
) -> FinancialStatementFigures:
    return FinancialStatementFigures(
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        revenue=revenue,
        interest_income=interest_income,
        other_non_operating_income=other_non_operating_income,
    )


# 4.1 Debt ratio: below, at, above threshold


def test_debt_ratio_below_threshold_passes():
    figures = make_figures(total_assets=1000.0, total_liabilities=200.0)  # 20%
    result = screen_aaoifi_compliance(
        figures, debt_ratio_threshold=0.30, non_permissible_income_threshold=1.0
    )
    assert result.classification == "compliant"
    assert result.debt_ratio == pytest.approx(0.20)


def test_debt_ratio_above_threshold_fails():
    figures = make_figures(total_assets=1000.0, total_liabilities=400.0)  # 40%
    result = screen_aaoifi_compliance(
        figures, debt_ratio_threshold=0.30, non_permissible_income_threshold=1.0
    )
    assert result.classification == "non-compliant"
    assert result.reasons == (DEBT_RATIO_EXCEEDED,)


def test_debt_ratio_equal_to_threshold_passes():
    figures = make_figures(total_assets=1000.0, total_liabilities=300.0)  # 30%
    result = screen_aaoifi_compliance(
        figures, debt_ratio_threshold=0.30, non_permissible_income_threshold=1.0
    )
    assert result.classification == "compliant"


# 4.2 Non-permissible income ratio: below, at, above threshold


def test_npi_below_threshold_passes():
    figures = make_figures(revenue=1000.0, interest_income=20.0, other_non_operating_income=10.0)
    result = screen_aaoifi_compliance(
        figures, debt_ratio_threshold=1.0, non_permissible_income_threshold=0.05
    )
    assert result.classification == "compliant"
    assert result.non_permissible_income_ratio == pytest.approx(0.03)


def test_npi_above_threshold_fails():
    figures = make_figures(revenue=1000.0, interest_income=50.0, other_non_operating_income=30.0)
    result = screen_aaoifi_compliance(
        figures, debt_ratio_threshold=1.0, non_permissible_income_threshold=0.05
    )
    assert result.classification == "non-compliant"
    assert result.reasons == (NON_PERMISSIBLE_INCOME_EXCEEDED,)


def test_npi_equal_to_threshold_passes():
    figures = make_figures(revenue=1000.0, interest_income=30.0, other_non_operating_income=20.0)
    result = screen_aaoifi_compliance(
        figures, debt_ratio_threshold=1.0, non_permissible_income_threshold=0.05
    )
    assert result.classification == "compliant"


# 4.3 Overall compliance: pass both, fail one, fail both


def test_passes_both_ratios_is_compliant():
    figures = make_figures(
        total_assets=1000.0,
        total_liabilities=200.0,
        revenue=1000.0,
        interest_income=10.0,
        other_non_operating_income=5.0,
    )
    result = screen_aaoifi_compliance(
        figures, debt_ratio_threshold=0.30, non_permissible_income_threshold=0.05
    )
    assert result.classification == "compliant"
    assert result.reasons == ()


def test_fails_debt_ratio_only():
    figures = make_figures(
        total_assets=1000.0,
        total_liabilities=400.0,
        revenue=1000.0,
        interest_income=10.0,
        other_non_operating_income=5.0,
    )
    result = screen_aaoifi_compliance(
        figures, debt_ratio_threshold=0.30, non_permissible_income_threshold=0.05
    )
    assert result.classification == "non-compliant"
    assert result.reasons == (DEBT_RATIO_EXCEEDED,)


def test_fails_both_ratios():
    figures = make_figures(
        total_assets=1000.0,
        total_liabilities=400.0,
        revenue=1000.0,
        interest_income=50.0,
        other_non_operating_income=30.0,
    )
    result = screen_aaoifi_compliance(
        figures, debt_ratio_threshold=0.30, non_permissible_income_threshold=0.05
    )
    assert result.classification == "non-compliant"
    assert result.reasons == (DEBT_RATIO_EXCEEDED, NON_PERMISSIBLE_INCOME_EXCEEDED)


# 4.4 Custom thresholds overriding the defaults via Settings


def test_custom_thresholds_from_settings(monkeypatch):
    monkeypatch.setattr(aaoifi.settings, "debt_ratio_threshold", 0.50)
    monkeypatch.setattr(aaoifi.settings, "non_permissible_income_threshold", 0.10)

    figures = make_figures(
        total_assets=1000.0,
        total_liabilities=400.0,
        revenue=1000.0,
        interest_income=50.0,
        other_non_operating_income=30.0,
    )
    result = screen_aaoifi_compliance(figures)
    assert result.classification == "compliant"


# 4.5 Missing/absent figures produce "unscreened" with the correct reason string(s)


def test_missing_balance_sheet_field_is_unscreened_with_debt_ratio_reason():
    figures = make_figures(total_assets=None)
    result = screen_aaoifi_compliance(
        figures, debt_ratio_threshold=0.30, non_permissible_income_threshold=0.05
    )
    assert result.classification == "unscreened"
    assert result.reasons == (INSUFFICIENT_DEBT_RATIO_DATA,)


def test_missing_income_statement_field_is_unscreened_with_npi_reason():
    figures = make_figures(interest_income=None)
    result = screen_aaoifi_compliance(
        figures, debt_ratio_threshold=0.30, non_permissible_income_threshold=0.05
    )
    assert result.classification == "unscreened"
    assert result.reasons == (INSUFFICIENT_NON_PERMISSIBLE_INCOME_DATA,)


# 4.7 None-vs-0 distinction: a field present as 0 is screened normally


def test_zero_interest_income_is_screened_normally_not_treated_as_missing():
    figures = make_figures(interest_income=0.0, other_non_operating_income=0.0, revenue=1000.0)
    result = screen_aaoifi_compliance(
        figures, debt_ratio_threshold=0.30, non_permissible_income_threshold=0.05
    )
    assert result.classification == "compliant"
    assert result.non_permissible_income_ratio == pytest.approx(0.0)


def test_zero_total_liabilities_is_screened_normally_not_treated_as_missing():
    figures = make_figures(total_liabilities=0.0)
    result = screen_aaoifi_compliance(
        figures, debt_ratio_threshold=0.30, non_permissible_income_threshold=0.05
    )
    assert result.classification == "compliant"
    assert result.debt_ratio == pytest.approx(0.0)


# 4.8 revenue None and revenue == 0 both produce "unscreened" with REVENUE_ZERO;
# both reasons reported when both sides are missing


def test_revenue_none_is_unscreened_with_revenue_zero_reason():
    figures = make_figures(revenue=None)
    result = screen_aaoifi_compliance(
        figures, debt_ratio_threshold=0.30, non_permissible_income_threshold=0.05
    )
    assert result.classification == "unscreened"
    assert result.reasons == (REVENUE_ZERO,)


def test_revenue_zero_is_unscreened_with_revenue_zero_reason():
    figures = make_figures(revenue=0.0)
    result = screen_aaoifi_compliance(
        figures, debt_ratio_threshold=0.30, non_permissible_income_threshold=0.05
    )
    assert result.classification == "unscreened"
    assert result.reasons == (REVENUE_ZERO,)


def test_revenue_none_reason_independent_of_interest_income_state():
    figures = make_figures(revenue=None, interest_income=None, other_non_operating_income=None)
    result = screen_aaoifi_compliance(
        figures, debt_ratio_threshold=0.30, non_permissible_income_threshold=0.05
    )
    assert result.classification == "unscreened"
    assert result.reasons == (REVENUE_ZERO,)


def test_both_balance_sheet_and_income_statement_data_missing_reports_both_reasons():
    figures = make_figures(total_assets=None, interest_income=None)
    result = screen_aaoifi_compliance(
        figures, debt_ratio_threshold=0.30, non_permissible_income_threshold=0.05
    )
    assert result.classification == "unscreened"
    assert result.reasons == (
        INSUFFICIENT_DEBT_RATIO_DATA,
        INSUFFICIENT_NON_PERMISSIBLE_INCOME_DATA,
    )


def test_both_balance_sheet_and_revenue_missing_reports_both_reasons():
    figures = make_figures(total_liabilities=None, revenue=None)
    result = screen_aaoifi_compliance(
        figures, debt_ratio_threshold=0.30, non_permissible_income_threshold=0.05
    )
    assert result.classification == "unscreened"
    assert result.reasons == (INSUFFICIENT_DEBT_RATIO_DATA, REVENUE_ZERO)
