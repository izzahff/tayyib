## Purpose

Shows the latest ranked list, every screening verdict with its numbers, and the run history, so results can be read without querying the database.

## ADDED Requirements

### Requirement: Current Ranked List
The dashboard SHALL show the target list from the latest completed ranking run, with each ticker's rank, momentum score and weight, and SHALL state when that run finished.

#### Scenario: A ranked list exists
- **WHEN** a completed ranking run has targets
- **THEN** the dashboard lists them in rank order with score, weight and the run's finish time

#### Scenario: No ranked list yet
- **WHEN** no completed ranking run exists
- **THEN** the dashboard says no list exists yet and names the command that creates one

### Requirement: Screening Results With Their Numbers
The dashboard SHALL show every ticker from the latest completed screening run with its verdict, both ratios against their limits, and its recorded reasons, and SHALL let the user filter by verdict.

#### Scenario: Ratios are shown against limits
- **WHEN** a screening result has both ratios
- **THEN** each ratio is shown with its value and its limit, and a failing ratio is visibly distinct from a passing one

#### Scenario: Missing data is not shown as a number
- **WHEN** a ratio is missing
- **THEN** the dashboard shows "no data" for it and never a zero

#### Scenario: Filtering
- **WHEN** the user chooses a verdict filter
- **THEN** only tickers with that verdict are listed

### Requirement: Run History
The dashboard SHALL list recent pipeline runs with step, outcome, start time, duration and failure reason.

#### Scenario: A failed run
- **WHEN** a run ended incomplete
- **THEN** it is shown as failed with its recorded reason

### Requirement: Read-Only and Private Connection
The dashboard SHALL only read data, and SHALL keep the database connection on the server.

#### Scenario: No browser access to the database
- **WHEN** a page loads
- **THEN** no database URL or query is sent to the browser

### Requirement: Clear Failure and Sample Data
IF the database cannot be reached, THEN the dashboard SHALL say so and name the setting to check. Sample data SHALL only appear when explicitly enabled and SHALL be labelled as sample data.

#### Scenario: Database unreachable
- **WHEN** a query fails
- **THEN** the page explains the dashboard cannot reach its data and names DATABASE_URL

#### Scenario: Sample data is labelled
- **WHEN** sample data mode is on
- **THEN** every page shows a banner saying the data is not real
