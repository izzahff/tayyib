## Purpose

Resolves a configured universe source into a validated, non-empty list of ticker symbols, failing fast on misconfiguration or missing/invalid data rather than returning an empty or partially-valid list.

## ADDED Requirements

### Requirement: Resolving the S&P 500 Universe
The system SHALL resolve the `"sp500"` universe source into a list of ticker symbols read from a static, locally-stored data source, without making a live external API call.

#### Scenario: The sp500 source resolves to tickers from local data
- **WHEN** the universe source is `"sp500"`
- **THEN** the system returns a list of ticker symbols read from local data, without contacting any external API

### Requirement: Resolved Universe Lists Must Be Valid
The system SHALL reject a resolved ticker list that contains an empty or blank entry, or that contains the same ticker more than once, rather than silently dropping the offending entries.

#### Scenario: A blank entry fails validation
- **WHEN** a universe source's underlying data contains an empty or blank entry
- **THEN** the system raises an error rather than returning a list with that entry silently dropped

#### Scenario: A duplicate ticker fails validation
- **WHEN** a universe source's underlying data contains the same ticker symbol more than once
- **THEN** the system raises an error rather than returning a list with the duplicate silently collapsed

#### Scenario: A valid list passes through unchanged
- **WHEN** a universe source's underlying data contains no blank entries and no duplicate tickers
- **THEN** the system returns the resolved list unchanged

### Requirement: Failing Fast on an Unrecognized Universe Source
IF the configured universe source is not a recognized value, THEN the system SHALL raise an error identifying the unrecognized value, rather than returning an empty list.

#### Scenario: An unrecognized universe source raises
- **WHEN** universe resolution is requested for a universe source value the system does not recognize
- **THEN** the system raises an error naming the unrecognized value, and does not return an empty or partial list

### Requirement: Failing Fast on Missing or Empty Universe Data
IF the data backing a recognized universe source is missing or empty, THEN the system SHALL raise an error describing the problem, rather than returning an empty list.

#### Scenario: Missing data raises
- **WHEN** the data backing a recognized universe source cannot be found
- **THEN** the system raises an error describing the problem, rather than returning an empty list

#### Scenario: Empty data raises
- **WHEN** the data backing a recognized universe source exists but contains no ticker entries
- **THEN** the system raises an error describing the problem, rather than returning an empty list
