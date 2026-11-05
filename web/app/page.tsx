import Link from "next/link";
import { formatDateTime, signedPercent } from "@/lib/format";
import { getOverview } from "@/lib/queries";

export const dynamic = "force-dynamic";

export default async function Home() {
  const overview = await getOverview();
  const { screeningRun, rankingRun, targets, counts } = overview;
  const screened = counts.compliant + counts["non-compliant"] + counts.unscreened;

  return (
    <>
      {overview.demo && (
        <p className="banner">Sample data. These are not real screening results.</p>
      )}
      <h1 className="title">Compliant stocks, ranked by six-month momentum</h1>

      {screeningRun ? (
        <p className="lede">
          The last screening run finished on{" "}
          <strong>{formatDateTime(screeningRun.completedAt)}</strong> and checked{" "}
          <strong>{screened} stocks</strong>. <strong>{counts.compliant}</strong> passed both
          ratios, <strong>{counts["non-compliant"]}</strong> failed one, and{" "}
          <strong>{counts.unscreened}</strong> could not be screened because data was missing.{" "}
          <Link href="/screening">See every result</Link>.
        </p>
      ) : (
        <p className="lede">No screening run has finished yet.</p>
      )}

      <h2 className="section-title">This week&apos;s list</h2>
      {rankingRun && targets.length > 0 ? (
        <>
          <p className="section-note">
            Each compliant stock gets an equal share. Momentum is the return on the adjusted close
            over the last 126 trading days. Ranking run {rankingRun.id} finished on{" "}
            {formatDateTime(rankingRun.completedAt)}.
          </p>
          <ol className="picks">
            {targets.map((target) => (
              <li key={target.ticker} className="pick">
                <span className="pick-rank">{target.rank}</span>
                <span className="pick-ticker">{target.ticker}</span>
                <span className={`pick-score ${target.score >= 0 ? "gain" : "loss"}`}>
                  {signedPercent(target.score)}
                  <small>{(target.weight * 100).toFixed(1)}% weight</small>
                </span>
              </li>
            ))}
          </ol>
        </>
      ) : (
        <div className="empty">
          <p style={{ margin: 0 }}>
            No ranked list yet. Run <code>uv run python -m tayyib.weekly</code> to screen the
            universe and create the first one.
          </p>
        </div>
      )}
    </>
  );
}
