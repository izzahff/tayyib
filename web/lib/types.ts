export type Classification = "compliant" | "non-compliant" | "unscreened";

export type Run = {
  id: number;
  step: string;
  status: string;
  startedAt: string;
  completedAt: string | null;
  failureReason: string | null;
};

export type Target = {
  rank: number;
  ticker: string;
  score: number;
  weight: number;
};

export type ScreeningRow = {
  ticker: string;
  classification: Classification;
  debtRatio: number | null;
  incomeRatio: number | null;
  reasons: string[];
};

export type Overview = {
  screeningRun: Run | null;
  rankingRun: Run | null;
  targets: Target[];
  counts: Record<Classification, number>;
  demo: boolean;
};
