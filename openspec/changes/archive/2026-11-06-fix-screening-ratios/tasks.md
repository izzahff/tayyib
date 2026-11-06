## 1. Data

- [x] 1.1 Parse `totalDebt` into `FinancialStatementFigures.total_debt` in place of `total_liabilities`

## 2. Screening

- [x] 2.1 Compute the debt ratio as total debt divided by total assets
- [x] 2.2 Floor interest income and other non-operating income at zero before summing

## 3. Tests

- [x] 3.1 Update fixtures and parser tests to `totalDebt`
- [x] 3.2 Add tests for a negative other-income figure, negative interest income, and zero debt

## 4. Docs

- [x] 4.1 Update the dashboard Method page
- [x] 4.2 Update the README methodology table
