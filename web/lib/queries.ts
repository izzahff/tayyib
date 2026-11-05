import { getPool } from "./db";
import { demoOverview, demoRuns, demoScreening } from "./demo";
import type { Classification, Overview, Run, ScreeningRow, Target } from "./types";

const isDemo = () => process.env.DASHBOARD_DEMO === "1";

type RunRow = {
  id: number;
  step_name: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  failure_reason: string | null;
};

const toRun = (row: RunRow): Run => ({
  id: row.id,
  step: row.step_name,
  status: row.status,
  startedAt: row.started_at,
  completedAt: row.completed_at,
  failureReason: row.failure_reason,
});

async function latestRun(step: string, completedOnly: boolean): Promise<Run | null> {
  const { rows } = await getPool().query<RunRow>(
    `select * from pipeline_runs
     where step_name = $1 ${completedOnly ? "and status = 'completed'" : ""}
     order by id desc limit 1`,
    [step],
  );
  return rows[0] ? toRun(rows[0]) : null;
}

export async function getOverview(): Promise<Overview> {
  if (isDemo()) return demoOverview;

  const [screeningRun, rankingRun] = await Promise.all([
    latestRun("screening", true),
    latestRun("ranking", true),
  ]);

  const targets: Target[] = rankingRun
    ? (
        await getPool().query<{ rank: number; ticker: string; score: number; weight: number }>(
          `select rank, ticker, score, weight from target_portfolio
           where pipeline_run_id = $1 order by rank`,
          [rankingRun.id],
        )
      ).rows
    : [];

  const counts: Record<Classification, number> = {
    compliant: 0,
    "non-compliant": 0,
    unscreened: 0,
  };
  if (screeningRun) {
    const result = await getPool().query<{ classification: Classification; total: string }>(
      `select classification, count(*) as total from screening_results
       where pipeline_run_id = $1 group by classification`,
      [screeningRun.id],
    );
    for (const row of result.rows) counts[row.classification] = Number(row.total);
  }

  return { screeningRun, rankingRun, targets, counts, demo: false };
}

export async function getScreening(): Promise<{ run: Run | null; rows: ScreeningRow[]; demo: boolean }> {
  if (isDemo()) return { run: demoRuns[1], rows: demoScreening, demo: true };

  const run = await latestRun("screening", true);
  if (!run) return { run: null, rows: [], demo: false };

  const { rows } = await getPool().query<{
    ticker: string;
    classification: Classification;
    debt_ratio: number | null;
    non_permissible_income_ratio: number | null;
    reasons: string[] | null;
  }>(
    `select ticker, classification, debt_ratio, non_permissible_income_ratio, reasons
     from screening_results where pipeline_run_id = $1 order by ticker`,
    [run.id],
  );

  return {
    run,
    demo: false,
    rows: rows.map((row) => ({
      ticker: row.ticker,
      classification: row.classification,
      debtRatio: row.debt_ratio,
      incomeRatio: row.non_permissible_income_ratio,
      reasons: row.reasons ?? [],
    })),
  };
}

export async function getRuns(): Promise<{ runs: Run[]; demo: boolean }> {
  if (isDemo()) return { runs: demoRuns, demo: true };
  const { rows } = await getPool().query<RunRow>(
    "select * from pipeline_runs order by id desc limit 40",
  );
  return { runs: rows.map(toRun), demo: false };
}
