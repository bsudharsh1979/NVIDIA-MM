"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Item = { id: string; label: string; ok: boolean; required?: boolean; count?: number };

export default function SetupPage() {
  const [data, setData] = useState<{ items: Item[]; go_live: boolean; note: string; disclaimer: string } | null>(null);
  useEffect(() => {
    api("/api/setup").then(setData);
  }, []);
  if (!data) return <p>Loading go-live checklist…</p>;
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
