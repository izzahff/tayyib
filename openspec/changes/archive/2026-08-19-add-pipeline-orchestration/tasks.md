## 1. Reason vocabulary

- [x] 1.1 Add a `FINANCIAL_DATA_FETCH_FAILED = "financial data fetch failed"` constant to `aaoifi.py`, alongside the five existing reason constants

## 2. Pipeline module

- [x] 2.1 Create `src/tayyib/pipeline.py`
- [x] 2.2 Add `run_screening_pipeline(tickers, session=None) -> PipelineRun`: starts the run via `start_pipeline_run("screening", session=session)`, computes `screening_date = datetime.now(UTC).date()` once for the whole run

## 3. Per-ticker processing

- [x] 3.1 For each ticker in `tickers`, fetch financial statement figures via `fmp.fetch_financial_statement_figures(ticker)`, catching only `FmpRequestError`
- [x] 3.2 On `FmpRequestError`, persist a result for that ticker via `persist_screening_result` with `classification="unscreened"`, both ratios `None`, and `reasons=(FINANCIAL_DATA_FETCH_FAILED,)`, then continue to the next ticker
- [x] 3.3 On a successful fetch, call `screen_aaoifi_compliance(figures)` and persist its result via `persist_screening_result`, using the run's shared `session`
- [x] 3.4 Verify every ticker in the input list produces exactly one persisted `screening_results` row (fetch-failure or normal outcome)

## 4. Pipeline-wide failure handling

- [x] 4.1 Wrap the per-ticker loop body, outside the `FmpRequestError` catch, in a `try/except Exception` that calls `fail_pipeline_run(run.id, reason=str(exc), session=session)` and stops processing further tickers
- [x] 4.2 Leave a failure from `start_pipeline_run` itself unhandled (propagates to the caller) - no run record exists yet to mark incomplete

## 5. Completion

- [x] 5.1 After every ticker is processed without a pipeline-wide failure, call `complete_pipeline_run(run.id, session=session)`
- [x] 5.2 Return the final `PipelineRun` (reflecting "completed" or "incomplete" status as applicable)

## 6. Tests

- [x] 6.1 Unit test: a pipeline run over a list of tickers with compliant, non-compliant, and unscreened-by-missing-fields outcomes persists one result per ticker and ends "completed"
- [x] 6.2 Unit test: one ticker's fetch fails among several - the remaining tickers are still processed and persisted, and the run still ends "completed"
- [x] 6.3 Unit test: the fetch-failed ticker's persisted result is `classification="unscreened"`, both ratios `None`, `reasons=("financial data fetch failed",)`
- [x] 6.4 Unit test: every ticker's fetch fails - all are persisted with the fetch-failed reason and the run still ends "completed" (fetch failures alone never cause "incomplete")
- [x] 6.5 Unit test: a pipeline-wide failure (e.g. a persistence error not tied to one ticker's fetch) stops the run, marks it "incomplete" with a failure reason, and leaves any tickers after the failure point unprocessed
- [x] 6.6 Unit test: an empty ticker list starts and immediately completes the run with zero persisted results
- [x] 6.7 Unit test: all persisted results for a run reference that run's id, across multiple tickers in a single call
- [x] 6.8 Unit test: a `start_pipeline_run` failure propagates to the caller as an exception rather than being swallowed, and no `PipelineRun` row is created
