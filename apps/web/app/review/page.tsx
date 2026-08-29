"use client";

import Link from "next/link";
import { useApi } from "@/lib/useApi";
import { ErrorCard, LoadingCard } from "@/components/Status";

export default function ReviewPage() {
  const { data: items, error, loading, retry } = useApi<any[]>("/api/review");
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold">Reviews due</h1>
      <p className="text-sm text-[var(--muted)]">FSRS-inspired scheduling from misses, weak concepts, and misconceptions.</p>
      {loading && <LoadingCard label="Loading reviews" />}
      {error && <ErrorCard error={error} retry={retry} title="Could not load reviews" />}
      {!loading && !error && (items || []).length === 0 && <p className="card">Nothing due yet. Miss a practice item to schedule a card.</p>}
      <ul className="space-y-2">
        {(items || []).map((i) => (
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
