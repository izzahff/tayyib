import Link from "next/link";
import { Gauge } from "@/components/Gauge";
import { DEBT_LIMIT, INCOME_LIMIT } from "@/lib/constants";
import { formatDateTime, verdictLabel } from "@/lib/format";
import { getScreening } from "@/lib/queries";
import type { Classification } from "@/lib/types";

export const dynamic = "force-dynamic";

const filters: { value: Classification | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "compliant", label: "Compliant" },
  { value: "non-compliant", label: "Not compliant" },
  { value: "unscreened", label: "Not screened" },
];

export default async function Screening({
  searchParams,
}: {
  searchParams: Promise<{ show?: string }>;
}) {
  const { show } = await searchParams;
  const active = filters.find((item) => item.value === show)?.value ?? "all";
  const { run, rows, demo } = await getScreening();
  const visible = active === "all" ? rows : rows.filter((row) => row.classification === active);

  return (
    <>
      {demo && <p className="banner">Sample data. These are not real screening results.</p>}
      <h1 className="title">Every stock, with the numbers behind its verdict</h1>
      <p className="lede">
        {run
          ? `Results from screening run ${run.id}, finished on ${formatDateTime(run.completedAt)}. The dark tick on each bar marks the limit. A stock sitting exactly on the limit passes.`
          : "No screening run has finished yet."}
      </p>

      <div className="filters" role="group" aria-label="Filter by verdict">
        {filters.map((item) => (
          <Link
            key={item.value}
            href={item.value === "all" ? "/screening" : `/screening?show=${item.value}`}
            aria-current={active === item.value ? "true" : undefined}
          >
            {item.label}
          </Link>
        ))}
      </div>

      {visible.length === 0 ? (
        <div className="empty">
          <p style={{ margin: 0 }}>
            {rows.length === 0
              ? "Nothing to show yet. Run the weekly job to create the first screening results."
              : "No stocks match this filter in the latest run."}
          </p>
        </div>
      ) : (
        <ul className="rows">
          {visible.map((row) => (
            <li key={row.ticker} className="row">
              <span className="row-ticker">{row.ticker}</span>
              <span className={`verdict verdict-${row.classification}`}>
                {verdictLabel(row.classification)}
              </span>
              <Gauge label="Debt to assets" value={row.debtRatio} limit={DEBT_LIMIT} />
              <Gauge label="Non-permissible income" value={row.incomeRatio} limit={INCOME_LIMIT} />
              {row.reasons.length > 0 && (
                <ul className="reasons">
                  {row.reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
