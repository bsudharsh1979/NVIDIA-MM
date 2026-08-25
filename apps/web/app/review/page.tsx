"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function ReviewPage() {
  const [items, setItems] = useState<any[]>([]);
  useEffect(() => {
    api<any[]>("/api/review").then(setItems);
  }, []);
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold">Reviews due</h1>
      <p className="text-sm text-[var(--muted)]">FSRS-inspired scheduling from misses, weak concepts, and misconceptions.</p>
      {items.length === 0 && <p className="card">Nothing due yet. Miss a practice item to schedule a card.</p>}
      <ul className="space-y-2">
        {items.map((i) => (
          <li key={i.id} className="card flex items-center justify-between text-sm">
            <span>
              {i.concept} · {i.reason} · due {i.due}
            </span>
            <Link className="btn" href={`/practice?concept=${i.concept}`}>
              Review
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
