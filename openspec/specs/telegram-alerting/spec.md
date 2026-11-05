# telegram-alerting Specification

## Purpose
Delivers messages to the user's Telegram chat so a failed pipeline run reaches the user without them checking the database.

## Requirements

### Requirement: Sending a Telegram Message
The system SHALL send a text message to the configured Telegram chat using the configured bot token, and SHALL report whether delivery succeeded.

#### Scenario: A message is delivered
- **WHEN** a message is sent while a bot token and chat identifier are configured and Telegram accepts the request
- **THEN** the system reports success

#### Scenario: Telegram rejects or cannot be reached
- **WHEN** Telegram returns an error or the request fails
- **THEN** the system reports failure and does not raise an error to the caller

### Requirement: Unconfigured Alerting Is Skipped
IF the bot token or chat identifier is not configured, THEN the system SHALL skip sending, make no network request, and report failure.

#### Scenario: No token configured
- **WHEN** a message is sent while the bot token is empty
- **THEN** the system makes no network request and reports failure

### Requirement: Failure Alert Content
The system SHALL format a failure alert that contains the run identifier, the step name, and the recorded failure reason.

#### Scenario: A failure alert is formatted
- **WHEN** a failure alert is built for an incomplete run
- **THEN** the message contains the run identifier, the step name, and the failure reason

### Requirement: Pipeline Failure Triggers an Alert
WHEN a pipeline run ends incomplete because of a pipeline-wide failure, THEN the system SHALL send a failure alert, and SHALL NOT let an alert delivery problem change the run's recorded outcome.

#### Scenario: A pipeline-wide failure alerts the user
- **WHEN** a pipeline-wide failure marks a run incomplete
- **THEN** the system sends a failure alert for that run

#### Scenario: Alert delivery fails during a failed run
- **WHEN** a pipeline-wide failure occurs and the alert cannot be delivered
- **THEN** the run is still marked incomplete with its failure reason and no additional error is raised

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
