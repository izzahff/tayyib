# momentum-ranking Specification

## Purpose
Ranks Shariah-compliant tickers by price momentum and produces an equal-weight target list, so the user knows which compliant stocks to look at first.

## Requirements

### Requirement: Ranking Input
The system SHALL rank only the tickers classified compliant in the most recent completed screening run, and SHALL end the run incomplete with a failure reason if no completed screening run exists.

#### Scenario: Only compliant tickers are ranked
- **WHEN** the latest completed screening run holds compliant, non-compliant, and unscreened tickers
- **THEN** only the compliant tickers are scored

#### Scenario: No completed screening run
- **WHEN** no completed screening run exists
- **THEN** the ranking run ends incomplete with a failure reason

### Requirement: Momentum Score
The system SHALL score each ticker as its latest dividend-adjusted close divided by its dividend-adjusted close the configured number of trading days earlier, minus 1.

#### Scenario: Score is computed
- **WHEN** a ticker has an adjusted close of 120 now and 100 the configured number of trading days earlier
- **THEN** its score is 0.2

### Requirement: Insufficient History Is Excluded
IF a ticker has fewer price records than the lookback requires, THEN the system SHALL exclude it from ranking, record the reason "insufficient price history", and continue.

#### Scenario: Thin history
- **WHEN** a ticker has fewer than lookback plus one price records
- **THEN** it has no score, it is recorded with reason "insufficient price history", and other tickers are still ranked

### Requirement: Price Fetch Failure Isolation
IF prices for one ticker cannot be fetched, THEN the system SHALL exclude that ticker, record the reason "price data fetch failed", and continue with the remaining tickers.

#### Scenario: One fetch fails
- **WHEN** the price fetch fails for one ticker among several
- **THEN** that ticker is recorded with reason "price data fetch failed" and the run still completes

### Requirement: Top N Equal Weight Target List
The system SHALL rank scored tickers from highest score to lowest, break ties by ticker name in ascending order, select up to the configured top N, and give each selected ticker an equal weight that sums to 1.

#### Scenario: More candidates than slots
- **WHEN** more scored tickers exist than the configured top N
- **THEN** exactly the top N by score are selected, each with weight 1 divided by N

#### Scenario: Fewer candidates than slots
- **WHEN** fewer scored tickers exist than the configured top N
- **THEN** all scored tickers are selected, each with weight 1 divided by the number selected

#### Scenario: Equal scores
- **WHEN** two tickers have the same score
- **THEN** the one earlier in alphabetical order ranks higher

### Requirement: Persistence and Audit Trail
The system SHALL persist one score record per ticker considered, including excluded tickers with their reason, and one target record per selected ticker, all linked to the ranking run.

#### Scenario: Every ticker is recorded
- **WHEN** a ranking run finishes
- **THEN** every considered ticker has a score record and every selected ticker has a target record linked to the run

### Requirement: Pipeline-Wide Failure
IF a failure occurs that is not an isolated per-ticker price problem, THEN the system SHALL mark the run incomplete with a failure reason, stop, and send a failure alert.

#### Scenario: Database failure mid-run
- **WHEN** persisting a score fails during a ranking run
- **THEN** the run is marked incomplete with the failure reason and an alert is sent
