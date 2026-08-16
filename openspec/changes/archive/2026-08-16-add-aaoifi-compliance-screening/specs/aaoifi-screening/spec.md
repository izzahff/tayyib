## Purpose

Determines whether a given stock ticker is Shariah-compliant under the AAOIFI two-ratio financial screen, using financial statement data and configurable thresholds.

## ADDED Requirements

### Requirement: Debt Ratio Screening
The system SHALL compute a ticker's debt ratio as total liabilities divided by total assets, using the FTSE/MSCI total-assets convention rather than AAOIFI's market-capitalization basis. The numerator SHALL be FMP's `totalLiabilities` field (all liabilities, including non-interest-bearing items such as accounts payable and deferred revenue), not FMP's `totalDebt` field (interest-bearing debt only). The system SHALL fail the ticker on this ratio when the computed value strictly exceeds the configured `debt_ratio_threshold`; a value equal to the threshold SHALL pass.

#### Scenario: Debt ratio within threshold
- **WHEN** a ticker's total liabilities divided by total assets is less than or equal to `debt_ratio_threshold`
- **THEN** the ticker passes the debt ratio test

#### Scenario: Debt ratio exceeds threshold
- **WHEN** a ticker's total liabilities divided by total assets is strictly greater than `debt_ratio_threshold`
- **THEN** the ticker fails the debt ratio test

#### Scenario: Debt ratio exactly at threshold
- **WHEN** a ticker's total liabilities divided by total assets is exactly equal to `debt_ratio_threshold`
- **THEN** the ticker passes the debt ratio test

### Requirement: Non-Permissible Income Ratio Screening
The system SHALL compute a ticker's non-permissible income ratio as non-permissible income divided by total revenue, where non-permissible income is the sum of FMP's `interestIncome` and `totalOtherIncomeExpensesNet` income-statement fields, and total revenue is FMP's `revenue` field. This collapses AAOIFI Standard 21's ratio #2 (interest-bearing deposits and investments / market cap) and ratio #3 (non-permissible income / total revenue) into a single check, since a reliable data source for ratio #2 is not available from FMP's free tier. The system SHALL fail the ticker on this ratio when the computed value strictly exceeds the configured `non_permissible_income_threshold`; a value equal to the threshold SHALL pass.

#### Scenario: Non-permissible income ratio within threshold
- **WHEN** a ticker's non-permissible income divided by total revenue is less than or equal to `non_permissible_income_threshold`
- **THEN** the ticker passes the non-permissible income test

#### Scenario: Non-permissible income ratio exceeds threshold
- **WHEN** a ticker's non-permissible income divided by total revenue is strictly greater than `non_permissible_income_threshold`
- **THEN** the ticker fails the non-permissible income test

#### Scenario: Non-permissible income ratio exactly at threshold
- **WHEN** a ticker's non-permissible income divided by total revenue is exactly equal to `non_permissible_income_threshold`
- **THEN** the ticker passes the non-permissible income test

### Requirement: Financial Data Retrieval and Missing-Data Handling
The system SHALL retrieve, for a given ticker, the total assets, total liabilities, revenue, interest income, and other non-operating income figures needed to compute both ratios from the configured financial data provider (FMP). The system SHALL distinguish a field that is absent (`None`) from the provider's response from a field with a real value of `0`: an absent field SHALL cause the ticker to be marked "unscreened," while a `0` value SHALL be treated as valid data and used in the calculation normally, except for `revenue`. If `revenue` is absent (`None`) or explicitly `0`, the system SHALL mark the ticker "unscreened" with reason "revenue is zero, cannot compute non-permissible income ratio" in either case, to avoid a division by zero; this reason is distinct from the general "insufficient data for non-permissible income calculation" reason, which applies only when `revenue` itself is present and non-zero but `interestIncome` or `totalOtherIncomeExpensesNet` is absent. When both a balance-sheet-side reason and a non-permissible-income-side reason apply to the same ticker, the system SHALL report both reasons together, not just one.

#### Scenario: Required figures available and screened normally
- **WHEN** the financial data provider returns non-`None` values for total assets, total liabilities, revenue, interest income, and other non-operating income for a ticker, and `revenue` is not `0`
- **THEN** the system computes both ratios and produces a compliance classification for that ticker

