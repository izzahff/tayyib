# Tayyib (طيّب)

**Shariah-compliant stock screening, done properly.**

Tayyib is an alert-only stock screening system that applies AAOIFI Shariah compliance rules to a stock universe, ranks compliant stocks by momentum, and sends weekly Telegram alerts. It does not execute trades, you stay in control of every actual transaction.

The name comes from the Quranic concept of *tayyib*, that which is pure and good, beyond merely permissible. It reflects the aspiration this project is building toward: not just a minimum compliance check, but a standard that holds itself to a higher bar as it grows. Most Shariah screeners stop at the floor. The name is a reminder that v1 is just the compliance layer, not the ceiling.

## Status

Actively in development, solo build, 4-week timeline. Four of the planned capabilities are built, tested, and archived. They cover AAOIFI screening, screening result persistence, pipeline orchestration, and ticker universe resolution. This is not yet a complete system, see [what's built](#whats-built-so-far) below for exactly what works today versus what's still planned.

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
| Pipeline orchestration (screen → persist wiring) | ✅ Built, tested | Connects screening and persistence into one runnable pipeline, with per-ticker fetch-failure isolation (REQ 1.9) and pipeline-wide failure handling (REQ 3.4/4.3) |
| Ticker universe resolution | ✅ Built, tested, 100% coverage | Loads and validates the S&P 500 constituent list (503 tickers) from a checked-in file, and fails fast on a missing, empty, or malformed universe |
| Momentum factor ranking | ⬜ Not yet built | Ranks compliant tickers, generates an equal-weight target list |
| Telegram alerting | ⬜ Not yet built | Sends weekly alerts on new entries, exits, and pipeline failures |
| Dashboard | ⬜ Not yet built | Web view of compliance status, portfolio value, and audit history |

Every capability above is developed spec-first using [OpenSpec](https://github.com/Fission-AI/OpenSpec): requirements are written, reviewed, and locked before any code is generated. Archived specs for completed capabilities live in `openspec/changes/archive/`, and live specs for what's currently built are in `openspec/specs/`.

## Architecture

Tayyib runs as a one-way pipeline. Data comes in from two sources, passes through a deterministic screening step and a ranking step, and lands in a Postgres audit store. Alerts and the dashboard read from that store. Solid boxes are built and tested today. Dashed boxes are planned.

```mermaid
flowchart LR
    subgraph SRC[Data sources]
        CSV[S&P 500 list<br/>static CSV, 503 tickers]
        FMPF[FMP stable API<br/>financial statements]
        FMPP[FMP stable API<br/>price history]
    end

    subgraph ENG[Pipeline engine, Python 3.13]
        UNI[universe.py<br/>resolve and validate]
        PIPE[pipeline.py<br/>run_screening_pipeline]
        SCR[screening/aaoifi.py<br/>two-ratio AAOIFI screen]
        RANK[Momentum ranking]
        TGT[Target list<br/>top N, equal weight]
        ALERT[Alert builder]
    end

    subgraph DB[PostgreSQL 16, audit store]
        PR[(pipeline_runs)]
        SR[(screening_results)]
        FS[(factor_scores)]
        TP[(target_portfolio)]
        NAV[(nav_history)]
    end

    subgraph OUT[Outputs]
        TG[Telegram alerts]
        DASH[Web dashboard]
    end

    CSV --> UNI --> PIPE
    FMPF --> PIPE
    PIPE --> SCR --> PIPE
    PIPE --> PR
    PIPE --> SR
    SR --> RANK
    FMPP --> RANK
    RANK --> FS
    RANK --> TGT --> TP
    TP --> ALERT --> TG
    PR --> ALERT
    SR --> DASH
    TP --> DASH
    NAV --> DASH

    classDef planned stroke-dasharray: 5 5,fill:#f6f6f6,color:#555
    class RANK,TGT,ALERT,FS,TP,NAV,TG,DASH,FMPP planned
```

### How a run works

1. `resolve_universe()` reads the checked-in S&P 500 file and raises if it is missing, empty, blank, or duplicated.
2. `run_screening_pipeline()` opens a tracked run in `pipeline_runs`.
3. For each ticker, the pipeline fetches financial statements from FMP and calls the pure screening function.
4. The pipeline persists exactly one row per ticker in `screening_results`, whatever the outcome.
5. A failed fetch for one ticker records that ticker as unscreened with the reason "financial data fetch failed" and the run continues.
6. Any other failure stops the run and marks it incomplete with a reason, so no run stays stuck in "started".

### Design decisions that shape the code

| Decision | Why |
|---|---|
| Screening is a pure function with no I/O | Same input always gives the same output, and tests need no network or database |
| Three-way result with fixed reason strings | Missing data never turns into a silent pass or fail, and every outcome is auditable |
| Per-ticker isolation catches only `FmpRequestError` | One bad ticker cannot abort a run, while a systemic failure such as a dead database still stops it loudly |
| Static universe file instead of a live API call | The index changes rarely, and a live call would burn API quota on every run |
| No AI in the runtime path | A compliance decision has to be reproducible and explainable |
| Alert-only, no trade execution | The user stays in control of every transaction |

### Code map

| Path | Role |
|---|---|
| `src/tayyib/universe.py` | Universe resolution and validation |
| `src/tayyib/pipeline.py` | Run orchestration and failure handling |
| `src/tayyib/screening/aaoifi.py` | Two-ratio screen and reason vocabulary |
| `src/tayyib/data/fmp.py` | FMP client and statement parsing |
| `src/tayyib/storage/` | SQLModel tables, engine, and persistence functions |
| `openspec/specs/` | Live specs for every built capability |
| `openspec/changes/archive/` | Proposal, design, and task history for each change |

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
# Add your FMP API key to .env
uv run pytest
```

Start PostgreSQL with `docker compose up -d`. Telegram bot configuration is part of upcoming work, see [Status](#status) above.

## Disclaimer

Tayyib is a personal engineering project applying a documented, cited methodology. It is **not** a Shariah board ruling, fatwa, or religious authority. Individual scholars and jurisdictions may interpret screening criteria differently. Use this tool for research and education, not as a substitute for professional religious or financial advice.

Any performance figures shown by this system, now or in the future, are simulated. Past or simulated performance does not indicate future results.

## License

MIT
