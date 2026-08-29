"use client";

import Link from "next/link";
import { useApi } from "@/lib/useApi";
import { ErrorCard, LoadingCard } from "@/components/Status";

export default function NotebooksPage() {
  const { data: rows, error, loading, retry } = useApi<any[]>("/api/notebooks");
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold">Notebook Studio</h1>
      <p className="text-sm text-[var(--muted)]">
        Every DLI notebook is walkable with per-cell insight tabs and a narrated audio lecture. Code is never auto-executed.
      </p>
      {loading && <LoadingCard label="Loading notebooks" />}
      {error && <ErrorCard error={error} retry={retry} title="Could not load notebooks" />}
      <div className="grid gap-3">
        {(rows || []).map((n) => (
          <Link key={n.slug} href={`/notebooks/${n.slug}`} className="card hover:border-nv-green">
            <div className="flex items-center justify-between">
              <div className="text-xs text-nv-green">Lab {n.order}</div>
              <span className="text-xs text-[var(--muted)]">audio lecture available</span>
            </div>
            <h2 className="text-lg font-semibold">{n.slug}</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">{n.purpose}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
