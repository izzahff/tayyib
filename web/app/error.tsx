"use client";

export default function ErrorPage({ reset }: { error: Error; reset: () => void }) {
  return (
    <>
      <h1 className="title">The dashboard cannot reach its data</h1>
      <div className="empty">
        <p style={{ marginTop: 0 }}>
          Check that <code>DATABASE_URL</code> is set in the Vercel environment variables and
          points to the Supabase transaction pooler. Then try again.
        </p>
        <button type="button" onClick={reset}>
          Try again
        </button>
      </div>
    </>
  );
}
