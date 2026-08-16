## 1. Data models

- [x] 1.1 Add a `FinancialStatementFigures` model (total assets, total liabilities, total revenue, interest income, other non-operating income) to represent the raw figures needed for AAOIFI screening
- [x] 1.2 Add an `AaoifiScreeningResult` model capturing per-ratio values, per-ratio pass/fail, overall classification (compliant / non-compliant / unscreened), and one or more fixed reason strings ("debt ratio exceeded", "non-permissible income exceeded", "insufficient data for debt ratio calculation", "insufficient data for non-permissible income calculation", "revenue is zero, cannot compute non-permissible income ratio")

## 2. FMP financial data client

- [x] 2.1 Add an FMP client function/module that fetches the balance-sheet statement for a ticker using `fmp_api_key` / `fmp_base_url` from `Settings`
- [x] 2.2 Add an FMP client function that fetches the income statement for a ticker
- [x] 2.3 Parse balance-sheet and income-statement responses into `FinancialStatementFigures`, distinguishing a field that is absent (`None`) from a field with a real value of `0`
- [x] 2.4 Surface HTTP/request failures as "unavailable," distinct from missing-field "unscreened" cases, per REQ 1.9a - do not conflate a failed fetch with incomplete data in logs or exceptions

## 3. AAOIFI ratio screening logic

- [x] 3.1 Implement debt ratio computation (total liabilities / total assets) with strict-exceed comparison against `debt_ratio_threshold`
- [x] 3.2 Implement non-permissible income computation (interest income + other non-operating income) and ratio (/ total revenue) with strict-exceed comparison against `non_permissible_income_threshold`
- [x] 3.3 Implement overall classification: compliant if both ratio tests pass; non-compliant with the applicable reason string(s) if either or both fail
- [x] 3.4 Wire threshold values from `Settings` (no hardcoded thresholds in screening logic)
- [x] 3.5 Handle missing/absent `FinancialStatementFigures` fields by returning "unscreened" with the applicable reason string(s) instead of a pass/fail; treat `revenue` as `None` or `0` identically - both produce "unscreened" with reason "revenue is zero, cannot compute non-permissible income ratio", distinct from the generic "insufficient data for non-permissible income calculation" reason used only when `interestIncome`/`totalOtherIncomeExpensesNet` is missing while `revenue` is present and non-zero; report both a balance-sheet-side and a non-permissible-income-side reason together when both apply
- [x] 3.6 Treat a field present with value `0` as valid data, not as missing

## 4. Tests

- [x] 4.1 Unit tests for debt ratio: below, exactly at, and above `debt_ratio_threshold`
- [x] 4.2 Unit tests for non-permissible income ratio: below, exactly at, and above `non_permissible_income_threshold`
- [x] 4.3 Unit tests for overall compliance: pass both, fail one, fail both
- [x] 4.4 Unit tests for custom thresholds overriding the defaults via `Settings`
- [x] 4.5 Unit tests for missing/absent figures producing "unscreened" with the correct reason string(s) (not a default pass or fail)
- [x] 4.6 Test FMP response parsing against representative sample payloads (including a payload missing an expected field)
- [x] 4.7 Unit tests for the `None`-vs-`0` distinction: a field present as `0` is screened normally, not treated as missing
- [x] 4.8 Unit tests for `revenue` being `None` and `revenue == 0` both producing "unscreened" with reason "revenue is zero, cannot compute non-permissible income ratio" (division-by-zero guard), and for both a balance-sheet-side and a non-permissible-income-side reason being reported together when both apply
