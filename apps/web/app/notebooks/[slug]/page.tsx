"use client";

import { use, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";

const TABS = ["CODE", "PLAIN ENGLISH", "LINE BY LINE", "WHY THIS EXISTS", "WHAT SHOULD HAPPEN", "HOW TO VERIFY", "COMMON FAILURE", "TRY MODIFYING"];

export default function NotebookDetail({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const [nb, setNb] = useState<any>(null);
  const [tab, setTab] = useState("CODE");
  const [open, setOpen] = useState<number | null>(0);
  useEffect(() => {
    api(`/api/notebooks/${slug}`).then(setNb);
  }, [slug]);
  if (!nb) return <p>Loading notebook…</p>;
  return (
    <div className="space-y-5">
      <h1 className="text-3xl font-semibold">{nb.filename}</h1>
      <div className="grid gap-3 md:grid-cols-3">
        <div className="card text-sm">
          <h2 className="font-semibold">Purpose</h2>
          <p className="mt-1 text-[var(--muted)]">{nb.purpose}</p>
        </div>
        <div className="card text-sm">
          <h2 className="font-semibold">Why it matters</h2>
          <p className="mt-1 text-[var(--muted)]">{nb.why_it_matters}</p>
        </div>
        <div className="card text-sm">
          <h2 className="font-semibold">Expected outcome</h2>
          <p className="mt-1 text-[var(--muted)]">{nb.expected_outcome}</p>
        </div>
      </div>
      <div className="card">
        <h2 className="font-semibold">Flow</h2>
        <ol className="mt-2 list-decimal pl-5 text-sm">
          {nb.flow.map((h: string) => (
            <li key={h}>{h}</li>
          ))}
        </ol>
        <p className="mt-3 text-xs text-amber-200">{nb.execution_policy}</p>
      </div>
      {nb.cells.map((c: any) => (
        <article key={c.index} className="card">
          <button className="flex w-full items-center justify-between text-left" onClick={() => setOpen(open === c.index ? null : c.index)}>
            <span className="font-mono text-xs text-[var(--muted)]">
              [{c.index}] {c.type} {c.heading}
            </span>
            {c.dangerous && <span className="text-xs text-amber-300">blocked auto-exec</span>}
          </button>
          {open === c.index && (
            <div className="mt-3">
              <div className="mb-2 flex flex-wrap gap-1">
                {TABS.map((t) => (
                  <button key={t} className={`rounded-full border px-2 py-0.5 text-[10px] ${tab === t ? "border-nv-green text-nv-green" : "border-[var(--line)]"}`} onClick={() => setTab(t)}>
                    {t}
                  </button>
                ))}
              </div>
              {tab === "CODE" && <pre className="overflow-auto rounded-lg bg-black/40 p-3 text-xs">{c.code || c.markdown}</pre>}
              {tab === "PLAIN ENGLISH" && <p className="text-sm">{c.tabs.plain_english}</p>}
              {tab === "LINE BY LINE" && (
                <ol className="list-decimal pl-5 text-xs">
                  {c.tabs.line_by_line.map((l: string, i: number) => (
                    <li key={i}>{l}</li>
                  ))}
                </ol>
              )}
              {tab === "WHY THIS EXISTS" && <p className="text-sm">{c.tabs.why}</p>}
              {tab === "WHAT SHOULD HAPPEN" && <p className="text-sm">{c.tabs.what_should_happen}</p>}
              {tab === "HOW TO VERIFY" && <p className="text-sm">{c.tabs.how_to_verify}</p>}
              {tab === "COMMON FAILURE" && <p className="text-sm">{c.tabs.common_failure}</p>}
              {tab === "TRY MODIFYING" && <p className="text-sm">{c.tabs.try_modifying}</p>}
              <div className="mt-3 flex items-center gap-2 text-xs">
                <EvidenceBadge type={c.stored_output ? "COURSE_SOURCE" : "EXPECTED_RESULT"} />
                source index {c.locator.file}:{c.locator.cell_index}
              </div>
              {c.stored_output ? (
                <pre className="mt-2 overflow-auto text-xs text-emerald-200">{c.stored_output}</pre>
              ) : (
                <p className="mt-2 text-xs text-[var(--muted)]">No stored cell output in this clone — not an ACTUAL_RUN.</p>
              )}
            </div>
          )}
        </article>
      ))}
    </div>
  );
}
