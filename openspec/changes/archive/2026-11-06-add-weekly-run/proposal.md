## Why

Screening, ranking and alerts exist as separate pieces. Nobody can run them as one weekly job, and the free FMP plan covers only part of the S&P 500, so the job needs a universe that fits the plan.

## What Changes

- Add one weekly run that resolves the configured universe, screens it, ranks the compliant tickers, and sends a Telegram summary.
- Ranking runs only after the screening run completes. If screening ends incomplete, ranking does not run.
- Add a "free-plan" universe source that reads the tickers found by the discovery script.
- Add a weekly summary message that lists the top picks and shows entries and exits against the previous ranking run.

**Out of scope**
- Scheduling the job (cron, GitHub Actions). That comes with deployment.
- Retry and backoff.

## Capabilities

### New Capabilities
- `weekly-run`: Runs screening, then ranking, then the summary alert as one ordered job.

### Modified Capabilities
- `ticker-universe`: Adds the "free-plan" universe source.
- `telegram-alerting`: Adds the weekly summary message.

## Impact

- New module `src/tayyib/weekly.py`, changes to `universe.py`, `alerts.py` and `persistence.py`.
