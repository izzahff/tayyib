import pytest

from tayyib import universe
from tayyib.universe import UniverseResolutionError, _read_ticker_file, resolve_universe

# 3.1


def test_resolve_universe_sp500_returns_uppercase_tickers_from_real_file():
    tickers = resolve_universe("sp500")
    assert len(tickers) > 0
    assert all(ticker == ticker.upper() for ticker in tickers)
    assert "AAPL" in tickers
    assert "MSFT" in tickers
    assert "JPM" in tickers


# 3.2


def test_resolve_universe_defaults_to_settings_universe_source(monkeypatch):
    monkeypatch.setattr(universe.settings, "universe_source", "unknown-source")
    with pytest.raises(UniverseResolutionError, match="unknown-source"):
        resolve_universe()


# 3.3


def test_unrecognized_universe_source_raises():
    with pytest.raises(UniverseResolutionError, match="nasdaq100"):
        resolve_universe("nasdaq100")


# 3.4


def test_missing_file_raises(tmp_path):
    missing_path = tmp_path / "does_not_exist.csv"
    with pytest.raises(UniverseResolutionError, match="not found"):
        _read_ticker_file(missing_path)


# 3.5


def test_empty_file_raises(tmp_path):
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("")
    with pytest.raises(UniverseResolutionError, match="empty"):
        _read_ticker_file(empty_file)


# 3.6


def test_blank_entry_raises(tmp_path):
    file_with_blank = tmp_path / "blank.csv"
    file_with_blank.write_text("AAPL\n\nMSFT\n")
    with pytest.raises(UniverseResolutionError, match="blank"):
        _read_ticker_file(file_with_blank)


# 3.7


def test_duplicate_ticker_raises(tmp_path):
    file_with_dup = tmp_path / "dup.csv"
    file_with_dup.write_text("AAPL\nMSFT\nAAPL\n")
    with pytest.raises(UniverseResolutionError, match="duplicate"):
        _read_ticker_file(file_with_dup)


# 3.8


def test_case_only_duplicate_raises(tmp_path):
    file_with_case_dup = tmp_path / "case_dup.csv"
    file_with_case_dup.write_text("AAPL\nmsft\nMSFT\n")
    with pytest.raises(UniverseResolutionError, match="duplicate"):
        _read_ticker_file(file_with_case_dup)


# 3.9


def test_mixed_case_file_returned_uppercased_in_order(tmp_path):
    mixed_case_file = tmp_path / "mixed.csv"
    mixed_case_file.write_text("aapl\nMsft\nJPM\n")
    tickers = _read_ticker_file(mixed_case_file)
    assert tickers == ["AAPL", "MSFT", "JPM"]
