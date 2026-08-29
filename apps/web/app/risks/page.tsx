"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Risk = {
  id: string;
  title: string;
  kind: string;
  leading_signal: string;
  spot_it_live: string;
  mitigation: string;
  example: string;
  twin: string;
  scenario: string;
};

export default function RisksPage() {
  const [rows, setRows] = useState<Risk[]>([]);
  useEffect(() => {
    api<Risk[]>("/api/risks").then(setRows);
  }, []);
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold">Risk radar</h1>
      <p className="text-sm text-[var(--muted)]">
        Curated technical, security, and business risks from this multimodal course. Each row deep-links into a twin drill.
      </p>
      <div className="grid gap-3">
        {rows.map((r) => (
          <article key={r.id} className="card space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-lg font-semibold">{r.title}</h2>
              <span className="rounded-full border border-[var(--line)] px-2 py-0.5 text-[10px] uppercase">{r.kind}</span>
            </div>
            <p className="text-sm">
              <strong>Leading signal:</strong> {r.leading_signal}
            </p>
            <p className="text-sm text-[var(--muted)]">
              <strong>Spot it live:</strong> {r.spot_it_live}
            </p>
            <p className="text-sm">
              <strong>Mitigation:</strong> {r.mitigation}
            </p>
            <p className="text-xs text-[var(--muted)]">{r.example}</p>
            <Link className="text-sm text-nv-green" href={`/twins/${r.twin}?scenario=${r.scenario}`}>
              Open {r.twin} drill →
            </Link>
          </article>
        ))}
      </div>
    </div>
  );
}
