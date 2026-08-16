## 1. Setup

- [x] 1.1 Add `psycopg2-binary` to `pyproject.toml` dependencies
- [x] 1.2 Create `src/tayyib/storage/` package (`__init__.py`, `models.py`, `engine.py`, `persistence.py`)

## 2. Table models

- [x] 2.1 Add `PipelineRun` SQLModel table: id, step_name, status ("started" / "completed" / "incomplete"), started_at, completed_at (nullable), failure_reason (nullable)
- [x] 2.2 Add `ScreeningResult` SQLModel table: id, pipeline_run_id (foreign key to `PipelineRun`), ticker, screening_date, debt_ratio (nullable float), non_permissible_income_ratio (nullable float), classification, reasons (`sa_type=ARRAY(String).with_variant(JSON(), "sqlite")` - native `text[]` on Postgres, JSON on SQLite)

## 3. Engine and session

- [x] 3.1 Add a module-level SQLModel engine built from `settings.database_url`
- [x] 3.2 Add a `get_session()` helper for opening a session against that engine
- [x] 3.3 Add a function to create all tables (`SQLModel.metadata.create_all(engine)`)

## 4. Persistence functions

- [x] 4.1 Add `start_pipeline_run(step_name)` - creates a `PipelineRun` with status "started" and a start timestamp, returns it
- [x] 4.2 Add `complete_pipeline_run(run_id)` - sets status "completed" and a completion timestamp
- [x] 4.3 Add `fail_pipeline_run(run_id, reason)` - sets status "incomplete", a completion timestamp, and the failure reason
- [x] 4.4 Add `persist_screening_result(run_id, ticker, screening_date, result: AaoifiScreeningResult)` - writes a `ScreeningResult` row linked to the run, mapping `result.classification`, `result.debt_ratio`, `result.non_permissible_income_ratio`, and `result.reasons` (as a `text[]` array, JSON under the SQLite test adapter) directly, without collapsing either ratio to null when only one side is unscreened

## 5. Tests

- [x] 5.1 Add a pytest fixture providing an in-memory SQLite engine/session for tests, independent of `settings.database_url`
- [x] 5.2 Unit tests for `start_pipeline_run`: step name, status "started", and start timestamp are recorded
- [x] 5.3 Unit tests for `complete_pipeline_run`: status becomes "completed" with a completion timestamp
- [x] 5.4 Unit tests for `fail_pipeline_run`: status becomes "incomplete" with a completion timestamp and the given failure reason
- [x] 5.5 Unit test that run tracking works identically for an arbitrary step name (e.g. "ranking"), not just "screening"
- [x] 5.6 Unit tests for `persist_screening_result` with a compliant result: both ratios and empty reasons persisted
- [x] 5.7 Unit tests for `persist_screening_result` with a non-compliant result: both ratios and one-or-two reasons persisted
- [x] 5.8 Unit tests for `persist_screening_result` with an unscreened result where only one ratio computed: the computed ratio is persisted (not nulled out) alongside the null ratio and the reason string(s)
- [x] 5.9 Unit test that a persisted screening result references its pipeline run's id
- [x] 5.10 Unit test that persisting results across two separate runs for the same ticker keeps both results retrievable and distinct (no overwrite)
