## Context

See proposal.md. Supabase's Data API is switched off, so supabase-js cannot read the tables. The tables are written by the Python job.

## Decisions

**Decision: server components query Postgres with `pg` using the pooler URL.** The URL stays on the server, and no API layer is needed for a read-only view.

**Decision: pages render on demand.** The build must not need a database, and the data changes weekly, so freshness matters more than caching.

**Decision: ratios are drawn as gauges with a tick at the limit.** The product is two ratios against two limits, so the gauge shows how close a stock sits to the line, not only pass or fail.

**Decision: limits are constants in `web/lib/constants.ts` that mirror the Python settings.** A comment names the Python file to keep them in step.

**Decision: TypeScript pinned to 5.x.** Next 15 does not build with TypeScript 7.

**Decision: sample data behind `DASHBOARD_DEMO=1`.** It lets the design be checked without real results and always shows a banner.

## Risks / Trade-offs

- [Limits drift from the Python settings] -> A comment in both places, and a later change can serve them from the database.
- [Pooler certificate is not trusted by Node] -> The connection uses TLS with certificate verification relaxed for the pooler only.
