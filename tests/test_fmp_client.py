from tayyib.data.fmp import parse_financial_statement_figures


def test_parses_complete_payload():
    balance_sheet = {"totalAssets": 1000.0, "totalLiabilities": 300.0}
    income_statement = {
        "revenue": 1000.0,
        "interestIncome": 10.0,
        "totalOtherIncomeExpensesNet": 5.0,
    }
    figures = parse_financial_statement_figures(balance_sheet, income_statement)
    assert figures.total_assets == 1000.0
    assert figures.total_liabilities == 300.0
    assert figures.revenue == 1000.0
    assert figures.interest_income == 10.0
    assert figures.other_non_operating_income == 5.0


def test_missing_field_becomes_none():
    balance_sheet = {"totalAssets": 1000.0}  # totalLiabilities absent
    income_statement = {
        "revenue": 1000.0,
        "interestIncome": 10.0,
        "totalOtherIncomeExpensesNet": 5.0,
    }
    figures = parse_financial_statement_figures(balance_sheet, income_statement)
    assert figures.total_liabilities is None


def test_zero_value_is_preserved_not_treated_as_missing():
    balance_sheet = {"totalAssets": 1000.0, "totalLiabilities": 300.0}
    income_statement = {
        "revenue": 1000.0,
        "interestIncome": 0.0,
        "totalOtherIncomeExpensesNet": 0.0,
    }
    figures = parse_financial_statement_figures(balance_sheet, income_statement)
    assert figures.interest_income == 0.0
    assert figures.other_non_operating_income == 0.0
