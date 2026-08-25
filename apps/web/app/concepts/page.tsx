"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";

export default function ConceptsPage() {
  const [graph, setGraph] = useState<{ nodes: any[]; edges: any[] } | null>(null);
  const [sel, setSel] = useState<string | null>(null);
  useEffect(() => {
    api<any>("/api/concepts").then(setGraph);
  }, []);
  const selected = graph?.nodes.find((n) => n.slug === sel);
  const clusters = useMemo(() => Array.from(new Set(graph?.nodes.map((n) => n.cluster) || [])), [graph]);
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold">Concept map</h1>
      <p className="text-sm text-[var(--muted)]">Select a node. Definitions stay source-grounded; twins stay simulations.</p>
      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <div className="card overflow-auto">
          <svg viewBox="0 0 900 640" className="h-[640px] w-full" role="img" aria-label="Concept graph">
            {graph?.edges.map((e, i) => {
              const a = pos(graph.nodes, e.src, clusters);
              const b = pos(graph.nodes, e.dst, clusters);
              if (!a || !b) return null;
              return <line key={i} x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="#1e2a38" strokeWidth="1" />;
            })}
            {graph?.nodes.map((n) => {
              const p = pos(graph.nodes, n.slug, clusters)!;
              return (
                <g key={n.slug} onClick={() => setSel(n.slug)} className="cursor-pointer">
                  <circle cx={p.x} cy={p.y} r={sel === n.slug ? 10 : 6} fill={sel === n.slug ? "#76b900" : "#4b7"} />
                  <text x={p.x + 10} y={p.y + 4} fontSize="10" fill="currentColor">
                    {n.name}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
        <aside className="card text-sm">
          {!selected && <p>Select a concept.</p>}
          {selected && (
            <div className="space-y-2">
              <h2 className="text-lg font-semibold">{selected.name}</h2>
              <EvidenceBadge type="COURSE_SOURCE" />
              <p>{selected.school}</p>
              <p className="text-[var(--muted)]">{selected.engineer}</p>
              <p className="text-xs">{selected.research}</p>
              <p className="text-xs">
                {selected.source?.file} · cell {selected.source?.cell_index}
              </p>
              <div className="flex flex-col gap-2 pt-2">
                <Link className="btn" href={`/learn/${selected.slug}`}>
                  Lesson
                </Link>
                <Link className="btn-ghost" href={`/practice?concept=${selected.slug}`}>
                  Quiz
                </Link>
                {selected.twin_id && (
                  <Link className="btn-ghost" href={`/twins/${selected.twin_id}`}>
                    Digital twin
                  </Link>
                )}
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

function pos(nodes: any[], slug: string, clusters: string[]) {
  const n = nodes.find((x) => x.slug === slug);
  if (!n) return null;
  const ci = Math.max(0, clusters.indexOf(n.cluster));
  const inCluster = nodes.filter((x) => x.cluster === n.cluster);
  const ji = inCluster.findIndex((x) => x.slug === slug);
  const x = 80 + (ci % 4) * 210 + (ji % 3) * 28;
  const y = 60 + Math.floor(ci / 4) * 280 + Math.floor(ji / 3) * 36;
  return { x, y };
}
