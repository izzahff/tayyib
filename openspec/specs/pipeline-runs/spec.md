# pipeline-runs Specification

## Purpose

Tracks the lifecycle of a pipeline run — started, completed, or incomplete — independent of which step is running, so any current or future pipeline step can record and query its own run history through one shared mechanism.

## Requirements

### Requirement: Starting a Pipeline Run
The system SHALL allow starting a new pipeline run for a given step name, recording the step name, a start timestamp, and an initial status of "started".

#### Scenario: A new run is started
- **WHEN** a step starts a pipeline run with a step name
- **THEN** the system creates a run record with that step name, a start timestamp, and status "started"

### Requirement: Marking a Run Complete
The system SHALL allow marking a started run as "completed", recording a completion timestamp.

#### Scenario: A run completes successfully
- **WHEN** a step marks a started run as complete
- **THEN** the system updates that run's status to "completed" and records a completion timestamp

### Requirement: Marking a Run Incomplete
The system SHALL allow marking a started run as "incomplete" when the step fails, recording a completion timestamp and a failure reason.

#### Scenario: A run fails and is marked incomplete
- **WHEN** a step marks a started run as incomplete, providing a failure reason
- **THEN** the system updates that run's status to "incomplete", records a completion timestamp, and stores the failure reason

### Requirement: Run Status Is Queryable
The system SHALL make it possible to retrieve a pipeline run's step name, status, start timestamp, and — once the run has ended — its completion timestamp and failure reason if any.

#### Scenario: Retrieving a run's status
- **WHEN** a caller retrieves a pipeline run by its identifier
- **THEN** the system returns the run's step name, status, start timestamp, and, if the run has ended, its completion timestamp and failure reason if one was recorded

### Requirement: Reusable Across Pipeline Steps
The system SHALL implement run tracking as a single mechanism usable with any step name, not hardcoded to a specific capability, so future steps can start, complete, or mark their own runs incomplete without introducing a separate tracking mechanism.

#### Scenario: A different step name uses the same mechanism
- **WHEN** a step other than screening (for example, ranking or alerting) starts, completes, or marks incomplete a pipeline run
- **THEN** the system records and updates that run using the same fields and behavior it uses for any other step name
