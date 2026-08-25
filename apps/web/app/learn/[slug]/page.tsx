"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";

export default function LessonPage({ params }: { params: { slug: string } }) {
  const slug = params.slug;
  const [concept, setConcept] = useState<any>(null);
  const [lesson, setLesson] = useState<any>(null);
  const [step, setStep] = useState(0);
  const [depth, setDepth] = useState<"school" | "engineer" | "research">("engineer");
  const [pred, setPred] = useState("");
  const [locked, setLocked] = useState(true);
  useEffect(() => {
    api(`/api/concepts/${slug}`).then(setConcept);
    api(`/api/lessons/${slug}`).then(setLesson).catch(() => {});
  }, [slug]);
  if (!concept) return <p>Loading lesson…</p>;
  const steps = lesson?.steps || [];
  const current = steps[step];
  const body = concept[depth];
  return (
    <div className="space-y-5">
      <p className="text-xs text-nv-green">Active lesson</p>
      <h1 className="text-3xl font-semibold">{concept.name}</h1>
      <div className="flex flex-wrap gap-2">
        {(["school", "engineer", "research"] as const).map((d) => (
          <button key={d} className={`btn-ghost ${depth === d ? "border-nv-green text-nv-green" : ""}`} onClick={() => setDepth(d)}>
            {d} mode
          </button>
        ))}
      </div>
      <div className="card whitespace-pre-wrap text-sm leading-relaxed">{body}</div>
      <p className="text-xs">
        Source{" "}
        <Link className="text-nv-green" href={`/sources?file=${concept.source?.file}`}>
          {concept.source?.file} cell {concept.source?.cell_index}
        </Link>{" "}
        <EvidenceBadge type="COURSE_SOURCE" />
      </p>
      {current && (
        <div className="card">
          <div className="text-xs uppercase tracking-wide text-[var(--muted)]">
            Step {step + 1}/{steps.length} · {current.kind}
          </div>
          <p className="mt-2">{current.text || current.kind}</p>
          {current.kind === "PREDICT" && (
            <textarea className="mt-3 w-full rounded-lg border border-[var(--line)] bg-transparent p-2" rows={3} value={pred} onChange={(e) => setPred(e.target.value)} placeholder="Your prediction before the twin runs…" />
          )}
          {current.kind === "EXPERIMENT" && (
            <div className="mt-3 flex gap-2">
              <Link className="btn" href={`/twins/${concept.twin_id}?prediction=${encodeURIComponent(pred)}`}>
                Open twin (prediction captured)
              </Link>
              <EvidenceBadge type="SIMULATED_RESULT" />
            </div>
          )}
          {current.kind === "PRACTICE" && (
            <Link className="btn mt-3" href={`/practice?concept=${slug}`}>
              Quiz this concept
            </Link>
          )}
          <div className="mt-4 flex justify-between">
            <button className="btn-ghost" disabled={step === 0} onClick={() => setStep((s) => s - 1)}>
              Back
            </button>
            <button className="btn" disabled={current.kind === "PREDICT" && !pred && locked} onClick={() => { setLocked(false); setStep((s) => Math.min(steps.length - 1, s + 1)); }}>
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
