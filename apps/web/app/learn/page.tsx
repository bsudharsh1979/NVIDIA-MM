"use client";

import Link from "next/link";
import { useApi } from "@/lib/useApi";
import { EvidenceBadge } from "@/components/EvidenceBadge";
import { ErrorCard, LoadingCard } from "@/components/Status";

export default function LearnIndex() {
  const { data, error, loading, retry } = useApi<{ nodes: { slug: string; name: string; cluster: string }[] }>("/api/concepts");
  const nodes = data?.nodes || [];
  const clusters = Array.from(new Set(nodes.map((n) => n.cluster)));
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-semibold">Learn</h1>
      <p className="text-[var(--muted)]">
        Every major lesson is explain → visualize → predict → experiment → observe → explain back. Answers are not shown first.
      </p>
      <Link className="btn" href="/diagnostic">
        First-run diagnostic
      </Link>
      {loading && <LoadingCard label="Loading concepts" />}
      {error && <ErrorCard error={error} retry={retry} title="Could not load concepts" />}
      {clusters.map((c) => (
        <section key={c} className="card">
          <h2 className="font-semibold capitalize">{c}</h2>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {nodes
              .filter((n) => n.cluster === c)
              .map((n) => (
                <Link key={n.slug} href={`/learn/${n.slug}`} className="rounded-lg border border-[var(--line)] px-3 py-2 text-sm hover:border-nv-green">
                  {n.name}
                </Link>
              ))}
          </div>
        </section>
      ))}
      <EvidenceBadge type="COURSE_SOURCE" />
    </div>
  );
}
