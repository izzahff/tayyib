## ADDED Requirements

### Requirement: Resolving the Free Plan Universe
The system SHALL resolve the "free-plan" universe source into the validated tickers stored from the free plan discovery, and SHALL fail fast if that data is missing or invalid.

#### Scenario: Free plan source resolves
- **WHEN** the universe source is "free-plan" and the discovery data exists and is valid
- **THEN** the system returns those tickers

#### Scenario: Free plan data is missing
- **WHEN** the universe source is "free-plan" and the discovery data does not exist
- **THEN** the system raises an error describing the problem
