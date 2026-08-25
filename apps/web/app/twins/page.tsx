"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";

export default function TwinsIndex() {
  const [rows, setRows] = useState<any[]>([]);
  useEffect(() => {
    api<any[]>("/api/twins").then(setRows);
  }, []);
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold">Digital twins</h1>
      <p className="text-sm text-[var(--muted)]">
        Web twins share TwinStateEngine with the Omniverse bridge. Every run is <EvidenceBadge type="SIMULATED_RESULT" />
      </p>
      <div className="grid gap-3 md:grid-cols-2">
        {rows.map((t) => (
          <Link key={t.slug} href={`/twins/${t.slug}`} className="card hover:border-nv-green">
            <h2 className="font-semibold">{t.title}</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">{t.summary}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