#### Scenario: A figure is legitimately zero
- **WHEN** `interestIncome`, `totalOtherIncomeExpensesNet`, total assets, or total liabilities is present with a real value of `0` (not absent)
- **THEN** the system treats it as valid data and uses it in the relevant ratio calculation

#### Scenario: An income-statement figure other than revenue is absent from the provider response
- **WHEN** `interestIncome` or `totalOtherIncomeExpensesNet` is absent (`None`) from the data provider's response for a ticker, and `revenue` is present and non-zero
- **THEN** the system marks the ticker "unscreened" with reason "insufficient data for non-permissible income calculation"

#### Scenario: A required balance-sheet figure is absent from the provider response
- **WHEN** total assets or total liabilities is absent (`None`) from the data provider's response for a ticker
- **THEN** the system marks the ticker "unscreened" with reason "insufficient data for debt ratio calculation"

#### Scenario: Revenue is missing or zero
- **WHEN** a ticker's `revenue` field is absent (`None`) or is present with a value of `0`
- **THEN** the system marks the ticker "unscreened" with reason "revenue is zero, cannot compute non-permissible income ratio," regardless of whether `interestIncome` or `totalOtherIncomeExpensesNet` are present

#### Scenario: Both balance-sheet-side and non-permissible-income-side data are missing
- **WHEN** a required balance-sheet field (total assets or total liabilities) is absent for a ticker, together with either an absent `interestIncome`/`totalOtherIncomeExpensesNet` (while `revenue` is present and non-zero) or an absent/zero `revenue`
- **THEN** the system marks the ticker "unscreened" and reports "insufficient data for debt ratio calculation" together with whichever applies of "insufficient data for non-permissible income calculation" or "revenue is zero, cannot compute non-permissible income ratio"

### Requirement: Overall Compliance Classification
The system SHALL classify each ticker as exactly one of: compliant, non-compliant, or unscreened. A ticker that fails the debt ratio test SHALL be classified non-compliant with reason "debt ratio exceeded." A ticker that fails the non-permissible income test SHALL be classified non-compliant with reason "non-permissible income exceeded." A ticker that fails both tests SHALL be classified non-compliant citing both reasons. A ticker that passes both tests SHALL be classified compliant. A ticker for which either ratio cannot be computed due to missing data SHALL be classified unscreened, and SHALL NOT be classified compliant or non-compliant.

#### Scenario: Ticker passes both ratio tests
- **WHEN** a ticker passes the debt ratio test and passes the non-permissible income test
- **THEN** the system classifies the ticker as compliant

#### Scenario: Ticker fails the debt ratio test
- **WHEN** a ticker fails the debt ratio test
- **THEN** the system classifies the ticker as non-compliant with reason "debt ratio exceeded"

#### Scenario: Ticker fails the non-permissible income test
- **WHEN** a ticker fails the non-permissible income test
- **THEN** the system classifies the ticker as non-compliant with reason "non-permissible income exceeded"

#### Scenario: Ticker fails both ratio tests
- **WHEN** a ticker fails both the debt ratio test and the non-permissible income test
- **THEN** the system classifies the ticker as non-compliant with reasons "debt ratio exceeded" and "non-permissible income exceeded"

#### Scenario: Ticker cannot be screened due to missing data
- **WHEN** required financial data for either ratio is unavailable for a ticker
- **THEN** the system classifies the ticker as unscreened and excludes it from both the compliant and non-compliant classifications

### Requirement: Configurable Thresholds
The system SHALL read `debt_ratio_threshold` and `non_permissible_income_threshold` from application settings at evaluation time, so that operators can change either threshold without modifying code.

#### Scenario: Default thresholds applied
- **WHEN** no threshold override is provided in the environment or `.env` file
- **THEN** the system uses a debt ratio threshold of 0.30 and a non-permissible income threshold of 0.05

#### Scenario: Threshold overridden via settings
- **WHEN** an operator sets a different value for `debt_ratio_threshold` or `non_permissible_income_threshold` via the environment or `.env` file
- **THEN** the system uses the overridden value when evaluating tickers
