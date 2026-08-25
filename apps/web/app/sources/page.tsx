"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";

function SourcesInner() {
  const file = useSearchParams().get("file") || "";
  const [arts, setArts] = useState<any[]>([]);
  const [spans, setSpans] = useState<any[] | null>(null);
  const [active, setActive] = useState<string>("");
  const [q, setQ] = useState(file ? file.replace(/\.ipynb$/, "") : "late fusion");
  const [hits, setHits] = useState<any[]>([]);
  useEffect(() => {
    api<any[]>("/api/sources").then(async (rows) => {
      setArts(rows);
      const match = rows.find((a) => !file || a.file === file || String(a.file).includes(file));
      if (match) {
        setActive(match.file);
        setSpans(await api(`/api/sources/${match.id}`));
      }
    });
  }, [file]);
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold">Sources</h1>
      <p className="text-sm text-[var(--muted)]">
        Jump to a notebook cell. Nothing here is executed. {file && <span>Opened from citation: {file}</span>}
      </p>
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
          <button
            key={a.id}
            className={`card text-left ${active === a.file ? "border-nv-green" : ""}`}
            onClick={async () => {
              setActive(a.file);
              setSpans(await api(`/api/sources/${a.id}`));
            }}
          >
            <div className="text-xs uppercase text-nv-green">{a.type}</div>
            <div className="font-semibold">{a.file}</div>
          </button>
        ))}
      </div>
      {spans && (
        <div className="card max-h-[480px] overflow-auto text-sm">
          {spans.map((s) => (
            <p key={s.id} className="border-b border-[var(--line)] py-2">
              <span className="font-mono text-xs">{JSON.stringify(s.locator)}</span> {s.title || s.heading}
              {s.text && <span className="mt-1 block text-[var(--muted)]">{String(s.text).slice(0, 280)}</span>}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}

export default function SourcesPage() {
  return (
    <Suspense fallback={<p>Loading sources…</p>}>
      <SourcesInner />
    </Suspense>
  );
}
