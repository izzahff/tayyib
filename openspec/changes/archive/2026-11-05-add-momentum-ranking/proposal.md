## Why

Screening tells the user which stocks are compliant, but not which ones to look at first. Tayyib needs to rank compliant stocks by momentum and produce a top N equal-weight target list that the later alert and dashboard steps can read.

## What Changes

- Fetch dividend-adjusted daily closing prices from FMP for each compliant ticker of the most recent completed screening run.
- Compute a simple momentum score per ticker, the adjusted close today divided by the adjusted close N trading days earlier, minus 1. N comes from `momentum_lookback_days` (default 126).
- Rank by score from highest to lowest, break ties by ticker name, and select the top `top_n_tickers` (default 10) at equal weight.
- Persist every score, including excluded tickers with a fixed reason, and persist the target list, both linked to a pipeline run.
- Isolate failures per ticker. A ticker whose prices cannot be fetched, or that has too little history, is excluded with a fixed reason and the run continues.
- A pipeline-wide failure marks the run incomplete and sends a failure alert.

**Out of scope**
- Multi-factor models, backtesting, and portfolio drift against manual positions.
- Wiring screening and ranking together on a schedule.

## Capabilities

### New Capabilities
- `momentum-ranking`: Scores compliant tickers by momentum, selects a top N equal-weight target list, and persists scores and targets with an audit trail.

### Modified Capabilities

(none)

## Impact

- New module `src/tayyib/ranking.py`, new price fetch in `src/tayyib/data/fmp.py`, two new tables, new persistence functions, and a new `run_ranking_pipeline` in `src/tayyib/pipeline.py`.
