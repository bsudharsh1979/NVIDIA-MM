"use client";

import Link from "next/link";
import { useApi } from "@/lib/useApi";
import { EvidenceBadge } from "@/components/EvidenceBadge";
import { ErrorCard, LoadingCard } from "@/components/Status";

export default function TwinsIndex() {
  const { data: rows, error, loading, retry } = useApi<any[]>("/api/twins");
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold">Digital twins</h1>
      <p className="text-sm text-[var(--muted)]">
        Predict before you run. Every outcome is a <EvidenceBadge type="SIMULATED_RESULT" /> — a teaching signal, never a measurement.
      </p>
      {loading && <LoadingCard label="Loading twins" />}
      {error && <ErrorCard error={error} retry={retry} title="Could not load twins" />}
      <div className="grid gap-3 md:grid-cols-2">
        {(rows || []).map((t) => (
          <Link key={t.slug} href={`/twins/${t.slug}`} className="card hover:border-nv-green">
            <h2 className="font-semibold">{t.title}</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">{t.summary}</p>
            {t.suggestions?.length ? (
              <p className="mt-2 text-xs text-nv-green">{t.suggestions.length} suggested scenarios</p>
            ) : null}
          </Link>
        ))}
      </div>
    </div>
  );
}
