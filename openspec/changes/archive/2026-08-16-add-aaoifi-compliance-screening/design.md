## Context

See [proposal.md](proposal.md) - Why. The project has an FMP-backed `Settings` class ([config.py](../../../src/tayyib/config.py)) with `fmp_api_key`, `fmp_base_url`, `debt_ratio_threshold`, and `non_permissible_income_threshold` already defined, but no code yet calls FMP or performs any screening. This is a greenfield capability: no existing HTTP client, data models, or screening module exist in `src/tayyib/`.

FMP's `/stable` API exposes balance-sheet and income-statement endpoints (e.g. `balance-sheet-statement`, `income-statement`) keyed by ticker symbol, returning the most recent reporting period's line items including `totalAssets`, `totalLiabilities`, `revenue`, `interestIncome`, and `totalOtherIncomeExpensesNet`.

## Goals / Non-Goals

**Goals:**
- Fetch the five financial figures needed for AAOIFI screening from FMP for a single ticker.
- Compute the two AAOIFI ratios and apply the strict-exceed boundary rule.
- Return a structured, typed result (per-ratio values, a three-way classification of compliant / non-compliant / unscreened, and one or more fixed reason strings) rather than a bare boolean, so callers and future reporting/dashboard code can show *why* a ticker failed, was excluded, or couldn't be screened.
- Keep thresholds sourced exclusively from the existing `Settings` object.

**Non-Goals:**
- Batch/universe-wide screening orchestration (looping over the S&P 500 universe) - this change provides the single-ticker building block; wiring it into a universe-wide job is a future change.
- Caching or persistence of fetched financial data or screening results (no `database_url` usage here).
- Any AAOIFI screening criteria beyond the two ratios (e.g. AAOIFI also defines a liquidity/market-cap ratio in some formulations) - explicitly out of scope per the proposal's "two-ratio implementation".
- Retry/backoff policy tuning for FMP - a single straightforward HTTP call with error surfacing is sufficient for this change.

## Decisions

**Decision: Separate FMP client module from screening logic module.**
`src/tayyib/data/fmp.py` (or similar) owns HTTP calls and raw response parsing into a typed `FinancialStatementFigures` model. `src/tayyib/screening/aaoifi.py` owns pure ratio computation and pass/fail logic, taking `FinancialStatementFigures` and the two thresholds as plain inputs.
- Alternative considered: a single module mixing fetch + evaluate. Rejected because it makes the ratio/boundary logic (the part with real business rules and the highest need for unit tests) untestable without mocking HTTP.

**Decision: Non-permissible income = `interestIncome` + `totalOtherIncomeExpensesNet` from FMP's income statement.**
Per the clarification in this change's proposal, non-permissible income is not a single FMP field; it's derived by summing interest income and other non-operating/non-halal income line items.
- Alternative considered: interest income only (simpler, more conservative estimate). Rejected per explicit user decision - `totalOtherIncomeExpensesNet` is included to avoid under-counting non-halal income sources.

**Decision: Debt ratio uses `totalLiabilities` from the balance sheet, not interest-bearing debt (`totalDebt`).**
Per AAOIFI Requirements v3.4 REQ 1.2.1 and REQ 1.2.1a, this project follows the FTSE/MSCI total-assets convention: the debt ratio numerator is total liabilities, not narrowly interest-bearing debt. This is a deliberate, documented convention choice, not an approximation.
- Alternative considered: interest-bearing debt (`totalDebt`) / total assets - the AAOIFI standard's literal "interest-bearing debt" language. Rejected in favor of the documented FTSE/MSCI total-liabilities convention per REQ 1.2.1a, which explicitly names and rejects `totalDebt`.

**Decision: Three-way classification (compliant / non-compliant / unscreened) with fixed reason strings, not a bare pass/fail.**
Per the spec's Overall Compliance Classification and Financial Data Retrieval requirements, a ticker is never defaulted into compliant or non-compliant when data is missing - it gets a distinct "unscreened" outcome. Reason strings are fixed values ("debt ratio exceeded", "non-permissible income exceeded", "insufficient data for debt ratio calculation", "insufficient data for non-permissible income calculation", "revenue is zero, cannot compute non-permissible income ratio") rather than freeform text, and a ticker with both a balance-sheet-side and a non-permissible-income-side reason reports both together, not just one. A field's `None` (absent) is distinguished from a real `0` value: `0` is valid data and is screened normally, except for `revenue` - whether `revenue` is `None` (absent) or explicitly `0` (present but zero-valued), the ticker is unscreened with the same "revenue is zero, cannot compute non-permissible income ratio" reason in both cases, to avoid a division by zero. This reason is distinct from the general "insufficient data for non-permissible income calculation" reason, which applies only when `revenue` itself is present and non-zero but `interestIncome` or `totalOtherIncomeExpensesNet` is absent.
- Alternative considered: raise an exception on missing data. Rejected as the non-goal excludes orchestration, but the single-ticker function must not force every caller into try/except for a routine data-availability case.
- Alternative considered: treat `0` and `None` identically as "missing". Rejected - some issuers (e.g. Apple FY2024-2025) legitimately report `0` for interest income, and treating that as missing would wrongly unscreen a computable ticker.
- Alternative considered: reuse the generic "insufficient data for non-permissible income calculation" reason for a zero or missing `revenue`. Rejected - a zero/missing `revenue` is a distinct, more specific failure (division-by-zero guard) than a merely-absent `interestIncome`/`totalOtherIncomeExpensesNet`, and collapsing them would hide which condition actually occurred.

**Decision: "Unavailable" (fetch failure) and "unscreened" (incomplete data) are distinct, non-interchangeable terms.**
Per REQ 1.9a, a failed/errored/timed-out FMP request ("unavailable") is a request/network-level problem, while a successful response missing required fields ("unscreened") is a data-completeness problem. Both ultimately exclude the ticker from the compliant list, but they SHALL be logged and reasoned about separately - conflating them in logs or reason strings would hide which category of problem actually occurred for a given ticker.
- Alternative considered: treat any failure to produce a compliance result as a single generic "unscreened" outcome. Rejected - it would erase the distinction between "the API connection or ticker itself has a problem" and "the provider's data for this ticker is incomplete," which are different things to investigate.

**Decision: Boundary comparison uses `>` (strict exceed) for failure, i.e. `<=` for pass.**
This matches the proposal's explicit "strict-exceed boundary rule" and the spec's exact-threshold scenarios: a ratio equal to the threshold passes.

## Risks / Trade-offs

- [FMP field names/availability may vary by ticker or plan tier (e.g. `totalLiabilities` or `totalOtherIncomeExpensesNet` not always present)] → Parse defensively in the FMP client layer, distinguish absent (`None`) from a real `0`, and treat any figure that cannot be resolved as missing, triggering the "unscreened" outcome with its reason string rather than a crash or a silently wrong ratio.
- [Two-ratio screen is a simplification of full AAOIFI Shariah Standard No. 21, which some implementations extend with a market-cap-based liquidity ratio] → Explicitly scoped out per the proposal; note this in code/docstrings so it isn't mistaken for a complete AAOIFI implementation.
- [FMP rate limits or transient HTTP failures on the free/stable tier] → Out of scope for retry tuning in this change; surface the HTTP error to the caller as "unavailable" rather than masking it as "unscreened." Per REQ 1.9a, "unavailable" (the fetch itself failed) and "unscreened" (the fetch succeeded but required fields were absent) are two distinct, intentionally separate failure modes - conflating them in logs or reason strings would hide which category of problem actually occurred.
