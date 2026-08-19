import pytest
from sqlmodel import select

from tayyib.data import fmp as fmp_module
from tayyib.data.fmp import FinancialStatementFigures, FmpRequestError
from tayyib.pipeline import run_screening_pipeline
from tayyib.screening.aaoifi import FINANCIAL_DATA_FETCH_FAILED
from tayyib.storage import persistence as persistence_module
from tayyib.storage.models import PipelineRun, ScreeningResult

COMPLIANT_FIGURES = FinancialStatementFigures(
    total_assets=1000.0,
    total_liabilities=200.0,
    revenue=1000.0,
    interest_income=10.0,
    other_non_operating_income=5.0,
)

NON_COMPLIANT_FIGURES = FinancialStatementFigures(
    total_assets=1000.0,
    total_liabilities=400.0,
    revenue=1000.0,
    interest_income=50.0,
    other_non_operating_income=30.0,
)

MISSING_FIELD_FIGURES = FinancialStatementFigures(
    total_assets=None,
    total_liabilities=200.0,
    revenue=1000.0,
    interest_income=10.0,
    other_non_operating_income=5.0,
)


def fetch_from_map(figures_by_ticker):
    def _fetch(ticker):
        value = figures_by_ticker[ticker]
        if isinstance(value, Exception):
            raise value
        return value

    return _fetch


def results_for_run(session, run_id):
    return session.exec(
        select(ScreeningResult).where(ScreeningResult.pipeline_run_id == run_id)
    ).all()


# 6.1


def test_pipeline_persists_one_result_per_ticker_and_completes(session, monkeypatch):
    figures_by_ticker = {
        "AAA": COMPLIANT_FIGURES,
        "BBB": NON_COMPLIANT_FIGURES,
        "CCC": MISSING_FIELD_FIGURES,
    }
    monkeypatch.setattr(
        fmp_module, "fetch_financial_statement_figures", fetch_from_map(figures_by_ticker)
    )

    run = run_screening_pipeline(["AAA", "BBB", "CCC"], session=session)

    assert run.status == "completed"
    results = results_for_run(session, run.id)
    by_ticker = {r.ticker: r for r in results}
    assert set(by_ticker) == {"AAA", "BBB", "CCC"}
    assert by_ticker["AAA"].classification == "compliant"
    assert by_ticker["BBB"].classification == "non-compliant"
    assert by_ticker["CCC"].classification == "unscreened"


# 6.2


def test_one_ticker_fetch_failure_does_not_abort_run(session, monkeypatch):
    figures_by_ticker = {
        "AAA": COMPLIANT_FIGURES,
        "BBB": FmpRequestError("network error"),
        "CCC": NON_COMPLIANT_FIGURES,
    }
    monkeypatch.setattr(
        fmp_module, "fetch_financial_statement_figures", fetch_from_map(figures_by_ticker)
    )

    run = run_screening_pipeline(["AAA", "BBB", "CCC"], session=session)

    assert run.status == "completed"
    results = results_for_run(session, run.id)
    assert {r.ticker for r in results} == {"AAA", "BBB", "CCC"}


# 6.3


def test_fetch_failed_ticker_persisted_as_unscreened_with_fetch_failed_reason(
    session, monkeypatch
):
    monkeypatch.setattr(
        fmp_module,
        "fetch_financial_statement_figures",
        fetch_from_map({"AAA": FmpRequestError("boom")}),
    )

    run = run_screening_pipeline(["AAA"], session=session)

    result = results_for_run(session, run.id)[0]
    assert result.classification == "unscreened"
    assert result.debt_ratio is None
    assert result.non_permissible_income_ratio is None
    assert result.reasons == [FINANCIAL_DATA_FETCH_FAILED]


# 6.4


def test_all_tickers_fetch_failing_still_completes_run(session, monkeypatch):
    monkeypatch.setattr(
        fmp_module,
        "fetch_financial_statement_figures",
        fetch_from_map(
            {
                "AAA": FmpRequestError("boom"),
                "BBB": FmpRequestError("boom2"),
            }
        ),
    )

    run = run_screening_pipeline(["AAA", "BBB"], session=session)

    assert run.status == "completed"
    results = results_for_run(session, run.id)
    assert len(results) == 2
    assert all(
        r.classification == "unscreened" and r.reasons == [FINANCIAL_DATA_FETCH_FAILED]
        for r in results
    )


# 6.5


def test_pipeline_wide_persistence_failure_marks_run_incomplete(session, monkeypatch):
    monkeypatch.setattr(
        fmp_module,
        "fetch_financial_statement_figures",
        fetch_from_map(
            {
                "AAA": COMPLIANT_FIGURES,
                "BBB": COMPLIANT_FIGURES,
                "CCC": COMPLIANT_FIGURES,
            }
        ),
    )

    original_persist = persistence_module.persist_screening_result
    call_count = {"n": 0}

    def flaky_persist(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 2:
            raise RuntimeError("db hiccup")
        return original_persist(*args, **kwargs)

    monkeypatch.setattr(persistence_module, "persist_screening_result", flaky_persist)

    run = run_screening_pipeline(["AAA", "BBB", "CCC"], session=session)

    assert run.status == "incomplete"
    assert run.failure_reason == "db hiccup"
    results = results_for_run(session, run.id)
    assert len(results) == 1
    assert results[0].ticker == "AAA"


# 6.6


def test_empty_ticker_list_completes_immediately_with_no_results(session):
    run = run_screening_pipeline([], session=session)

    assert run.status == "completed"
    assert results_for_run(session, run.id) == []


# 6.7


def test_all_persisted_results_reference_the_run_id(session, monkeypatch):
    monkeypatch.setattr(
        fmp_module,
        "fetch_financial_statement_figures",
        fetch_from_map({"AAA": COMPLIANT_FIGURES, "BBB": NON_COMPLIANT_FIGURES}),
    )

    run = run_screening_pipeline(["AAA", "BBB"], session=session)

    results = results_for_run(session, run.id)
    assert len(results) == 2
    assert all(r.pipeline_run_id == run.id for r in results)


# 6.8


def test_start_pipeline_run_failure_propagates_and_creates_no_row(session, monkeypatch):
    def broken_start(*args, **kwargs):
        raise RuntimeError("cannot connect")

    monkeypatch.setattr(persistence_module, "start_pipeline_run", broken_start)

    with pytest.raises(RuntimeError, match="cannot connect"):
        run_screening_pipeline(["AAA"], session=session)

    assert session.exec(select(PipelineRun)).all() == []
