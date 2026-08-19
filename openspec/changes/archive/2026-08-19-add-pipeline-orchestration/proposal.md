## Why

`aaoifi-screening` (single-ticker screening), `pipeline-runs` (run lifecycle tracking), and `screening-persistence` (writing one result) all exist as building blocks, but nothing wires them together. There is no way today to actually screen a list of tickers and get a tracked, persisted run out of it - each piece has to be called by hand. This change adds the orchestration layer that runs the existing building blocks end-to-end for a given ticker list.

## What Changes

- Add a `run_screening_pipeline(tickers)` function that, for a given list of ticker symbols:
  - Starts a pipeline run via `start_pipeline_run("screening")`.
  - For each ticker: fetches financial statement figures (`fmp.py`), screens them (`screen_aaoifi_compliance`), and persists the result (`persist_screening_result`) - all against that one run.
  - Marks the run `complete_pipeline_run` once every ticker has been processed.
- Per-ticker fetch isolation (REQ 1.9): if a ticker's FMP fetch fails entirely (`FmpRequestError`), the run continues with the remaining tickers rather than aborting.
- A new fixed reason string, `"financial data fetch failed"`, is introduced for this specific case - distinct from the five existing `aaoifi-screening` reasons, which all describe a successful FMP response with specific fields missing, not a failed request. A ticker whose fetch fails entirely is persisted as `classification="unscreened"`, both ratios `null`, with this reason - it is not skipped and not conflated with the existing "insufficient data" reasons (per the same non-conflation principle established for REQ 1.7a). `screen_aaoifi_compliance()` never sees this case (fetch failure happens before a `FinancialStatementFigures` even exists), so this is new `pipeline-orchestration` behavior, not a change to `aaoifi-screening`'s existing contract - the constant's exact code location is a design.md decision, not a spec-level concern.
- Pipeline-wide failure handling (REQ 3.4/4.3): any failure that is not an isolated per-ticker fetch/screening problem (e.g. the run cannot start, or a persistence error not tied to fetching/screening one ticker) marks the run `incomplete` via `fail_pipeline_run` with a reason, rather than leaving it dangling in `"started"`.
- No changes to `screen_aaoifi_compliance()`, `AaoifiScreeningResult`, the FMP client functions, or the persistence functions' existing behavior - this change calls them, it doesn't alter their contracts (aside from the one new reason string above).

**Out of scope for this change** (per explicit scoping decision):
- Fetching or maintaining the ticker universe itself (e.g. the S&P 500 constituent list behind `settings.universe_source`). `run_screening_pipeline` takes an explicit ticker list; resolving "the configured universe" into that list is a separate, future concern.
- Ranking, alerting, and scheduling (Capabilities 2-4) - this change only wires screening + persistence.
- Retry/backoff for FMP fetch failures - a failed fetch is recorded as `"unscreened"` for that ticker in that run, not retried within the same run.

## Capabilities

### New Capabilities
- `pipeline-orchestration`: Runs AAOIFI screening across a list of tickers as one tracked pipeline run, persisting a result per ticker (including a dedicated outcome for a ticker whose financial data cannot be fetched at all) and isolating per-ticker fetch/screening failures from pipeline-wide failures.

### Modified Capabilities
(none - `aaoifi-screening`'s existing contract for `screen_aaoifi_compliance()` is unchanged; the fetch-failure outcome is new `pipeline-orchestration` behavior, since `screen_aaoifi_compliance()` is never invoked when the fetch itself fails)

## Impact

- New module under `src/tayyib/` for the pipeline orchestration function and the new reason-string constant (exact location, including whether the constant lives alongside `aaoifi.py`'s existing ones or in the new module, is a design.md decision).
- `screen_aaoifi_compliance()`'s own logic and its five existing reasons in `src/tayyib/screening/aaoifi.py` are unchanged - that function only ever sees a successfully-fetched (if incomplete) response.
- Calls existing, unmodified functions from `src/tayyib/data/fmp.py` and `src/tayyib/storage/persistence.py`.
- No changes to `Settings`, table schemas, or the `aaoifi-screening`/`pipeline-runs`/`screening-persistence` capabilities' existing requirements.
