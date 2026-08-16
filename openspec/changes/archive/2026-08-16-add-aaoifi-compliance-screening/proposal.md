## Why

Tayyib screens stocks for Shariah compliance, but the project currently has no implementation of the actual compliance screen — only placeholder thresholds in `config.py`. AAOIFI Shariah Standard No. 21 defines two financial ratio tests (total liabilities to total assets, and non-permissible income to total revenue) that a company must pass to be considered investable. Without this capability, the momentum/ranking pipeline has no way to exclude non-compliant tickers.

## What Changes

- Add an AAOIFI compliance screening capability that evaluates two ratios per ticker:
  - **Debt ratio**: total liabilities / total assets, must not exceed `debt_ratio_threshold` (default 30%).
  - **Non-permissible income ratio**: non-permissible income / total revenue, must not exceed `non_permissible_income_threshold` (default 5%).
- Non-permissible income is computed as interest income plus other non-operating/non-halal income (e.g. FMP's `interestIncome` + `totalOtherIncomeExpensesNet`), summed and divided by total revenue.
- A ticker fails a ratio test only when its value **strictly exceeds** the threshold; a value equal to the threshold passes.
- A ticker is Shariah-compliant only if it passes both ratio tests; failing either ratio fails the ticker.
- A ticker whose required financial data is missing (absent, not a real `0`) is classified "unscreened" rather than compliant or non-compliant, with a fixed reason string identifying which data was missing.
- Add an FMP data-fetch layer that pulls the balance sheet and income statement figures (total assets, total liabilities, total revenue, interest income, other non-operating income) needed to compute both ratios for a given ticker.
- Thresholds remain configurable via the existing `Settings` (Pydantic Settings) fields `debt_ratio_threshold` and `non_permissible_income_threshold` — no new config mechanism.

## Capabilities

### New Capabilities
- `aaoifi-screening`: Fetches the financial figures needed for AAOIFI screening from FMP and evaluates the two-ratio compliance test (debt ratio, non-permissible income ratio) for a given ticker, using configurable thresholds and a strict-exceed boundary rule.

### Modified Capabilities
(none — no existing specs)

## Impact

- New module(s) under `src/tayyib/` for the FMP financial-statement client and the AAOIFI screening logic.
- Reads `debt_ratio_threshold` and `non_permissible_income_threshold` from the existing `Settings` class in [config.py](src/tayyib/config.py) — no schema change needed there.
- Depends on `fmp_api_key` / `fmp_base_url` already present in `Settings`.
- New dependency on `httpx` (already a project dependency) for FMP HTTP calls.
- No changes to existing code, since no other capability exists yet.
