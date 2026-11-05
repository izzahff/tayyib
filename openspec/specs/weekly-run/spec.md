# weekly-run Specification

## Purpose
Runs the full Tayyib job in the right order so one command produces a screening result, a ranked target list and a summary alert.

## Requirements

### Requirement: Ordered Weekly Run
The system SHALL run screening over the configured universe first, and SHALL run ranking only if the screening run completed.

#### Scenario: Screening completes
- **WHEN** the screening run completes
- **THEN** the ranking run starts

#### Scenario: Screening ends incomplete
- **WHEN** the screening run ends incomplete
- **THEN** ranking does not run and no summary is sent

### Requirement: Summary After Ranking
WHEN the ranking run completes, THEN the system SHALL send the weekly summary alert.

#### Scenario: Ranking completes
- **WHEN** the ranking run completes
- **THEN** a weekly summary is sent

#### Scenario: Ranking ends incomplete
- **WHEN** the ranking run ends incomplete
- **THEN** no weekly summary is sent, because the failure alert already went out
