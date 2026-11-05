## 1. Prices

- [x] 1.1 Add `fetch_adjusted_closes` to fmp.py, sorted ascending, raising FmpRequestError on failure or empty data

## 2. Pure logic

- [x] 2.1 Add `momentum_score`, `MomentumScore`, `select_top` and reason constants in ranking.py

## 3. Storage

- [x] 3.1 Add `FactorScore` and `TargetPortfolio` tables
- [x] 3.2 Add persistence functions and `latest_compliant_tickers`

## 4. Pipeline

- [x] 4.1 Add `run_ranking_pipeline` with per-ticker isolation and failure alerting

## 5. Tests

- [x] 5.1 Scoring, thin history, tie-break, fewer than N, weights sum to 1
- [x] 5.2 Parser sorts and handles the real response shape
- [x] 5.3 Pipeline end to end, fetch failure isolation, no screening run, persistence failure alert
