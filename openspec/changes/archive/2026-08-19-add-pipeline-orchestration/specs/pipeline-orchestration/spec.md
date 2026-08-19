## Purpose

Runs AAOIFI screening across a list of tickers as one tracked pipeline run, persisting a result for every ticker and isolating per-ticker fetch failures from pipeline-wide failures.

## ADDED Requirements

### Requirement: Running a Screening Pipeline for a Ticker List
The system SHALL run AAOIFI screening for each ticker in a given list of ticker symbols as a single tracked pipeline run: starting the run, processing every ticker in the list, and ending the run in exactly one terminal status, "completed" or "incomplete".

#### Scenario: Running the pipeline for a list of tickers
- **WHEN** a screening pipeline run is started for a list of ticker symbols
- **THEN** the system processes every ticker in the list and ends the run as either "completed" or "incomplete"

### Requirement: Per-Ticker Fetch Failure Isolation
IF a ticker's financial data cannot be fetched at all, THEN the system SHALL NOT abort the pipeline run for the remaining tickers; it SHALL record that ticker as unscreened with reason "financial data fetch failed" and continue processing the remaining tickers in the list.

#### Scenario: One ticker's fetch fails among several
- **WHEN** a ticker's financial data fetch fails entirely during a pipeline run that includes other tickers
- **THEN** the system continues processing the remaining tickers in the list rather than aborting the run

#### Scenario: The failed ticker is still recorded, not silently dropped
- **WHEN** a ticker's financial data fetch fails entirely
- **THEN** the system records that ticker's result as unscreened with reason "financial data fetch failed", distinct from the reasons used when a fetch succeeds but specific fields are missing

### Requirement: Every Ticker Gets a Persisted Result
The system SHALL persist exactly one screening result per ticker in the input list, linked to the pipeline run, regardless of whether that ticker was classified compliant, non-compliant, unscreened due to missing fields, or unscreened due to a total fetch failure.

#### Scenario: Every outcome type is persisted
- **WHEN** a pipeline run processes a list of tickers whose outcomes include compliant, non-compliant, unscreened-due-to-missing-fields, and unscreened-due-to-fetch-failure results
- **THEN** the system persists one result per ticker, linked to that run, reflecting each ticker's actual outcome

### Requirement: Pipeline-Wide Failure Marks the Run Incomplete
IF a failure occurs during a pipeline run that is not an isolated per-ticker fetch failure - for example, a failure persisting a result that is not attributable to fetching or screening one specific ticker - THEN the system SHALL mark the run "incomplete" with a failure reason and SHALL stop processing further tickers, rather than leaving the run in "started" status or continuing past the failure.

#### Scenario: A pipeline-wide failure stops the run and marks it incomplete
- **WHEN** a failure occurs during a pipeline run that is not an isolated per-ticker fetch failure
- **THEN** the system marks the run "incomplete" with a failure reason and does not process any remaining tickers

#### Scenario: The run cannot be started at all
- **WHEN** a pipeline run cannot be started in the first place
- **THEN** no run record exists to mark incomplete, and the failure is surfaced to the caller rather than silently swallowed

### Requirement: Successful Completion
WHEN every ticker in the list has been processed without a pipeline-wide failure, THEN the system SHALL mark the run "completed".

#### Scenario: All tickers processed successfully
- **WHEN** every ticker in the input list has been processed and no pipeline-wide failure occurred
- **THEN** the system marks the run "completed"
