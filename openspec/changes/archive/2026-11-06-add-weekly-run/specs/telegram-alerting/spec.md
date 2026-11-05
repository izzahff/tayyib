## ADDED Requirements

### Requirement: Weekly Summary Message
The system SHALL format a weekly summary that lists each target ticker with its rank, momentum score and weight, and lists tickers that entered or left the target list compared with the previous completed ranking run.

#### Scenario: Entries and exits are shown
- **WHEN** the current target list differs from the previous ranking run's list
- **THEN** the summary lists the tickers that entered and the tickers that left

#### Scenario: First run has no previous list
- **WHEN** no previous ranking run exists
- **THEN** the summary lists the targets and states that this is the first run

#### Scenario: Empty target list
- **WHEN** the target list is empty
- **THEN** the summary states that no compliant ticker could be ranked
