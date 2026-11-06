## Context

Screening run 1 used total liabilities for the debt ratio and a signed sum for non-permissible income. This change corrects both while keeping Tayyib's total-assets denominator and its free-plan call budget.

## Decisions

### Use `totalDebt`, keep the total-assets denominator
FMP's `totalDebt` adds short-term and long-term debt. It may include finance lease obligations, which AAOIFI scholars generally treat as interest-bearing, so including them errs on the strict side. Market capitalisation stays out of scope for the reasons the README already gives.

Alternative rejected: `totalLiabilities` minus non-interest items. FMP does not split those cleanly, and the result would depend on which fields a company reports.

### Floor each income component at zero
Non-permissible income = max(interestIncome, 0) + max(totalOtherIncomeExpensesNet, 0). Interest expense never makes earned interest permissible, so a net loss must not reduce the numerator.

Trade-off: `totalOtherIncomeExpensesNet` still mixes permissible and non-permissible items such as asset-sale gains. Counting the positive part as non-permissible errs on the strict side, the same direction as the debt choice.

### Keep a zero as data and an absent field as missing
`totalDebt` of 0 is a real value, common for debt-free companies, and produces a debt ratio of 0. An absent `totalDebt` marks the stock unscreened, as before.

## Risks

- Results change for every stock, so the first run under the new rules will show many entries and exits. The weekly summary reports these honestly.
