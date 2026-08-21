from __future__ import annotations

from pathlib import Path

from tayyib.config import settings

SP500_CONSTITUENTS_PATH = Path(__file__).parent / "data" / "sp500_constituents.csv"


class UniverseResolutionError(Exception):
    pass


def _read_ticker_file(path: Path) -> list[str]:
    if not path.exists():
        raise UniverseResolutionError(f"Universe data file not found: {path}")

    lines = path.read_text().splitlines()
    if not lines:
        raise UniverseResolutionError(f"Universe data file is empty: {path}")

    tickers: list[str] = []
    seen: set[str] = set()
    for line in lines:
        ticker = line.strip().upper()
        if not ticker:
            raise UniverseResolutionError(f"Universe data file contains a blank entry: {path}")
        if ticker in seen:
            raise UniverseResolutionError(
                f"Universe data file contains a duplicate ticker: {ticker} ({path})"
            )
        seen.add(ticker)
        tickers.append(ticker)

    return tickers


def resolve_universe(universe_source: str | None = None) -> list[str]:
    if universe_source is None:
        universe_source = settings.universe_source

    if universe_source == "sp500":
        return _read_ticker_file(SP500_CONSTITUENTS_PATH)

    raise UniverseResolutionError(f"Unrecognized universe source: {universe_source!r}")
