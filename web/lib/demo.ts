import type { Overview, Run, ScreeningRow } from "./types";

// Sample data for local design checks only. It appears when DASHBOARD_DEMO=1 and
// the page shows a banner saying so. These are not real screening results.
const run = (id: number, step: string, status: string, failure: string | null = null): Run => ({
  id,
  step,
  status,
  startedAt: "2026-11-06T01:00:00Z",
  completedAt: status === "started" ? null : "2026-11-06T01:02:10Z",
  failureReason: failure,
});

export const demoRuns: Run[] = [
  run(4, "ranking", "completed"),
  run(3, "screening", "completed"),
  run(2, "ranking", "incomplete", "no completed screening run found"),
  run(1, "screening", "incomplete", "db hiccup"),
];

export const demoScreening: ScreeningRow[] = [
  { ticker: "XOM", classification: "compliant", debtRatio: 0.21, incomeRatio: 0.004, reasons: [] },
  { ticker: "GE", classification: "compliant", debtRatio: 0.29, incomeRatio: 0.012, reasons: [] },
  { ticker: "HCA", classification: "compliant", debtRatio: 0.3, incomeRatio: 0.0, reasons: [] },
  { ticker: "F", classification: "non-compliant", debtRatio: 0.74, incomeRatio: 0.031, reasons: ["debt ratio exceeded"] },
  { ticker: "GS", classification: "non-compliant", debtRatio: 0.88, incomeRatio: 0.21, reasons: ["debt ratio exceeded", "non-permissible income exceeded"] },
  { ticker: "FDX", classification: "unscreened", debtRatio: null, incomeRatio: 0.01, reasons: ["insufficient data for debt ratio calculation"] },
];

export const demoOverview: Overview = {
  screeningRun: demoRuns[1],
  rankingRun: demoRuns[0],
  targets: [
    { rank: 1, ticker: "GE", score: 0.312, weight: 1 / 3 },
    { rank: 2, ticker: "XOM", score: 0.118, weight: 1 / 3 },
    { rank: 3, ticker: "HCA", score: -0.024, weight: 1 / 3 },
  ],
  counts: { compliant: 3, "non-compliant": 2, unscreened: 1 },
  demo: true,
};
