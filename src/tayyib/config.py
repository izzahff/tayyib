from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Data Provider
    fmp_api_key: str
    fmp_base_url: str = "https://financialmodelingprep.com/stable"

    # Universe
    universe_source: str = "sp500"

    # AAOIFI Thresholds (two-ratio, per Requirements v3.0)
    debt_ratio_threshold: float = 0.30
    non_permissible_income_threshold: float = 0.05

    # Momentum
    momentum_lookback_days: int = 126
    top_n_tickers: int = 10

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Database
    database_url: str = "postgresql://shariah_user:password@localhost:5432/tayyib"

    # Dashboard
    dashboard_port: int = 8080

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()