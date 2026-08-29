"use client";

import Link from "next/link";

export default function ErrorPage({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="card max-w-xl space-y-3" role="alert">
      <h1 className="text-xl font-semibold">This page hit an unexpected error</h1>
      <p className="text-sm text-[var(--muted)]">
        Nothing was lost — content ids are deterministic, so your links stay valid. {error?.message ? `Detail: ${error.message}` : ""}
      </p>
      <div className="flex gap-2">
        <button className="btn" type="button" onClick={() => reset()}>
          Try again
        </button>
        <Link className="btn-ghost" href="/">
          Back to dashboard
        </Link>
      </div>
    </div>
  );
}
