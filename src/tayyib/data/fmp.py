from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import httpx

from tayyib.config import settings


class FmpRequestError(Exception):
    """A request-level failure ("unavailable"), distinct from a successful
    response with missing fields ("unscreened") per REQ 1.9a."""


@dataclass(frozen=True)
class FinancialStatementFigures:
    total_assets: float | None
    total_liabilities: float | None
    revenue: float | None
    interest_income: float | None
    other_non_operating_income: float | None


def _get(endpoint: str, ticker: str) -> dict:
    try:
        response = httpx.get(
            f"{settings.fmp_base_url}/{endpoint}",
            params={"symbol": ticker, "apikey": settings.fmp_api_key},
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise FmpRequestError(f"FMP request to {endpoint} failed for {ticker}: {exc}") from exc

    data = response.json()
    if not data:
        raise FmpRequestError(f"FMP returned no data from {endpoint} for {ticker}")
    return data[0]


def fetch_balance_sheet(ticker: str) -> dict:
    return _get("balance-sheet-statement", ticker)


def fetch_income_statement(ticker: str) -> dict:
    return _get("income-statement", ticker)


def parse_financial_statement_figures(
    balance_sheet: dict, income_statement: dict
) -> FinancialStatementFigures:
    return FinancialStatementFigures(
        total_assets=balance_sheet.get("totalAssets"),
        total_liabilities=balance_sheet.get("totalLiabilities"),
        revenue=income_statement.get("revenue"),
        interest_income=income_statement.get("interestIncome"),
        other_non_operating_income=income_statement.get("totalOtherIncomeExpensesNet"),
    )


def fetch_financial_statement_figures(ticker: str) -> FinancialStatementFigures:
    return parse_financial_statement_figures(
        fetch_balance_sheet(ticker), fetch_income_statement(ticker)
    )


def fetch_adjusted_closes(ticker: str, from_date: date) -> list[tuple[date, float]]:
    """Dividend-adjusted daily closes, oldest first."""
    try:
        response = httpx.get(
            f"{settings.fmp_base_url}/historical-price-eod/dividend-adjusted",
            params={
                "symbol": ticker,
                "from": from_date.isoformat(),
                "apikey": settings.fmp_api_key,
            },
        )
        response.raise_for_status()
        rows = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise FmpRequestError(f"FMP price request failed for {ticker}: {exc}") from exc

    closes = parse_adjusted_closes(rows)
    if not closes:
        raise FmpRequestError(f"FMP returned no price data for {ticker}")
    return closes


def parse_adjusted_closes(rows: object) -> list[tuple[date, float]]:
    if not isinstance(rows, list):
        return []
    closes = [
        (date.fromisoformat(row["date"]), float(row["adjClose"]))
        for row in rows
        if row.get("adjClose") is not None and row.get("date")
    ]
    return sorted(closes, key=lambda item: item[0])
