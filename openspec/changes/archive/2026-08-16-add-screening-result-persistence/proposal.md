## Why

The AAOIFI screening capability ([aaoifi-screening](../../specs/aaoifi-screening/spec.md)) currently only returns an in-memory `AaoifiScreeningResult` — nothing is written to the database, so there is no audit trail and no way to reconstruct which tickers were compliant on a past date. This change adds persistence for screening results, plus a reusable pipeline-run lifecycle so future steps (ranking, alerting) can track their own runs the same way.

## What Changes

- Add a `pipeline_runs` table/model tracking a run's step name, start time, completion time, and status (`started` / `completed` / `incomplete`), with a shared function to mark a run complete or incomplete. This is built step-agnostic now, per REQ 3.4/4.3's shared-function pattern, so ranking and alerting can reuse it once those capabilities exist — it is not scoped to screening internally, even though screening is its only caller today.
- Add a `screening_results` table/model persisting, per ticker per run: the ticker, the screening date, both ratio values (nullable, since an unscreened ticker has no computed ratio), the classification (compliant / non-compliant / unscreened), and the reason string(s).
- Add a SQLModel engine/session setup sourced from the existing `settings.database_url`.
- Add persistence functions: start a pipeline run, mark a run complete or incomplete, and write one ticker's `AaoifiScreeningResult` to `screening_results` linked to a run.
- Historical data is retained indefinitely; this change adds no deletion or pruning logic.
- Add a Postgres driver dependency (SQLModel/SQLAlchemy needs one for `postgresql://` URLs; none is currently in `pyproject.toml`) — the exact package is a design.md decision.

**Out of scope for this change** (per explicit scoping decision):
- Universe-wide iteration (calling the screening logic for every ticker in `settings.universe_source`). This change only adds the persistence layer; a future change wires iteration to it.
- Ranking and alerting persistence (REQ 2.6, REQ 5.2) — only screening results are persisted here. The `pipeline_runs` table is shaped to support those later, but no ranking/alerting code is added.

## Capabilities

### New Capabilities
- `pipeline-runs`: Tracks the lifecycle (started / completed / incomplete) of a pipeline run, independent of which step is running, so any step can record and query its own run history.
- `screening-persistence`: Persists AAOIFI screening results (ratios, classification, reasons) per ticker per pipeline run, enabling historical reconstruction of past compliance decisions.

### Modified Capabilities
(none — `aaoifi-screening`'s requirements are unchanged; this change only adds persistence around its existing output)

## Impact

- New module(s) under `src/tayyib/` for SQLModel table models, the engine/session, and persistence functions (exact layout in design.md).
- New Postgres driver dependency in `pyproject.toml` (exact package chosen in design.md).
- Reads `settings.database_url` (already defined in [config.py](../../../src/tayyib/config.py)); no changes to `Settings`.
- No changes to `screen_aaoifi_compliance()` or `AaoifiScreeningResult` in [aaoifi.py](../../../src/tayyib/screening/aaoifi.py) — this change consumes that output, it doesn't alter it.
