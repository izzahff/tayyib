from __future__ import annotations

from dataclasses import dataclass

INSUFFICIENT_PRICE_HISTORY = "insufficient price history"
PRICE_DATA_FETCH_FAILED = "price data fetch failed"


@dataclass(frozen=True)
class MomentumScore:
    ticker: str
    score: float | None
    reason: str | None = None


@dataclass(frozen=True)
class TargetEntry:
    ticker: str
    rank: int
    score: float
    weight: float


def momentum_score(closes: list[float], lookback: int) -> float | None:
    """Latest adjusted close over the close `lookback` records earlier, minus 1."""
    if len(closes) < lookback + 1:
        return None
    base = closes[-(lookback + 1)]
    if base <= 0:
        return None
    return closes[-1] / base - 1


def select_top(scores: list[MomentumScore], top_n: int) -> list[TargetEntry]:
    scored = [item for item in scores if item.score is not None]
    scored.sort(key=lambda item: (-item.score, item.ticker))
    chosen = scored[:top_n]
    if not chosen:
        return []
    weight = 1 / len(chosen)
    return [
        TargetEntry(ticker=item.ticker, rank=index, score=item.score, weight=weight)
        for index, item in enumerate(chosen, start=1)
    ]
