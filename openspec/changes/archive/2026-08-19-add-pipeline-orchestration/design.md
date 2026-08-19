## Context

See [proposal.md](proposal.md) - Why. Three building blocks already exist and are unmodified by this change: `screen_aaoifi_compliance()` and `AaoifiScreeningResult` in [aaoifi.py](../../../src/tayyib/screening/aaoifi.py); `fetch_financial_statement_figures()` and `FmpRequestError` in [fmp.py](../../../src/tayyib/data/fmp.py); and `start_pipeline_run`/`complete_pipeline_run`/`fail_pipeline_run`/`persist_screening_result` in [persistence.py](../../../src/tayyib/storage/persistence.py), each accepting an optional `session: Session | None = None` for testability (defaulting to `get_session()` from `engine.py`). This change adds the function that calls all of them in sequence for a list of tickers.

## Goals / Non-Goals

**Goals:**
- Add `run_screening_pipeline(tickers, session=None) -> PipelineRun` that screens and persists a result for every ticker in the list, as one tracked run.
- Keep per-ticker fetch-failure isolation (REQ 1.9) narrowly scoped to `FmpRequestError` - the only failure REQ 1.9 actually describes ("the financial data API fails for a single ticker").
- Make pipeline-wide failure handling (REQ 3.4/4.3) a single, simple mechanism: anything that isn't caught by the per-ticker `FmpRequestError` handler propagates to one outer handler that calls `fail_pipeline_run` and stops.
- Keep the function testable without a live Postgres or a live FMP connection, following the existing `session` and `monkeypatch` patterns already used in this codebase.

**Non-Goals:**
- Fetching or resolving the ticker universe (`settings.universe_source`) - out of scope per the proposal; `tickers` is a plain input list.
- Concurrent/parallel ticker processing - tickers are processed sequentially, one at a time. Revisit if scanning the eventual full universe sequentially proves too slow; not a concern at this stage.
- Retry/backoff on a failed fetch - a fetch failure is recorded once as `"unscreened"` for that ticker in that run, not retried within the run.
- Structured logging (`structlog`) - not yet a project dependency; this change does not add a logging framework, matching the architecture doc's own "not yet built" status for logging.
- Ranking, alerting, or scheduling - this change stops at "screening results are persisted for a given ticker list."

## Decisions

**Decision: New `src/tayyib/pipeline.py` module with one function, `run_screening_pipeline`.**
A single function is enough for this change's scope; no new package is warranted for one function that composes three already-separate modules.
- Alternative considered: a `src/tayyib/orchestration/` package. Rejected as premature structure for one function; revisit if a second orchestration function (e.g. a ranking pipeline) arrives and the two need to share helpers.

