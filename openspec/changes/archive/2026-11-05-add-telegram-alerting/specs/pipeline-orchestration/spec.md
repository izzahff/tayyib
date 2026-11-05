## ADDED Requirements

### Requirement: Pipeline-Wide Failure Sends an Alert
WHEN a pipeline-wide failure marks a run incomplete, THEN the system SHALL send a failure alert for that run through the alerting capability.

#### Scenario: Failed run sends an alert
- **WHEN** a pipeline-wide failure marks a run incomplete
- **THEN** a failure alert for that run is sent
