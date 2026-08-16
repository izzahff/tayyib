# screening-persistence Specification

## Purpose

Persists AAOIFI screening results — ratios, classification, and reasons — per ticker per pipeline run, so past compliance decisions can be reconstructed for any prior date.

## Requirements

### Requirement: Persisting a Screening Result
The system SHALL persist, for a given ticker and pipeline run, the screening date, the debt ratio value, the non-permissible income ratio value, the classification (compliant, non-compliant, or unscreened), and the reason string(s) produced by AAOIFI screening. Either ratio value MAY be absent when the corresponding ratio could not be computed.

#### Scenario: A compliant ticker's result is persisted
- **WHEN** a ticker is screened and classified compliant, with both ratio values computed and no reasons
- **THEN** the system persists the ticker, date, both ratio values, classification "compliant", and no reasons

#### Scenario: A non-compliant ticker's result is persisted with its reasons
- **WHEN** a ticker is screened and classified non-compliant, with one or two exceeded-threshold reasons
- **THEN** the system persists the ticker, date, both ratio values, classification "non-compliant", and every reason produced

#### Scenario: An unscreened ticker's result is persisted with a partial or absent ratio
- **WHEN** a ticker is screened and classified unscreened, with one or both ratio values absent because required data was missing
- **THEN** the system persists the ticker, date, whichever ratio value(s) were computed, classification "unscreened", and the applicable insufficient-data reason string(s)

### Requirement: Screening Results Are Linked to a Pipeline Run
The system SHALL associate every persisted screening result with the pipeline run during which it was produced.

#### Scenario: A persisted result references its run
- **WHEN** a screening result is persisted
- **THEN** the system records which pipeline run produced that result, so results from different runs are never conflated

### Requirement: Screening Results Are Retained Indefinitely
The system SHALL retain persisted screening results indefinitely. No automatic deletion or pruning of screening results SHALL occur.

#### Scenario: Older results remain after newer runs are persisted
- **WHEN** a new pipeline run persists screening results for a ticker
- **THEN** screening results persisted by earlier runs for that ticker remain retrievable and unmodified

### Requirement: Reconstructing Past Compliance State
The system SHALL make it possible to retrieve a ticker's persisted screening results across multiple runs, each result distinct and attributed to its own run and date, so the compliance decision for any past date can be reconstructed.

#### Scenario: Retrieving a ticker's history across runs
- **WHEN** a ticker has been screened in more than one pipeline run
- **THEN** the system returns each run's result separately, with its own date, ratios, classification, and reasons, rather than only the most recent result
