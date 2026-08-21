## Context

See [proposal.md](proposal.md) - Why. `settings.universe_source` ([config.py](../../../src/tayyib/config.py)) already exists, defaulting to `"sp500"`, but nothing reads it. No universe-related module, file, or data exists in the repo yet. `run_screening_pipeline(tickers, session=None)` ([pipeline.py](../../../src/tayyib/pipeline.py)) already accepts a plain `list[str]`, unmodified by this change.

## Goals / Non-Goals

**Goals:**
- Add `resolve_universe(universe_source=None) -> list[str]`, defaulting to `settings.universe_source`, that returns a validated ticker list for `"sp500"` and raises for anything else.
- Populate the real static S&P 500 constituent file as part of this change - the capability does not exist in any useful sense without real data in it.
- Make every failure mode (unrecognized source, missing file, empty file, invalid entries) raise a single, clearly-named exception type with a message that says which case occurred.

**Non-Goals:**
- Wiring `resolve_universe()` into `run_screening_pipeline` - per the proposal, this change produces a compatible list, it does not compose the two.
- Any universe source beyond `"sp500"` - see proposal's Out of scope.
- Keeping the static file current over time (a refresh job, staleness detection, or diffing against a live source on each run) - the file is accurate as of when this change is implemented; that's the whole point of "static, checked-in," not "live."

## Decisions

**Decision: New `src/tayyib/universe.py` module with one function, `resolve_universe`, and one exception, `UniverseResolutionError`.**
Mirrors the existing pattern of a small, single-purpose module per concern (`pipeline.py` for orchestration, `aaoifi.py` for screening logic).
- Alternative considered: put this in `data/fmp.py` since it's "data sourcing." Rejected - this data is explicitly *not* fetched from FMP (that's the whole reason for a static file), so co-locating it with the FMP client would be misleading about what the module does.

**Decision: `UniverseResolutionError(Exception)` is one exception type covering all four failure modes (unrecognized source, missing file, empty file, invalid entries), distinguished by message text, not by subclassing.**
All four are the same category of problem from a caller's perspective - "the universe could not be resolved, don't start a run" - and REQ 1.9's per-ticker isolation explicitly does not apply here (see proposal - Why), so there's no behavioral reason for a caller to need to distinguish them programmatically. A caller that wants to log or alert on why can read the exception's message.
- Alternative considered: a subclass per failure mode (`UnrecognizedUniverseSourceError`, `MissingUniverseDataError`, etc.). Rejected as unneeded granularity - nothing in this change's scope catches these selectively; they're all meant to propagate and stop the caller before a run starts.

**Decision: The `"sp500"` data lives at `src/tayyib/data/sp500_constituents.csv` - one ticker symbol per line, no header row.**
CSV over JSON: a one-column file is simpler to read (`csv.reader` or even plain line-splitting), simpler to diff in git when constituents change, and matches how such lists are typically distributed (e.g. copied from a table). No header row, since the file has exactly one kind of value in it - a header would just be another line to skip.
- Alternative considered: JSON array of strings. Rejected - no structural benefit for a flat list of ~500 strings, and CSV is marginally more diffable/reviewable in a PR.
- Alternative considered: put the file under a new `src/tayyib/data/universe/` subpackage. Rejected as unneeded structure for one file; revisit if a second universe source (with its own file) is ever added.

**Decision: Tickers are uppercased on read, and duplicate/blank checks run against the uppercased form.**
Ticker symbols are conventionally uppercase; normalizing on read means `"aapl"` and `"AAPL"` in the source data are treated as the same ticker for duplicate detection (and raise, per the validation requirement) rather than silently becoming two distinct-looking entries that are actually the same company.
- Alternative considered: preserve file casing exactly, no normalization. Rejected - it would let a case-only duplicate (a real data-quality bug in the source file) slip past validation undetected.

**Decision: Reading and validating a ticker file is a separate, path-parameterized function (`_read_ticker_file(path) -> list[str]`) from `resolve_universe()`'s source-name-to-path mapping.**
`resolve_universe()` maps `"sp500"` to the real checked-in path and calls `_read_ticker_file` on it; tests call `_read_ticker_file` directly against a `tmp_path`-created file to exercise missing/empty/blank/duplicate cases, without touching or mutating the real production data file. Mirrors the existing split between `fmp.py`'s network-calling functions and its pure `parse_financial_statement_figures`.
- Alternative considered: test exclusively against the real `sp500_constituents.csv`, using `monkeypatch` to point at broken variants only for the failure cases. Rejected - it's simpler and more isolated to construct a small, purpose-built file per test case than to fixture-swap the real (large) data file.

**Decision: Validation raises on the first problem found; it does not collect and report every problem in one pass.**
Simpler to implement and reason about, and the fix is the same either way (correct the source file and re-run) - collecting a full list of every blank/duplicate before raising adds complexity this change's scope doesn't need.
- Alternative considered: accumulate all validation errors and raise once with the full list. Rejected as unneeded polish for a file that, once corrected the first time, is expected to stay valid.

**Decision: Sourcing the real S&P 500 constituent list uses a public reference (e.g. Wikipedia's "List of S&P 500 companies" page), fetched once during this change's implementation, not invented or approximated.**
Ticker data accuracy matters - an incomplete or wrong universe silently changes what gets screened. This is a task in tasks.md, done with actual data retrieval during `/opsx:apply`, not a placeholder deferred elsewhere.
- Alternative considered: hand-write a "representative sample" of well-known large-cap tickers instead of the real ~500. Rejected - a fake or partial universe would silently misrepresent what "the S&P 500 universe" means to every caller of this function, which is a worse failure mode than the ones this change is designed to catch.

## Risks / Trade-offs

- [The checked-in file becomes stale as real S&P 500 constituents change (additions, removals, rebalances)] → Accepted per the Non-Goals; this change delivers a snapshot, not a live sync. Revisit with a refresh mechanism if staleness becomes an actual problem in practice.
- [Sourcing real constituent data from a public reference page depends on that page's structure/accuracy at implementation time] → Mitigated by using a well-known, commonly-cited reference rather than an obscure one; the resulting file is reviewable in the PR diff like any other checked-in data, so an obviously wrong or truncated list is visible before merge.
- [Task 1.1 depends on live web access at the time it's implemented; without it, the only "safe" outcome is stopping and asking, since filling the file from memorized/approximated data would look identical to a correct file while being silently wrong for however many constituents have changed] → Mitigated by stating this explicitly as a hard stop condition in task 1.1 itself, not left as an assumption the implementer is expected to infer.
- [A single "no duplicates" rule with case-insensitive normalization could, in principle, reject two genuinely different tickers that happen to collide only after uppercasing - not a real scenario for standard US equity tickers, but worth naming] → Accepted as a non-issue for this change's actual data (S&P 500 US equity tickers use a consistent, non-colliding format); revisit if a future universe source uses tickers where this assumption doesn't hold.
