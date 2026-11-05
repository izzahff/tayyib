import { formatDateTime, formatDuration } from "@/lib/format";
import { getRuns } from "@/lib/queries";

export const dynamic = "force-dynamic";

export default async function Runs() {
  const { runs, demo } = await getRuns();

  return (
    <>
      {demo && <p className="banner">Sample data. These are not real runs.</p>}
      <h1 className="title">Every run, including the ones that failed</h1>
      <p className="lede">
        Each step of the job records when it started, how it ended, and why it stopped if it did
        not finish. A failed run also sends a Telegram alert.
      </p>

      {runs.length === 0 ? (
        <div className="empty">
          <p style={{ margin: 0 }}>
            No runs recorded yet. Run <code>uv run python -m tayyib.weekly</code> to create one.
          </p>
        </div>
      ) : (
        <ul className="runs">
          {runs.map((run) => (
            <li key={run.id} className="run">
              <span className="run-id">Run {run.id}</span>
              <span>{run.step === "screening" ? "Screening" : run.step === "ranking" ? "Ranking" : run.step}</span>
              <span className={`status-${run.status}`}>
                {run.status === "incomplete" ? "Failed" : run.status === "completed" ? "Completed" : "Started"}
              </span>
              <span className="run-detail">
                {formatDateTime(run.startedAt)}, took {formatDuration(run.startedAt, run.completedAt)}
                {run.failureReason ? `. Reason: ${run.failureReason}` : ""}
              </span>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
