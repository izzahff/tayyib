from datetime import date

import pytest
from sqlmodel import select

from tayyib import alerts
from tayyib.config import settings
from tayyib.data import fmp as fmp_module
from tayyib.data.fmp import FmpRequestError, parse_adjusted_closes
from tayyib.pipeline import run_ranking_pipeline
from tayyib.ranking import MomentumScore, momentum_score, select_top
from tayyib.screening.aaoifi import AaoifiScreeningResult
from tayyib.storage import persistence
from tayyib.storage import persistence as persistence_module
from tayyib.storage.models import FactorScore, TargetPortfolio


def test_score_is_return_over_lookback():
    closes = [100.0] + [110.0] * 5 + [120.0]
    assert momentum_score(closes, lookback=6) == pytest.approx(0.2)


def test_thin_history_has_no_score():
    assert momentum_score([1.0] * 6, lookback=6) is None


def test_zero_base_has_no_score():
    assert momentum_score([0.0, 5.0], lookback=1) is None


def test_select_top_ranks_and_weights():
    scores = [MomentumScore("A", 0.1), MomentumScore("B", 0.3), MomentumScore("C", 0.2)]
    top = select_top(scores, 2)
    assert [t.ticker for t in top] == ["B", "C"]
    assert [t.rank for t in top] == [1, 2]
    assert all(t.weight == 0.5 for t in top)


def test_fewer_candidates_than_slots_weights_sum_to_one():
    top = select_top(
        [MomentumScore("A", 0.1), MomentumScore("B", 0.2), MomentumScore("X", None, "r")], 10
    )
    assert len(top) == 2
    assert abs(sum(t.weight for t in top) - 1) < 1e-9


def test_tie_breaks_alphabetically():
    top = select_top([MomentumScore("ZZZ", 0.5), MomentumScore("AAA", 0.5)], 1)
    assert top[0].ticker == "AAA"


def test_parser_sorts_oldest_first_and_skips_missing():
    rows = [
        {"symbol": "AAPL", "date": "2026-11-04", "adjClose": 349.51},
        {"symbol": "AAPL", "date": "2026-11-03", "adjClose": 331.9},
        {"symbol": "AAPL", "date": "2026-11-02", "adjClose": None},
    ]
    assert parse_adjusted_closes(rows) == [(date(2026, 11, 3), 331.9), (date(2026, 11, 4), 349.51)]
    assert parse_adjusted_closes({"error": "x"}) == []


def _seed_screening(session, compliant, other=()):
    run = persistence.start_pipeline_run("screening", session=session)
    for t in compliant:
        persistence.persist_screening_result(
            run.id, t, date.today(), AaoifiScreeningResult("compliant", 0.1, 0.01), session=session
        )
    for t in other:
        persistence.persist_screening_result(
            run.id,
            t,
            date.today(),
            AaoifiScreeningResult("non-compliant", 0.5, 0.01, ("x",)),
            session=session,
        )
    persistence.complete_pipeline_run(run.id, session=session)


def _prices(last, first=100.0, n=127):
    closes = [first] + [first] * (n - 2) + [last]
    return [(date(2026, 1, 1), c) for c in closes]


def _patch_prices(monkeypatch, mapping):
    def fetch(ticker, from_date):
        value = mapping[ticker]
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr(fmp_module, "fetch_adjusted_closes", fetch)


def test_ranking_pipeline_end_to_end(session, monkeypatch):
    monkeypatch.setattr(settings, "top_n_tickers", 2)
    monkeypatch.setattr(settings, "momentum_lookback_days", 126)
    _seed_screening(session, ["AAA", "BBB", "CCC"], other=["NOPE"])
    _patch_prices(monkeypatch, {"AAA": _prices(110), "BBB": _prices(150), "CCC": _prices(130)})
    run = run_ranking_pipeline(session=session)
    assert run.status == "completed"
    targets = session.exec(select(TargetPortfolio).order_by(TargetPortfolio.rank)).all()
    assert [t.ticker for t in targets] == ["BBB", "CCC"]
    scores = session.exec(select(FactorScore)).all()
    assert {s.ticker for s in scores} == {"AAA", "BBB", "CCC"}
    assert all(s.pipeline_run_id == run.id for s in scores)


def test_fetch_failure_and_thin_history_are_recorded_and_run_completes(session, monkeypatch):
    _seed_screening(session, ["AAA", "BBB", "CCC"])
    _patch_prices(
        monkeypatch,
        {"AAA": FmpRequestError("down"), "BBB": _prices(120, n=10), "CCC": _prices(120)},
    )
    run = run_ranking_pipeline(session=session)
    assert run.status == "completed"
    reasons = {s.ticker: s.reason for s in session.exec(select(FactorScore)).all()}
    assert reasons == {
        "AAA": "price data fetch failed",
        "BBB": "insufficient price history",
        "CCC": None,
    }
    assert [t.ticker for t in session.exec(select(TargetPortfolio)).all()] == ["CCC"]


def test_no_screening_run_fails_and_alerts(session, monkeypatch):
    sent = []
    monkeypatch.setattr(alerts, "send_telegram_message", lambda text: sent.append(text) or True)
    run = run_ranking_pipeline(session=session)
    assert run.status == "incomplete"
    assert "no completed screening run" in run.failure_reason
    assert len(sent) == 1


def test_persistence_failure_marks_incomplete_and_alerts(session, monkeypatch):
    _seed_screening(session, ["AAA"])
    _patch_prices(monkeypatch, {"AAA": _prices(120)})
    sent = []
    monkeypatch.setattr(alerts, "send_telegram_message", lambda text: sent.append(text) or True)

    def boom(*a, **k):
        raise RuntimeError("db hiccup")

    monkeypatch.setattr(persistence_module, "persist_factor_score", boom)
    run = run_ranking_pipeline(session=session)
    assert run.status == "incomplete" and run.failure_reason == "db hiccup"
    assert len(sent) == 1


def test_no_scored_tickers_gives_empty_target_list():
    assert select_top([MomentumScore("A", None, "price data fetch failed")], 10) == []
