"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function ProgressPage() {
  const [data, setData] = useState<any>(null);
  const [integrity, setIntegrity] = useState<any>(null);
  useEffect(() => {
    api("/api/progress").then(setData);
    api("/api/integrity").then(setIntegrity);
  }, []);
  if (!data) return <p>Loading progress…</p>;
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold">Progress & integrity</h1>
      <div className="card text-sm">
        <h2 className="font-semibold">Cost / usage</h2>
        <p className="mt-2">
          {data.usage.calls} calls · {data.usage.input_tokens} in / {data.usage.output_tokens} out · ${data.usage.cost_usd} of ${data.usage.budget_usd}
        </p>
      </div>
      <div className="card">
        <h2 className="font-semibold">Mastery</h2>
        <ul className="mt-2 max-h-96 overflow-auto text-sm">
          {data.mastery.map((m: any) => (
            <li key={m.slug} className="flex justify-between border-b border-[var(--line)] py-1">
              <Link href={`/learn/${m.slug}`}>{m.slug}</Link>
              <span>{Math.round(m.score * 100)}%</span>
            </li>
          ))}
        </ul>
      </div>
      <div className="card text-sm">
        <h2 className="font-semibold">Content integrity dashboard</h2>
        <p className="mt-2">
          {integrity?.questions} questions · {integrity?.spans} source spans
        </p>
        <ul className="mt-2 list-disc pl-5">
          {integrity?.flags?.slice(0, 12).map((f: any, i: number) => (
            <li key={i}>
              {f.kind}: {f.item} — {f.detail}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
