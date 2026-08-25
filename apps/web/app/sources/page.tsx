"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";

export default function SourcesPage() {
  const [arts, setArts] = useState<any[]>([]);
  const [spans, setSpans] = useState<any[] | null>(null);
  const [q, setQ] = useState("late fusion");
  const [hits, setHits] = useState<any[]>([]);
  useEffect(() => {
    api<any[]>("/api/sources").then(setArts);
  }, []);
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold">Sources</h1>
      <form
        className="flex gap-2"
        onSubmit={async (e) => {
          e.preventDefault();
          setHits(await api(`/api/search?q=${encodeURIComponent(q)}`));
        }}
      >
        <input className="flex-1 rounded-lg border border-[var(--line)] bg-transparent px-3 py-2" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search sources" />
        <button className="btn">Hybrid search</button>
      </form>
      {hits.map((h, i) => (
        <article key={i} className="card text-sm">
          <EvidenceBadge type="COURSE_SOURCE" /> <span className="font-mono text-xs">{JSON.stringify(h.locator)}</span>
          <p className="mt-2">{h.text.slice(0, 400)}</p>
        </article>
      ))}
      <div className="grid gap-2 md:grid-cols-2">
        {arts.map((a) => (
          <button key={a.id} className="card text-left" onClick={async () => setSpans(await api(`/api/sources/${a.id}`))}>
            <div className="text-xs uppercase text-nv-green">{a.type}</div>
            <div className="font-semibold">{a.file}</div>
          </button>
        ))}
      </div>
      {spans && (
        <div className="card max-h-[480px] overflow-auto text-sm">
          {spans.map((s) => (
            <p key={s.id} className="border-b border-[var(--line)] py-2">
              <span className="font-mono text-xs">{JSON.stringify(s.locator)}</span> {s.title}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
