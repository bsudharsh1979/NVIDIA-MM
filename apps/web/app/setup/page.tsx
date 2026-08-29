"use client";

import { useApi } from "@/lib/useApi";
import { ErrorCard, LoadingCard } from "@/components/Status";

type Item = { id: string; label: string; ok: boolean; required?: boolean; count?: number };

export default function SetupPage() {
  const { data, error, loading, retry } = useApi<{ items: Item[]; go_live: boolean; note: string; disclaimer: string }>("/api/setup");
  if (loading) return <LoadingCard label="Loading go-live checklist" />;
  if (error) return <ErrorCard error={error} retry={retry} title="Could not load the checklist" />;
  if (!data) return null;
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold">Go-live checklist</h1>
      <p className="text-sm text-[var(--muted)]">{data.note}</p>
      <p className="text-xs text-amber-200">{data.disclaimer}</p>
      <p className="text-sm">
        Core path: <strong>{data.go_live ? "ready without keys" : "blocked"}</strong>
      </p>
      <ul className="space-y-2">
        {data.items.map((item) => (
          <li key={item.id} className="card flex items-center justify-between text-sm">
            <span>
              {item.label}
              {typeof item.count === "number" ? ` (${item.count})` : ""}
              {item.required ? <span className="ml-2 text-[10px] uppercase text-[var(--muted)]">required</span> : null}
            </span>
            <span className={item.ok ? "text-nv-green" : "text-amber-300"}>{item.ok ? "configured" : "not configured"}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
