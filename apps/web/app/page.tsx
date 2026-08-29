"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, friendlyError } from "@/lib/api";
import { ApiPicker } from "@/components/ApiPicker";
import { ErrorCard, LoadingCard } from "@/components/Status";

type Dash = {
  overall_mastery: number;
  heatmap: { slug: string; score: number; tags: string[] }[];
  reviews_due: number;
  weakest: { slug: string; score: number }[];
  strongest: { slug: string; score: number }[];
  misconception_count: number;
  assessment_readiness: number;
  resume: { text: string; href?: string };
  plan: { minutes: number; action: string; href: string }[];
  what_i_know: { slug: string }[];
  what_i_forget: { slug: string }[];
  blocking_misconception: string | null;
  notebook_revisit: string;
  twin_run: string;
  diagnostic_complete?: boolean;
  tutor_provider?: string;
  ask_api?: string;
};

export default function HomePage() {
  const [data, setData] = useState<Dash | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  useEffect(() => {
    setErr(null);
    api<Dash>("/api/dashboard")
      .then(setData)
      .catch((e) => setErr(friendlyError(e)));
  }, [tick]);
  if (err) return <ErrorCard error={err} retry={() => setTick((t) => t + 1)} title="The learning API is unreachable" />;
  if (!data) return <LoadingCard label="Loading your dashboard" />;
  return (
    <div className="space-y-6">
      <header>
        <p className="text-xs uppercase tracking-[0.2em] text-nv-green">Learner dashboard</p>
        <h1 className="mt-1 text-3xl font-semibold">What should I learn next?</h1>
        <p className="mt-2 max-w-3xl text-[var(--muted)]">
          Source-grounded academy for <strong>NVIDIA — Building Multimodal AI Applications</strong>. Digital twins are labeled
          simulations. Demo mode needs no API key.
        </p>
      </header>
      <section className="grid gap-4 lg:grid-cols-2">
        <ApiPicker />
        <div className="card space-y-3">
          <h2 className="font-semibold">{data.diagnostic_complete ? "Diagnostic on file" : "First-run diagnostic"}</h2>
          <p className="text-sm text-[var(--muted)]">
            {data.diagnostic_complete
              ? "Heatmap below already includes your attempts. Re-run if you want a fresh snapshot."
              : "Before lessons, probe fusion, KV-analog (CILP), VSS, and Graph-RAG so the 30-minute plan is honest."}
          </p>
          <Link className="btn" href="/diagnostic">
            {data.diagnostic_complete ? "Retake diagnostic" : "Start diagnostic"}
          </Link>
        </div>
      </section>
      <section className="grid gap-4 md:grid-cols-4">
        <Stat label="Overall mastery" value={`${Math.round(data.overall_mastery * 100)}%`} />
        <Stat label="Reviews due" value={String(data.reviews_due)} href="/review" />
        <Stat label="Misconceptions" value={String(data.misconception_count)} />
        <Stat label="Assessment readiness" value={`${Math.round(data.assessment_readiness * 100)}%`} href="/assessment" />
      </section>
      <section className="card">
        <h2 className="font-semibold">Session resume</h2>
        <p className="mt-2 text-sm text-[var(--muted)]">{data.resume?.text}</p>
        <Link className="btn mt-4" href={data.resume?.href || "/learn"}>
          Continue
        </Link>
      </section>
      <section className="grid gap-4 md:grid-cols-2">
        <div className="card">
          <h2 className="font-semibold">What I know</h2>
          <ul className="mt-3 space-y-1 text-sm">
            {data.strongest.map((s) => (
              <li key={s.slug}>
                <Link className="text-nv-green" href={`/learn/${s.slug}`}>
                  {s.slug}
                </Link>{" "}
                <span className="text-[var(--muted)]">{Math.round(s.score * 100)}%</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="card">
          <h2 className="font-semibold">What I am forgetting</h2>
          <ul className="mt-3 space-y-1 text-sm">
            {data.weakest.map((s) => (
              <li key={s.slug}>
                <Link className="text-nv-green" href={`/learn/${s.slug}`}>
                  {s.slug}
                </Link>{" "}
                <span className="text-[var(--muted)]">{Math.round(s.score * 100)}%</span>
              </li>
            ))}
          </ul>
        </div>
      </section>
      <section className="card">
        <h2 className="font-semibold">Today&apos;s 30-minute plan</h2>
        <ol className="mt-3 space-y-2">
          {data.plan.map((p) => (
            <li key={p.action} className="flex items-center justify-between gap-3 text-sm">
              <span>
                <span className="text-nv-green">{p.minutes}m</span> {p.action}
              </span>
              <Link className="btn-ghost" href={p.href}>
                Go
              </Link>
            </li>
          ))}
        </ol>
      </section>
      <section className="card">
        <h2 className="font-semibold">Concept heatmap</h2>
        <div className="mt-4 flex flex-wrap gap-1">
          {data.heatmap.map((h) => (
            <Link
              key={h.slug}
              href={`/learn/${h.slug}`}
              title={`${h.slug} ${Math.round(h.score * 100)}%`}
              className="h-7 w-7 rounded-sm"
              style={{ background: `rgba(118,185,0,${0.15 + h.score * 0.85})` }}
            />
          ))}
        </div>
        <p className="mt-3 text-sm text-[var(--muted)]">
          Blocking misconception: {data.blocking_misconception || "none detected"}. Revisit {data.notebook_revisit}. Run twin{" "}
          <Link className="text-nv-green" href={`/twins/${data.twin_run}`}>
            {data.twin_run}
          </Link>
          .
        </p>
      </section>
    </div>
  );
}

function Stat({ label, value, href }: { label: string; value: string; href?: string }) {
  const inner = (
    <div className="card">
      <div className="text-xs uppercase tracking-wide text-[var(--muted)]">{label}</div>
      <div className="mt-1 text-2xl font-semibold">{value}</div>
    </div>
  );
  return href ? <Link href={href}>{inner}</Link> : inner;
}
