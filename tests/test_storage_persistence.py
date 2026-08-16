from datetime import date

from tayyib.screening.aaoifi import (
    DEBT_RATIO_EXCEEDED,
    NON_PERMISSIBLE_INCOME_EXCEEDED,
    REVENUE_ZERO,
    AaoifiScreeningResult,
)
from tayyib.storage.persistence import (
    complete_pipeline_run,
    fail_pipeline_run,
    persist_screening_result,
    start_pipeline_run,
)


def make_result(
    classification="compliant",
    debt_ratio=0.2,
    non_permissible_income_ratio=0.03,
    reasons=(),
) -> AaoifiScreeningResult:
    return AaoifiScreeningResult(
        classification=classification,
        debt_ratio=debt_ratio,
        non_permissible_income_ratio=non_permissible_income_ratio,
        reasons=tuple(reasons),
    )


# 5.2 start_pipeline_run


def test_start_pipeline_run_records_step_name_status_and_start_time(session):
    run = start_pipeline_run("screening", session=session)
    assert run.step_name == "screening"
    assert run.status == "started"
    assert run.started_at is not None
    assert run.id is not None


# 5.3 complete_pipeline_run


def test_complete_pipeline_run_sets_completed_status_and_timestamp(session):
    run = start_pipeline_run("screening", session=session)
    completed = complete_pipeline_run(run.id, session=session)
    assert completed.status == "completed"
    assert completed.completed_at is not None


# 5.4 fail_pipeline_run


def test_fail_pipeline_run_sets_incomplete_status_timestamp_and_reason(session):
    run = start_pipeline_run("screening", session=session)
    failed = fail_pipeline_run(run.id, "FMP API unreachable", session=session)
    assert failed.status == "incomplete"
    assert failed.completed_at is not None
    assert failed.failure_reason == "FMP API unreachable"


# 5.5 arbitrary step name works identically


def test_pipeline_run_tracking_works_for_arbitrary_step_name(session):
    run = start_pipeline_run("ranking", session=session)
    assert run.step_name == "ranking"
    completed = complete_pipeline_run(run.id, session=session)
    assert completed.status == "completed"


# 5.6 compliant result persisted


def test_persist_compliant_result(session):
    run = start_pipeline_run("screening", session=session)
    result = make_result(
        classification="compliant", debt_ratio=0.2, non_permissible_income_ratio=0.03
    )
    row = persist_screening_result(run.id, "AAPL", date(2026, 8, 16), result, session=session)
    assert row.classification == "compliant"
    assert row.debt_ratio == 0.2
    assert row.non_permissible_income_ratio == 0.03
    assert row.reasons == []


# 5.7 non-compliant result persisted with reasons


def test_persist_non_compliant_result_with_reasons(session):
    run = start_pipeline_run("screening", session=session)
    result = make_result(
        classification="non-compliant",
        debt_ratio=0.4,
        non_permissible_income_ratio=0.08,
        reasons=(DEBT_RATIO_EXCEEDED, NON_PERMISSIBLE_INCOME_EXCEEDED),
    )
    row = persist_screening_result(run.id, "XYZ", date(2026, 8, 16), result, session=session)
    assert row.classification == "non-compliant"
    assert row.reasons == [DEBT_RATIO_EXCEEDED, NON_PERMISSIBLE_INCOME_EXCEEDED]


# 5.8 unscreened result with partial ratio persisted, not nulled to both


def test_persist_unscreened_result_keeps_computed_ratio(session):
    run = start_pipeline_run("screening", session=session)
    result = AaoifiScreeningResult(
        classification="unscreened",
        debt_ratio=0.2,
        non_permissible_income_ratio=None,
        reasons=(REVENUE_ZERO,),
    )
    row = persist_screening_result(run.id, "ABC", date(2026, 8, 16), result, session=session)
    assert row.classification == "unscreened"
    assert row.debt_ratio == 0.2
    assert row.non_permissible_income_ratio is None
    assert row.reasons == [REVENUE_ZERO]


# 5.9 result references its pipeline run's id


def test_persisted_result_references_pipeline_run_id(session):
    run = start_pipeline_run("screening", session=session)
    result = make_result()
    row = persist_screening_result(run.id, "AAPL", date(2026, 8, 16), result, session=session)
    assert row.pipeline_run_id == run.id


# 5.10 results across two separate runs remain distinct, no overwrite


def test_results_across_two_runs_remain_distinct(session):
    run1 = start_pipeline_run("screening", session=session)
    result1 = make_result(debt_ratio=0.2, non_permissible_income_ratio=0.03)
    row1 = persist_screening_result(run1.id, "AAPL", date(2026, 8, 9), result1, session=session)

    run2 = start_pipeline_run("screening", session=session)
    result2 = make_result(debt_ratio=0.25, non_permissible_income_ratio=0.04)
    row2 = persist_screening_result(run2.id, "AAPL", date(2026, 8, 16), result2, session=session)

    assert row1.id != row2.id
    assert row1.pipeline_run_id == run1.id
    assert row2.pipeline_run_id == run2.id
    assert row1.debt_ratio == 0.2
    assert row2.debt_ratio == 0.25