**Decision: The new `"financial data fetch failed"` reason string lives in `aaoifi.py`, alongside the five existing reason constants.**
All reason strings that can appear in a persisted `screening_results.reasons` value live in one place, so anyone auditing "what are all possible reasons" checks one file - even though this specific one is never produced by `screen_aaoifi_compliance()` itself (it's attached by `pipeline.py` when the fetch step raises `FmpRequestError`, before a `FinancialStatementFigures` exists to pass to `screen_aaoifi_compliance()`).
- Alternative considered: define the constant in `pipeline.py` instead, since that's the module that actually produces it. Rejected - splitting the reason-string vocabulary across two files makes the existing REQ 1.7a non-conflation guarantee ("these two reasons SHALL NOT be conflated or reused interchangeably") harder to audit by inspection.

**Decision: Per-ticker isolation catches only `FmpRequestError`; everything else is a pipeline-wide failure.**
For each ticker, `run_screening_pipeline` wraps only the fetch call in a `try/except FmpRequestError`. A `FmpRequestError` there is recorded as that ticker's result (`unscreened`, `"financial data fetch failed"`) and the loop continues. Any other exception - including one raised by `persist_screening_result` for a specific ticker - is not caught per-ticker; it propagates to one outer `try/except Exception` around the whole per-ticker loop, which calls `fail_pipeline_run(run.id, reason=str(exception))` and stops processing further tickers. This applies even when the underlying cause is transient (e.g. a momentary lock timeout on one write) rather than a systemic outage - the isolation boundary does not distinguish the two, so a single flaky persistence write costs the run every ticker after it, not just that one ticker's data.
- Alternative considered: also catch persistence errors per-ticker (skip that ticker, continue). Rejected - not primarily because persistence failures are assumed systemic (that's a bet this design does not actually rely on), but because a persistence failure can't be safely isolated the way a fetch failure can: a fetch failure is recorded by persisting an explicit "fetch failed" row for that ticker, but there is no way to record "persistence failed for this ticker" through the very mechanism that just failed. Catching it per-ticker would mean silently skipping tickers with no trace of why, which is a worse audit gap (REQ 5.1) than stopping the run and marking it `incomplete` with the real exception as the reason. A finer-grained response (e.g. tolerating some number of consecutive persistence failures before giving up) would fix the "one flaky write kills the run" cost this decision accepts, but that is a retry/threshold policy, the same category of thing already deferred as a Non-Goal - not introduced here to keep this change to the minimal wiring it proposes.

**Decision: `run_screening_pipeline` takes an optional `session: Session | None = None`, threading the same session through every persistence call it makes for the run.**
Matches the existing pattern in `persistence.py`'s four functions. One session per pipeline run (rather than one per persistence call, as the individual functions default to) keeps a test's assertions about a run and its results within one transaction/connection, and avoids reopening a session per ticker in production.
- Alternative considered: let each underlying persistence call open and close its own session (pass nothing through). Rejected - for a run screening many tickers, opening a fresh session per ticker is wasteful, and it would make it harder for a test to inspect a run and its results together via one `Session` object before anything is closed.

**Decision: An empty `tickers` list is valid input - the run starts and immediately completes with zero persisted results.**
No requirement implies rejecting an empty list, and treating it as an error would be an invented constraint. A run with zero results is a degenerate but well-defined case: "completed" status, no `screening_results` rows.
- Alternative considered: raise on an empty list. Rejected as an invented requirement not implied by anything in scope.

**Decision: `screening_date` is `datetime.now(UTC).date()`, computed once per run, shared by every ticker in that run.**
Matches the UTC convention already used for `PipelineRun` timestamps. Computing it once (not per-ticker) keeps every result in a run attributed to the same date, which matters for REQ 5.4's "reconstruct compliance for any past date."
- Alternative considered: compute the date per-ticker. Rejected - a run spanning midnight could then attribute results within the same run to two different dates, which would misrepresent what "a run's results" means for REQ 5.4's reconstruction.

**Decision: Test fetch-failure and pipeline-wide-failure behavior via `monkeypatch`, not a fake HTTP server.**
`pipeline.py` calls `fmp.fetch_financial_statement_figures` and `persistence.persist_screening_result` by reference, so tests can `monkeypatch.setattr` either to simulate a specific ticker's fetch failing (raise `FmpRequestError`) or a persistence call failing (raise a generic exception) without any real network or database dependency, following the same pattern already used for `settings.debt_ratio_threshold` in `test_aaoifi_screening.py`.
- Alternative considered: a fake/mock FMP HTTP server (e.g. `respx`). Rejected as unneeded weight - no task in this change tests FMP's HTTP layer itself (that was covered, or deliberately left uncovered, in the prior `aaoifi-screening` change); this change only needs to simulate "fetch succeeded" vs "fetch raised" at the function-call boundary.

## Risks / Trade-offs

- [A single transient `persist_screening_result` failure for one ticker - not just a systemic database outage - aborts the whole run and leaves every remaining ticker in the list unprocessed for that run, even though screening itself worked fine for them] → Accepted for this change's scope: there is no way to isolate a persistence failure the way a fetch failure is isolated (a fetch failure can be recorded via an explicit "fetch failed" row; a persistence failure cannot be recorded through the mechanism that just failed). The affected tickers are simply absent from that run's results rather than recorded with a false status, which is preferable to silently dropping them - but it does mean run reliability for the whole ticker list is only as good as the reliability of each individual write. Revisit with a retry/threshold policy (deferred, see Non-Goals) if transient write failures turn out to be common enough in practice to matter.
- [Sequential per-ticker processing means a run's wall-clock time scales linearly with the ticker list, with no batching or concurrency] → Acceptable at this stage per the Non-Goals; revisit once a real universe size (e.g. S&P 500) is actually wired in.
- [No logging means a pipeline-wide failure's `str(exception)` is the only diagnostic trail beyond what's in `pipeline_runs.failure_reason`] → Acceptable per the Non-Goals (`structlog` not yet a dependency); the failure reason is still persisted and queryable, just not also logged to a stream.
- [Catching only `FmpRequestError` per-ticker means a bug inside `screen_aaoifi_compliance()` itself - which should never raise, per its existing design - would still surface as a pipeline-wide failure rather than being isolated to one ticker] → Accepted: `screen_aaoifi_compliance()` is a pure function with no documented failure mode; if it ever raised, that would itself be a bug worth stopping the run over, not silently skipping past.
