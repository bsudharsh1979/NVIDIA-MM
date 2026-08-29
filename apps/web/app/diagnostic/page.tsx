"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, friendlyError } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { EvidenceBadge } from "@/components/EvidenceBadge";
import { ErrorCard, LoadingCard } from "@/components/Status";

export default function DiagnosticPage() {
  const { data, error, loading, retry } = useApi<{ items: any[] }>("/api/diagnostic");
  const items = data?.items || [];
  const [i, setI] = useState(0);
  const [choice, setChoice] = useState("");
  const [done, setDone] = useState(false);
  const [submitErr, setSubmitErr] = useState<string | null>(null);
  const router = useRouter();
  const q = items[i];
  if (loading) return <LoadingCard label="Loading diagnostic" />;
  if (error) return <ErrorCard error={error} retry={retry} title="Could not load the diagnostic" />;
  if (done) {
    return (
      <div className="card space-y-3">
        <h1 className="text-2xl font-semibold">Diagnostic complete</h1>
        <p>Open Home for the mastery heatmap and a 30-minute plan. Nothing here is an ACTUAL_RUN.</p>
        <button className="btn" onClick={() => router.push("/")}>
          Go to dashboard
        </button>
      </div>
    );
  }
  if (!q) return <p className="card">No diagnostic items available yet.</p>;
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold">Adaptive diagnostic</h1>
      <p className="text-sm text-[var(--muted)]">
        {i + 1}/{items.length} · {q.concept_slug} <EvidenceBadge type="COURSE_SOURCE" />
      </p>
      <div className="card">
        <p>{q.prompt}</p>
        <div className="mt-3 space-y-2">
          {(q.options || []).map((o: string) => (
            <label key={o} className="flex gap-2 text-sm">
              <input type="radio" name="d" checked={choice === o} onChange={() => setChoice(o)} />
              {o}
            </label>
          ))}
        </div>
        {submitErr && <p className="mt-3 text-sm text-amber-300">{submitErr}</p>}
        <button
          className="btn mt-4"
          disabled={!choice}
          onClick={async () => {
            try {
              setSubmitErr(null);
              await api(`/api/questions/${q.id}/attempt`, { method: "POST", body: JSON.stringify({ response: choice }) });
              setChoice("");
              if (i + 1 >= items.length) setDone(true);
              else setI(i + 1);
            } catch (e) {
              setSubmitErr(friendlyError(e));
            }
          }}
        >
          Continue
        </button>
      </div>
    </div>
  );
}
