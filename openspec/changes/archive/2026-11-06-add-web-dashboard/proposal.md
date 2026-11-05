## Why

All results sit in the database. The user and any reviewer need a readable view of the current list, every screening verdict with its numbers, and the run history, without writing SQL.

## What Changes

- Add a read-only Next.js dashboard in `web/`, deployed on Vercel, reading directly from the Supabase Postgres database on the server.
- Pages for the current ranked list, every screening result with the two ratios shown against their limits, the run history including failed runs, and the methodology.
- The dashboard never writes to the database and never exposes the database URL to the browser.

**Out of scope**
- Sign-in, editing, and trade execution.
- Charts of portfolio performance, which need price history storage first.

## Capabilities

### New Capabilities
- `web-dashboard`: A read-only web view of the latest ranked list, screening results, run history and methodology.

### Modified Capabilities

(none)

## Impact

- New `web/` app, new CI workflow, new weekly scheduled workflow.
