## Context

See [proposal.md](proposal.md) - Why. `settings.database_url` ([config.py](../../../src/tayyib/config.py)) already defaults to a plain `postgresql://` URL but nothing in the codebase uses it yet - no engine, no session, no table models. `sqlmodel` is already a project dependency; no Postgres DBAPI driver is. The only existing domain code this change touches is [aaoifi.py](../../../src/tayyib/screening/aaoifi.py)'s `AaoifiScreeningResult` (read, not modified) and [fmp.py](../../../src/tayyib/data/fmp.py) (untouched).

## Goals / Non-Goals

**Goals:**
- Add SQLModel table models for `pipeline_runs` and `screening_results` and a way to create them in a real Postgres database.
- Add small, testable persistence functions: start/complete/fail a pipeline run, and persist one ticker's `AaoifiScreeningResult` against a run.
- Keep `screen_aaoifi_compliance()` pure and untouched - persistence is a separate layer that consumes its output, not a change to the screening module itself.
- Make tests runnable without a live Postgres instance.

**Non-Goals:**
- Universe-wide iteration or wiring persistence into an actual screening loop - per the proposal, this change is the persistence layer only.
- Ranking/alerting persistence (REQ 2.6, REQ 5.2) - only `screening_results` is added.
- Schema migration tooling (e.g. Alembic). This is the project's first schema; tables are created with `SQLModel.metadata.create_all()`. Migrations become relevant once a schema change needs to roll out against an existing populated database - not yet.
- Deletion/retention policy enforcement beyond "don't delete anything" - no TTL, no archival job.

## Decisions

**Decision: New `src/tayyib/storage/` package with `models.py`, `engine.py`, and `persistence.py`.**
`models.py` holds the two SQLModel table classes. `engine.py` holds a module-level engine built from `settings.database_url` and a `get_session()` helper. `persistence.py` holds the functions that open a session, do one unit of work, and commit - `start_pipeline_run`, `complete_pipeline_run`, `fail_pipeline_run`, `persist_screening_result`.
- Alternative considered: put persistence functions directly in `screening/aaoifi.py`. Rejected - it would couple the pure ratio-computation module to a database dependency, and the prior change's design deliberately kept that module free of I/O for testability.

**Decision: `psycopg2-binary` as the Postgres driver.**
`settings.database_url`'s existing default is a bare `postgresql://` URL with no `+driver` suffix; SQLAlchemy resolves that to `psycopg2` by default. Adding `psycopg2-binary` works with the URL as it already exists, with no change to `Settings`.
- Alternative considered: `psycopg[binary]` (psycopg3). Rejected for this change - it's a fine driver, but using it would require changing the default URL to `postgresql+psycopg://` (or documenting that operators must), which isn't otherwise motivated here. Revisit if there's a concrete reason to move to psycopg3 later.

**Decision: `reasons` stored as a Postgres native `text[]` array column, not JSON, a join table, or a delimited string.**
The production schema uses `ARRAY(String)` (SQLModel `sa_type=ARRAY(String)`), giving a real Postgres `text[]` column rather than JSON. This supports direct array queries (e.g. `WHERE 'debt ratio exceeded' = ANY(reasons)`) without casting, per REQ 5.1a. SQLite has no native array type, so the same field's type is given a SQLite variant - `ARRAY(String).with_variant(JSON(), "sqlite")` - so tests running against the in-memory SQLite engine store the same values as a JSON column while production Postgres stores a true `text[]`. This is a per-dialect type adapter, not a change to the production schema.
- Alternative considered: JSON column on both Postgres and SQLite. Rejected - `text[]` is the locked production type; JSON is only the SQLite test-only fallback via the type adapter, never the production schema.
- Alternative considered: a separate `screening_result_reasons` join table. Rejected as over-normalized for a bounded 0-2-item list with no independent identity or querying need beyond "does this result have reason X."
- Alternative considered: a comma-joined string column. Rejected - reasons like "non-permissible income exceeded" don't contain commas today, but a string-splitting convention is more fragile and less explicit than a native array for no real space savings.

**Decision: Both ratio columns are nullable independently.**
An unscreened result can have one ratio computed and the other not (e.g. debt ratio computed fine, non-permissible income unscreened because revenue was zero) - per `aaoifi.py`'s `AaoifiScreeningResult`, `debt_ratio` and `non_permissible_income_ratio` are independently `float | None`. The persisted row mirrors that shape exactly rather than collapsing to "both null when unscreened."
- Alternative considered: null out both ratios whenever classification is "unscreened," ignoring whichever one actually computed. Rejected - it would silently discard real computed data that the audit trail (REQ 5.4) should keep.

**Decision: Tests use an in-memory SQLite engine, not a live Postgres instance.**
SQLModel/SQLAlchemy can create the same table models against `sqlite:///:memory:` for tests, avoiding a Postgres dependency in CI/dev. Column types used (string, float, datetime, JSON) are all supported by SQLite.
- Alternative considered: require a live Postgres for tests (e.g. via `testcontainers`). Rejected as unnecessary weight for this change's scope; revisit if Postgres-specific behavior (e.g. JSONB operators) is ever relied on.

**Decision: Session-per-call, not a long-lived global session.**
Each persistence function opens a `Session`, does one unit of work, commits, and closes. No connection pooling tuning or request-scoped session management, since there's no web request lifecycle in scope yet.
- Alternative considered: a shared/global session. Rejected - unsafe across concurrent callers and unnecessary until there's an actual server process managing session lifecycle.

## Risks / Trade-offs

- [SQLite-in-tests vs. Postgres-in-production diverge for `reasons`: real `text[]` array on Postgres, JSON on SQLite via the type adapter] → The two representations are functionally equivalent for this change's usage (an ordered list of strings, read and written as a whole - no partial-element queries or array operators used anywhere), so the divergence has no observable effect on the persistence functions' behavior. Revisit if a future change ever relies on Postgres-specific array operators that SQLite's JSON fallback can't emulate.
- [No migration tooling means a future schema change has no tracked upgrade path] → Acceptable for the first schema; flagged as a Non-Goal to revisit once the schema needs to evolve against real data.
- [`psycopg2-binary` is a binary wheel convenience package, not recommended for production by its own docs (prefers building `psycopg2` from source in prod)] → Acceptable for this stage of the project (per the requirements doc's own 4-week solo-build framing); revisit before any production hardening pass.
