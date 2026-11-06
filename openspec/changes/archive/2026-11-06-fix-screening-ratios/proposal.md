## Why

The first live run on 6 November 2026 screened 25 stocks and passed only AMD. Two flaws in the ratios caused most of the damage.

The debt ratio divided total liabilities by total assets. Total liabilities includes accounts payable, deferred revenue and other items that carry no interest, so the screen called Apple 72% "debt" and Costco 60%. AAOIFI Standard 21 counts only interest-bearing debt, and the dashboard labels the ratio "Debt to assets", so the label and the formula disagreed.

The non-permissible income ratio added interest income to the net of other non-operating items. When that net figure was a loss, it cancelled out real interest income. ABBV scored -21.6% and passed the income test for that reason alone.

## What Changes

- The debt ratio uses FMP's `totalDebt` (interest-bearing debt) divided by `totalAssets`. Both come from the balance-sheet call Tayyib already makes, so the FMP call budget stays the same.
- The non-permissible income ratio adds only the positive part of `interestIncome` and the positive part of `totalOtherIncomeExpensesNet`. A loss counts as zero, so it can no longer hide interest income, and the ratio can never go negative.
- The missing-data rules now name `totalDebt` in place of `totalLiabilities`. The six reason strings stay the same.
- The dashboard Method page and the README methodology table describe the new formulas.

## Capabilities

### Modified Capabilities
- `aaoifi-screening`: new debt ratio numerator, income floored at zero, updated data retrieval requirement.

## Impact

- Code: `src/tayyib/data/fmp.py`, `src/tayyib/screening/aaoifi.py`, `web/app/methodology/page.tsx`, `README.md`.
- Tests: `tests/test_aaoifi_screening.py`, `tests/test_fmp_client.py`, `tests/test_pipeline.py`.
- Database: no schema change. Old runs keep the ratios they stored. The next screening run writes new results under the new rules.
