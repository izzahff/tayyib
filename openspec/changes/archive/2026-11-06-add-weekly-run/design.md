## Context

See proposal.md. `run_screening_pipeline` and `run_ranking_pipeline` already exist and each handle their own failures and failure alerts.

## Decisions

**Decision: `weekly.py` only sequences the existing functions.** Failure handling already lives inside them, so the weekly run adds none of its own.

**Decision: previous list comes from the latest completed ranking run before the current one.** Incomplete runs never count as a baseline.

**Decision: the summary is plain text.** Same reason as failure alerts, Markdown can break on odd characters.

**Decision: discovery data lives in `free_plan_constituents.csv`.** The same file format and validator as the S&P 500 list.

## Risks / Trade-offs

- [The free-plan file is a snapshot] -> Rerun the discovery script when the plan changes.
