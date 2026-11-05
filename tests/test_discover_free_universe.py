import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "discover", Path(__file__).resolve().parents[1] / "scripts" / "discover_free_universe.py"
)
discover = importlib.util.module_from_spec(spec)
spec.loader.exec_module(discover)


def test_classify_covered():
    assert discover.classify_status(200, [{"symbol": "AAPL"}]) == "covered"


def test_classify_empty_ok_is_unknown():
    assert discover.classify_status(200, []) == "unknown"


def test_classify_not_covered_and_limit():
    assert discover.classify_status(402, "x") == "not_covered"
    assert discover.classify_status(429, None) == "limit_reached"
    assert discover.classify_status(500, None) == "unknown"
