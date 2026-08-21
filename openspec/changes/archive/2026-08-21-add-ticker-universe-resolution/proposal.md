## Why

`run_screening_pipeline(tickers)` exists and works, but nothing produces the `tickers` list it needs - `settings.universe_source` ("sp500" by default) is stored in config but never resolved into anything. There is no way today to actually run a real screening pass without hand-typing a ticker list. This change adds the missing piece: turning `settings.universe_source` into a concrete `list[str]` that a caller can hand to `run_screening_pipeline`.

## What Changes

- Add a `resolve_universe(universe_source=None)` function that resolves a universe source name into a `list[str]` of ticker symbols.
- For the `"sp500"` source, resolve from a static, checked-in file (not a live API call) - the constituent list changes infrequently, and re-fetching it on every run would burn FMP quota for no benefit.
- Validate the resolved list: no empty/blank entries, no duplicate tickers. A malformed file fails the same way a missing one does, not silently.
- Fail fast and loudly - raise an exception, not return an empty list - when: `universe_source` is not a recognized value; the backing file for a recognized source is missing; the file is empty; or the file contains only invalid entries. A universe-level problem is a configuration/startup problem, not a per-ticker one, and REQ 1.9's per-ticker isolation does not apply to it - `resolve_universe()` either returns a real, non-empty, valid list or raises before any pipeline run starts.
- Include, as part of this change's own tasks, actually populating the static S&P 500 constituent file with real ticker symbols from a reliable public source - the capability is not usable without real data in that file, so sourcing it is not deferred to a later change.

**Out of scope for this change** (per explicit scoping decision):
- Wiring `resolve_universe()` into `run_screening_pipeline` automatically (e.g. calling it when `tickers` is omitted). This change produces a list compatible with what `run_screening_pipeline` already accepts; composing the two is left to whatever future entry point (CLI, scheduler) actually triggers a real run, matching how every prior change in this project deferred cross-capability wiring to its own explicit step.
- Any universe source other than `"sp500"` - `universe_source` accepting other values in `Settings` does not mean this change resolves them; an unrecognized value is exactly the "misconfigured" case that fails fast.
- Keeping the static file in sync with real-world index changes over time (e.g. a refresh job or staleness check). The file is checked in as of when this change is implemented; keeping it current is a future concern.

## Capabilities

### New Capabilities
- `ticker-universe`: Resolves a configured universe source into a validated, non-empty list of ticker symbols, failing fast on misconfiguration or missing/invalid data rather than returning an empty or partially-valid list.

### Modified Capabilities
(none - `pipeline-orchestration`'s `run_screening_pipeline` is unchanged; this change produces an input compatible with its existing `tickers: list[str]` parameter, it does not call into or alter that function)

## Impact

- New module under `src/tayyib/` for `resolve_universe()` (exact location in design.md).
- New static data file checked into the repo, populated with real S&P 500 constituent tickers as part of this change's tasks.
- No changes to `Settings` (the `universe_source` field already exists), `run_screening_pipeline`, or any existing capability's requirements.
- No new runtime dependency for reading the file (CSV/JSON, exact choice in design.md - both are Python standard library).
