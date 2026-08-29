"use client";

import { Suspense, use, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api, friendlyError } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";
import { ErrorCard, LoadingCard } from "@/components/Status";
import { WalkthroughPlayer } from "@/components/WalkthroughPlayer";

const TABS = ["CODE", "PLAIN ENGLISH", "WHY THIS EXISTS", "BUSINESS IMPACT", "WHAT SHOULD HAPPEN", "HOW TO VERIFY", "COMMON FAILURE", "TRY MODIFYING"];

function Detail({ slug }: { slug: string }) {
  const walkthrough = useSearchParams().get("walkthrough") === "1";
  const [nb, setNb] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  const [tab, setTab] = useState("CODE");
  const [open, setOpen] = useState<number | null>(0);
  const [stage, setStage] = useState<{ start: number | null; end: number | null }>({ start: null, end: null });

  useEffect(() => {
    setErr(null);
    api(`/api/notebooks/${slug}`)
      .then(setNb)
      .catch((e) => setErr(friendlyError(e)));
  }, [slug, tick]);

  const onStage = useCallback((start: number | null, end: number | null) => {
    setStage({ start, end });
  }, []);

  if (err) return <ErrorCard error={err} retry={() => setTick((t) => t + 1)} title="Notebook unavailable" />;
  if (!nb) return <LoadingCard label="Loading notebook" />;
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-3xl font-semibold">{nb.filename}</h1>
          <p className="mt-1 text-xs text-[var(--muted)]">{nb.disclaimer}</p>
        </div>
        <WalkthroughPlayer notebookKey={nb.id || slug} onStage={onStage} autoOpen={walkthrough} />
      </div>
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
      {nb.cells.map((c: any) => {
        const narrating = stage.start != null && c.index >= stage.start && c.index <= (stage.end ?? -1);
        return (
          <article key={c.index} className={`card ${narrating ? "cell-narrating" : ""}`}>
            <button className="flex w-full items-center justify-between text-left" onClick={() => setOpen(open === c.index ? null : c.index)}>
              <span className="font-mono text-xs text-[var(--muted)]">
                [{c.index}] {c.type} {c.heading}
                {narrating ? " · narrating this stage" : ""}
              </span>
              {c.dangerous && <span className="text-xs text-amber-300">never_execute — blocked auto-exec</span>}
            </button>
            {open === c.index && (
              <div className="mt-3">
                {c.dangerous && (
                  <div className="mb-2 rounded-lg border border-amber-400/40 bg-amber-400/10 px-3 py-2 text-xs text-amber-100">
                    Shell/cluster command flagged <strong>never_execute</strong>. Shown as DATA only.
                  </div>
                )}
                <div className="mb-2 flex flex-wrap gap-1">
                  {TABS.map((t) => (
                    <button key={t} className={`rounded-full border px-2 py-0.5 text-[10px] ${tab === t ? "border-nv-green text-nv-green" : "border-[var(--line)]"}`} onClick={() => setTab(t)}>
                      {t}
                    </button>
                  ))}
                </div>
                {tab === "CODE" && <pre className="overflow-auto rounded-lg bg-black/40 p-3 text-xs">{c.code || c.markdown}</pre>}
                {tab === "PLAIN ENGLISH" && <p className="text-sm">{c.tabs.plain || c.tabs.plain_english}</p>}
                {tab === "WHY THIS EXISTS" && <p className="text-sm">{c.tabs.why}</p>}
                {tab === "BUSINESS IMPACT" && <p className="text-sm">{c.tabs.business}</p>}
                {tab === "WHAT SHOULD HAPPEN" && <p className="text-sm">{c.tabs.should || c.tabs.what_should_happen}</p>}
                {tab === "HOW TO VERIFY" && <p className="text-sm">{c.tabs.verify || c.tabs.how_to_verify}</p>}
                {tab === "COMMON FAILURE" && <p className="text-sm">{c.tabs.failure || c.tabs.common_failure}</p>}
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
        );
      })}
    </div>
  );
}

export default function NotebookDetail({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  return (
    <Suspense fallback={<p>Loading notebook…</p>}>
      <Detail slug={slug} />
    </Suspense>
  );
}
