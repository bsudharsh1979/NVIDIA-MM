"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";

function PracticeInner() {
  const sp = useSearchParams();
  const concept = sp.get("concept") || "";
  const [items, setItems] = useState<any[]>([]);
  const [idx, setIdx] = useState(0);
  const [choice, setChoice] = useState("");
  const [result, setResult] = useState<any>(null);
  const [hints, setHints] = useState(0);
  const [hintText, setHintText] = useState("");
  useEffect(() => {
    const q = concept ? `/api/questions?concept=${concept}` : "/api/questions";
    api<any[]>(q).then((rows) => {
      setItems(rows);
      setIdx(0);
      setResult(null);
    });
  }, [concept]);
  const q = items[idx];
  async function submit() {
    if (!q) return;
    const r = await api<any>(`/api/questions/${q.id}/attempt`, {
      method: "POST",
      body: JSON.stringify({ response: choice, hints, latency_ms: 800 }),
    });
    setResult(r);
  }
  if (!q) return <p>No questions yet.</p>;
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold">Practice</h1>
      <p className="text-sm text-[var(--muted)]">
        {idx + 1}/{items.length} · {q.bloom} · {q.concept_slug} <EvidenceBadge type="COURSE_SOURCE" />
      </p>
      <div className="card">
        <p className="font-medium">{q.prompt}</p>
        <div className="mt-3 space-y-2">
          {(q.options || []).length > 0 ? (
            q.options.map((o: string) => (
              <label key={o} className="flex gap-2 rounded-lg border border-[var(--line)] p-2 text-sm">
                <input type="radio" name="opt" checked={choice === o} onChange={() => setChoice(o)} />
                {o}
              </label>
            ))
          ) : (
            <textarea className="w-full rounded-lg border border-[var(--line)] bg-transparent p-2" rows={4} value={choice} onChange={(e) => setChoice(e.target.value)} />
          )}
        </div>
        <div className="mt-4 flex gap-2">
          <button className="btn" onClick={submit} disabled={!choice}>
            Submit
          </button>
          <button
            className="btn-ghost"
            onClick={() => {
              setHints((h) => h + 1);
              const loc = q.source || {};
              setHintText(
                hints === 0
                  ? `Hint 1 — inspect ${loc.file || "the notebook"} cell ${loc.cell_index ?? "?"}. Do not skip the distinction this item is probing.`
                  : "Hint 2 — after you submit, a simple correction appears; the full key stays hidden until two hints are used."
              );
            }}
          >
            Hint (don&apos;t reveal yet)
          </button>
        </div>
        {hintText && <p className="mt-3 text-sm text-amber-200">{hintText}</p>}
        {result && (
          <div className="mt-4 space-y-2 text-sm">
            {result.correct ? <p className="text-nv-green">Correct.</p> : <p className="text-amber-300">{result.socratic}</p>}
            {result.why_wrong && (
              <div className="rounded-xl border border-amber-500/30 p-3">
                <h3 className="font-semibold">Why am I wrong?</h3>
                <p className="mt-2">Your answer: {result.why_wrong.your_answer}</p>
                <p>What this suggests you believe: {result.why_wrong.what_this_suggests}</p>
                <p>Missing distinction: {result.why_wrong.missing_distinction}</p>
                <p>
                  Source: {result.why_wrong.source_evidence?.file} cell {result.why_wrong.source_evidence?.cell_index}
                </p>
                <p>Simple correction: {result.why_wrong.simple_correction}</p>
                <p>Try again before the full key is shown (hint twice to reveal).</p>
              </div>
            )}
            {result.explanation && <p className="text-[var(--muted)]">{result.explanation}</p>}
            <button
              className="btn-ghost"
              onClick={() => {
                setIdx((i) => Math.min(items.length - 1, i + 1));
                setChoice("");
                setResult(null);
                setHints(0);
                setHintText("");
              }}
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default function PracticePage() {
  return (
    <Suspense fallback={<p>Loading practice…</p>}>
      <PracticeInner />
    </Suspense>
  );
}
