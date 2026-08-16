# Tayyib (طيّب)

**Shariah-compliant stock screening, done properly.**

Tayyib is an alert-only stock screening system that applies AAOIFI Shariah compliance rules to a stock universe, ranks compliant stocks by momentum, and sends weekly Telegram alerts. It does not execute trades, you stay in control of every actual transaction.

The name comes from the Quranic concept of *tayyib*, that which is pure and good, beyond merely permissible. It reflects the aspiration this project is building toward: not just a minimum compliance check, but a standard that holds itself to a higher bar as it grows. Most Shariah screeners stop at the floor. The name is a reminder that v1 is just the compliance layer, not the ceiling.

## Status

Actively in development, solo build, 4-week timeline. Two of six planned capabilities are built, tested, and archived. This is not yet a complete system, see [what's built](#whats-built-so-far) below for exactly what works today versus what's still planned.

## Features (target)

- **AAOIFI screening** — two-ratio implementation with fully documented methodology, deliberately scoped down from AAOIFI's strict three-ratio standard for data-availability reasons, and that deviation is cited, not hidden
- **Momentum ranking** — single-factor model, configurable lookback *(not yet built)*
- **Weekly Telegram alerts** — new entries, exits, action items *(not yet built)*
- **Simulated portfolio tracking** — benchmarked against SPUS *(not yet built)*
- **Audit trail** — every decision traceable to source data, with fixed, explicit reason strings for every non-compliant or unscreened outcome
- **Deterministic** — no AI in the runtime path, same input always produces the same output
- **Modern Python stack** — UV, SQLModel, Pydantic Settings, pytest, Ruff

## What's built so far

| Capability | Status | What it does |
|---|---|---|
| AAOIFI compliance screening | ✅ Built, tested, 100% coverage | Fetches financial data from FMP, computes two ratios, classifies a ticker as compliant, non-compliant, or unscreened with a fixed reason string |
| Screening result persistence | ✅ Built, tested | Stores every screening decision (including failures and unscreened tickers) in PostgreSQL, with generic pipeline-run lifecycle tracking reusable across future steps |
| Pipeline orchestration (screen → persist wiring) | ⬜ Not yet built | Connects screening and persistence into one runnable pipeline with per-ticker failure isolation |
| Momentum factor ranking | ⬜ Not yet built | Ranks compliant tickers, generates an equal-weight target list |
| Telegram alerting | ⬜ Not yet built | Sends weekly alerts on new entries, exits, and pipeline failures |
| Dashboard | ⬜ Not yet built | Web view of compliance status, portfolio value, and audit history |

Every capability above is developed spec-first using [OpenSpec](https://github.com/Fission-AI/OpenSpec): requirements are written, reviewed, and locked before any code is generated. Archived specs for completed capabilities live in `openspec/changes/archive/`, and live specs for what's currently built are in `openspec/specs/`.

## Methodology

Tayyib implements a **deliberately simplified two-ratio version** of AAOIFI Shariah Standard No. 21, which formally defines three ratios measured against market capitalization. This system uses two ratios measured against total assets instead, for two reasons: market cap is volatile and unreliable to compute from the free data tier this project uses, and AAOIFI's second ratio (interest-bearing deposits and investments) isn't cleanly exposed by that same data source.

| Ratio | Formula | Threshold | Basis |
|---|---|---|---|
| Debt ratio | total liabilities / total assets | 30% | FTSE/MSCI convention, not AAOIFI's market-cap basis |
| Non-permissible income | (interest income + other non-operating income) / total revenue | 5% | AAOIFI Standard 21, ratio expanded to absorb the deposits/investments ratio |

Every ticker is classified as **compliant**, **non-compliant**, or **unscreened**, never defaulted into a pass or fail when data is missing. Non-compliant and unscreened outcomes always carry one or more fixed reason strings, so any result is traceable back to the exact rule and data that produced it.

Boundary rule: a value equal to the threshold passes (strict-exceed, not inclusive-fail).

Full methodology, version history, and every decision's rationale is tracked as [OpenSpec](https://github.com/Fission-AI/OpenSpec) capabilities. See `openspec/specs/` for the current live specs, and `openspec/changes/archive/` for the full review history behind each one.

## Quick Start

```bash
git clone https://github.com/izzahff/tayyib.git
cd tayyib
uv sync
cp .env.example .env
# Add your FMP API key
uv run pytest
```

Database setup (PostgreSQL via Docker) and Telegram bot configuration are part of upcoming work, see [Status](#status) above.

## Disclaimer

Tayyib is a personal engineering project applying a documented, cited methodology. It is **not** a Shariah board ruling, fatwa, or religious authority. Individual scholars and jurisdictions may interpret screening criteria differently. Use this tool for research and education, not as a substitute for professional religious or financial advice.

Any performance figures shown by this system, now or in the future, are simulated. Past or simulated performance does not indicate future results.

## License

MIT
