"use client";

export function LoadingCard({ label = "Loading" }: { label?: string }) {
  return (
    <div className="card flex items-center gap-3 text-sm" role="status" aria-live="polite">
      <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-nv-green border-t-transparent" aria-hidden />
      <span>
        {label}… <span className="text-[var(--muted)]">first request after idle wakes the server (~10 s).</span>
      </span>
    </div>
  );
}

export function ErrorCard({ error, retry, title = "Something went wrong" }: { error: string; retry?: () => void; title?: string }) {
  return (
    <div className="card border-amber-400/40 text-sm" role="alert">
      <h2 className="font-semibold text-amber-200">{title}</h2>
      <p className="mt-2 text-[var(--muted)]">{error}</p>
      <div className="mt-3 flex gap-2">
        {retry && (
          <button className="btn" type="button" onClick={retry}>
            Retry
          </button>
        )}
        <a className="btn-ghost" href="/setup">
          Check go-live status
        </a>
      </div>
    </div>
  );
}
