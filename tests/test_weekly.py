from datetime import date

import pytest

from tayyib import alerts, universe, weekly
from tayyib.storage import persistence
from tayyib.storage.models import PipelineRun, TargetPortfolio
from tayyib.universe import UniverseResolutionError, resolve_universe


def target(rank, ticker, score=0.1, weight=0.5):
    return TargetPortfolio(
        pipeline_run_id=1, target_date=date.today(), ticker=ticker, rank=rank,
        score=score, weight=weight,
    )  # fmt: skip


def test_free_plan_source_reads_its_file(tmp_path, monkeypatch):
    path = tmp_path / "free.csv"
    path.write_text("aapl\nxom\n")
    monkeypatch.setattr(universe, "FREE_PLAN_CONSTITUENTS_PATH", path)
    assert resolve_universe("free-plan") == ["AAPL", "XOM"]


def test_free_plan_source_missing_file_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(universe, "FREE_PLAN_CONSTITUENTS_PATH", tmp_path / "none.csv")
    with pytest.raises(UniverseResolutionError):
        resolve_universe("free-plan")


def test_summary_shows_entries_and_exits():
    text = alerts.format_weekly_summary([target(1, "AAA"), target(2, "BBB")], ["BBB", "CCC"])
    assert "1. AAA" in text and "2. BBB" in text
    assert "Entered AAA" in text and "Left CCC" in text


def test_summary_first_run_and_empty():
    first = alerts.format_weekly_summary([target(1, "AAA")], None)
    assert "First run" in first
    assert "No compliant ticker" in alerts.format_weekly_summary([], ["AAA"])


def test_previous_targets_ignore_incomplete_runs(session):
    done = persistence.start_pipeline_run("ranking", session=session)
    session.add(TargetPortfolio(pipeline_run_id=done.id, target_date=date.today(),
                                ticker="OLD", rank=1, score=0.1, weight=1.0))  # fmt: skip
    session.commit()
    persistence.complete_pipeline_run(done.id, session=session)
    failed = persistence.start_pipeline_run("ranking", session=session)
    persistence.fail_pipeline_run(failed.id, "x", session=session)
    current = persistence.start_pipeline_run("ranking", session=session)
    assert persistence.previous_target_tickers(current.id, session=session) == ["OLD"]
    assert persistence.previous_target_tickers(done.id, session=session) is None


def fake_run(status, run_id=1):
    return PipelineRun(id=run_id, step_name="x", status=status, started_at=None)


def test_incomplete_screening_skips_ranking_and_summary(monkeypatch):
    monkeypatch.setattr(weekly, "resolve_universe", lambda: ["AAA"])
    monkeypatch.setattr(
        weekly, "run_screening_pipeline", lambda t, session=None: fake_run("incomplete")
    )
    monkeypatch.setattr(
        weekly, "run_ranking_pipeline", lambda session=None: pytest.fail("no ranking")
    )
    monkeypatch.setattr(alerts, "send_telegram_message", lambda t: pytest.fail("no summary"))
    screening, ranking = weekly.run_weekly()
    assert screening.status == "incomplete" and ranking is None


def test_completed_ranking_sends_summary(monkeypatch):
    sent = []
    monkeypatch.setattr(weekly, "resolve_universe", lambda: ["AAA"])
    monkeypatch.setattr(
        weekly, "run_screening_pipeline", lambda t, session=None: fake_run("completed")
    )
    monkeypatch.setattr(
        weekly, "run_ranking_pipeline", lambda session=None: fake_run("completed", 2)
    )
    monkeypatch.setattr(
        persistence, "current_targets", lambda rid, session=None: [target(1, "AAA")]
    )
    monkeypatch.setattr(persistence, "previous_target_tickers", lambda rid, session=None: None)
    monkeypatch.setattr(alerts, "send_telegram_message", lambda t: sent.append(t) or True)
    weekly.run_weekly()
    assert len(sent) == 1 and "AAA" in sent[0]


def test_incomplete_ranking_sends_no_summary(monkeypatch):
    monkeypatch.setattr(weekly, "resolve_universe", lambda: ["AAA"])
    monkeypatch.setattr(
        weekly, "run_screening_pipeline", lambda t, session=None: fake_run("completed")
    )
    monkeypatch.setattr(
        weekly, "run_ranking_pipeline", lambda session=None: fake_run("incomplete", 2)
    )
    monkeypatch.setattr(alerts, "send_telegram_message", lambda t: pytest.fail("no summary"))
    weekly.run_weekly()
