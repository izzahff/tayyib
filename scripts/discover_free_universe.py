"""Find which S&P 500 tickers the FMP free plan covers.

Run it once a day. It tests tickers that are not yet checked, up to --max calls,
and saves progress in src/tayyib/data/free_plan_probe.json. It stops at once if
FMP says the daily limit is reached. When every ticker is checked, it writes
src/tayyib/data/free_plan_constituents.csv with the covered tickers.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import httpx

from tayyib.config import settings
from tayyib.universe import resolve_universe

DATA_DIR = Path(__file__).resolve().parents[1] / "src" / "tayyib" / "data"
STATE_FILE = DATA_DIR / "free_plan_probe.json"
OUTPUT_FILE = DATA_DIR / "free_plan_constituents.csv"


def classify_status(status_code: int, body: object) -> str:
    """Return covered, not_covered, limit_reached, or unknown."""
    if status_code == 200 and isinstance(body, list) and body:
        return "covered"
    if status_code == 402:
        return "not_covered"
    if status_code == 429:
        return "limit_reached"
    return "unknown"


def probe(ticker: str) -> str:
    try:
        response = httpx.get(
            f"{settings.fmp_base_url}/balance-sheet-statement",
            params={"symbol": ticker, "apikey": settings.fmp_api_key},
            timeout=20,
        )
    except httpx.HTTPError:
        return "unknown"
    try:
        body = response.json()
    except ValueError:
        body = None
    return classify_status(response.status_code, body)


def load_state() -> dict[str, list[str]]:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"covered": [], "not_covered": []}


def save_state(state: dict[str, list[str]]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=200, help="maximum calls this run")
    args = parser.parse_args()

    universe = resolve_universe("sp500")
    state = load_state()
    done = set(state["covered"]) | set(state["not_covered"])
    todo = [t for t in universe if t not in done][: args.max]

    for position, ticker in enumerate(todo, start=1):
        result = probe(ticker)
        print(f"[{position}/{len(todo)}] {ticker} {result}", flush=True)
        if result == "limit_reached":
            print("Daily limit reached. Run again tomorrow.")
            break
        if result == "unknown":
            print(f"Skipped {ticker}, unexpected response.")
            continue
        state[result].append(ticker)
        save_state(state)

    save_state(state)
    remaining = len(universe) - len(state["covered"]) - len(state["not_covered"])
    covered = len(state["covered"])
    not_covered = len(state["not_covered"])
    print(f"Covered {covered}, not covered {not_covered}, left {remaining}")
    if remaining == 0:
        OUTPUT_FILE.write_text("\n".join(state["covered"]) + "\n")
        print(f"Wrote {OUTPUT_FILE.name} with {len(state['covered'])} tickers")


if __name__ == "__main__":
    main()
