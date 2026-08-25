"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";

export default function LearnIndex() {
  const [nodes, setNodes] = useState<{ slug: string; name: string; cluster: string }[]>([]);
  useEffect(() => {
    api<{ nodes: typeof nodes }>("/api/concepts").then((d) => setNodes(d.nodes));
  }, []);
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
