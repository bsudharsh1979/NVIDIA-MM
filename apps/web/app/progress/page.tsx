"use client";

import Link from "next/link";
import { useApi } from "@/lib/useApi";
import { ErrorCard, LoadingCard } from "@/components/Status";

export default function ProgressPage() {
  const { data, error, loading, retry } = useApi<any>("/api/progress");
  const { data: integrity } = useApi<any>("/api/integrity");
  if (loading) return <LoadingCard label="Loading progress" />;
  if (error) return <ErrorCard error={error} retry={retry} title="Could not load progress" />;
  if (!data) return null;
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
