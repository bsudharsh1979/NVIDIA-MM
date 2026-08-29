import Link from "next/link";

export default function NotFound() {
  return (
    <div className="card max-w-xl space-y-3">
      <h1 className="text-xl font-semibold">Page not found</h1>
      <p className="text-sm text-[var(--muted)]">
        If this was a bookmarked notebook or source, the link may predate a redeploy. Ids are deterministic, so the same
        content is still here — reopen it from the list.
      </p>
      <div className="flex gap-2">
        <Link className="btn" href="/notebooks">
          Notebooks
        </Link>
        <Link className="btn-ghost" href="/">
          Dashboard
        </Link>
      </div>
    </div>
  );
}
