"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function NotebooksPage() {
  const [rows, setRows] = useState<any[]>([]);
  useEffect(() => {
    api<any[]>("/api/notebooks").then(setRows);
  }, []);
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold">Notebook Studio</h1>
      <p className="text-sm text-[var(--muted)]">Every DLI notebook is walkable. Code is never auto-executed.</p>
      <div className="grid gap-3">
        {rows.map((n) => (
          <Link key={n.slug} href={`/notebooks/${n.slug}`} className="card hover:border-nv-green">
            <div className="text-xs text-nv-green">Lab {n.order}</div>
            <h2 className="text-lg font-semibold">{n.slug}</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">{n.purpose}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
