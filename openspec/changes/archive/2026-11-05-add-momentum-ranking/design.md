## Context

See proposal.md. FMP stable endpoint `historical-price-eod/dividend-adjusted` was checked against real output for AAPL. It returns a list, newest first, with `symbol`, `date`, `adjOpen`, `adjHigh`, `adjLow`, `adjClose`, `volume`.

## Decisions

**Decision: simple return on adjusted close.** It is easy to explain and audit. Adjusted close absorbs splits and dividends so returns are comparable.

**Decision: lookback counts trading records, not calendar days.** The score uses the record 126 positions back in the sorted series. The fetch window is 260 calendar days so a normal ticker always has enough records.

**Decision: sort ascending by date after fetch.** The API order is not part of the contract, so the parser sorts.

**Decision: the pure scoring and selection functions do no I/O.** Same pattern as screening, so tests need no network.

**Decision: two tables.** `factor_scores` stores every score or exclusion reason. `target_portfolio` stores the selected list. Auditing why a ticker was missing from the list needs the first table.

**Decision: reuse the pipeline failure pattern.** Only `FmpRequestError` is isolated per ticker. Anything else fails the run and alerts.

## Risks / Trade-offs

- [Free FMP plan covers about 87 tickers] -> Other tickers come back as "price data fetch failed", which is recorded rather than hidden.
- [A one-off bad price record skews a score] -> Accepted for a single-factor v1.
