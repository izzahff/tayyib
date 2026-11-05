import httpx
import pytest

from tayyib import alerts
from tayyib.config import settings
from tayyib.data import fmp as fmp_module
from tayyib.pipeline import run_screening_pipeline
from tayyib.storage import persistence as persistence_module
from tayyib.storage.models import PipelineRun
from tests.test_pipeline import COMPLIANT_FIGURES, fetch_from_map


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", "123:ABC")
    monkeypatch.setattr(settings, "telegram_chat_id", "42")


class FakeResponse:
    def __init__(self, ok=True):
        self.ok = ok

    def raise_for_status(self):
        if not self.ok:
            raise httpx.HTTPStatusError("bad", request=None, response=None)


def test_message_is_posted_to_telegram(configured, monkeypatch):
    calls = []

    def fake_post(url, json, timeout):
        calls.append((url, json, timeout))
        return FakeResponse()

    monkeypatch.setattr(alerts.httpx, "post", fake_post)
    assert alerts.send_telegram_message("hello") is True
    url, body, _ = calls[0]
    assert url == "https://api.telegram.org/bot123:ABC/sendMessage"
    assert body == {"chat_id": "42", "text": "hello"}


def test_http_error_returns_false(configured, monkeypatch):
    monkeypatch.setattr(alerts.httpx, "post", lambda *a, **k: FakeResponse(ok=False))
    assert alerts.send_telegram_message("x") is False


def test_network_error_returns_false(configured, monkeypatch):
    def boom(*a, **k):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(alerts.httpx, "post", boom)
    assert alerts.send_telegram_message("x") is False


def test_empty_token_makes_no_request(monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", "")
    monkeypatch.setattr(settings, "telegram_chat_id", "42")

    def fail(*a, **k):
        raise AssertionError("no request expected")

    monkeypatch.setattr(alerts.httpx, "post", fail)
    assert alerts.send_telegram_message("x") is False


def test_failure_alert_contains_run_details():
    run = PipelineRun(id=7, step_name="screening", status="incomplete", failure_reason="db down")
    text = alerts.format_failure_alert(run)
    assert "7" in text and "screening" in text and "db down" in text


def _break_second_persist(monkeypatch):
    original = persistence_module.persist_screening_result
    count = {"n": 0}

    def flaky(*args, **kwargs):
        count["n"] += 1
        if count["n"] == 2:
            raise RuntimeError("db hiccup")
        return original(*args, **kwargs)

    monkeypatch.setattr(persistence_module, "persist_screening_result", flaky)


def _fetch_all_compliant(monkeypatch):
    monkeypatch.setattr(
        fmp_module,
        "fetch_financial_statement_figures",
        fetch_from_map({"AAA": COMPLIANT_FIGURES, "BBB": COMPLIANT_FIGURES}),
    )


def test_pipeline_failure_sends_one_alert(session, monkeypatch):
    _fetch_all_compliant(monkeypatch)
    _break_second_persist(monkeypatch)
    sent = []
    monkeypatch.setattr(alerts, "send_telegram_message", lambda text: sent.append(text) or True)
    run = run_screening_pipeline(["AAA", "BBB"], session=session)
    assert run.status == "incomplete"
    assert len(sent) == 1 and "db hiccup" in sent[0]


def test_failed_alert_send_keeps_run_incomplete(session, monkeypatch, configured):
    _fetch_all_compliant(monkeypatch)
    _break_second_persist(monkeypatch)

    def boom(*a, **k):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(alerts.httpx, "post", boom)
    run = run_screening_pipeline(["AAA", "BBB"], session=session)
    assert run.status == "incomplete"
    assert run.failure_reason == "db hiccup"


def test_successful_run_sends_no_alert(session, monkeypatch):
    _fetch_all_compliant(monkeypatch)
    sent = []
    monkeypatch.setattr(alerts, "send_telegram_message", lambda text: sent.append(text) or True)
    run = run_screening_pipeline(["AAA", "BBB"], session=session)
    assert run.status == "completed"
    assert sent == []
