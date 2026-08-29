"use client";

import { useCallback, useEffect, useState } from "react";
import { api, friendlyError } from "@/lib/api";

/** Load a GET endpoint with loading, friendly error, and retry. */
export function useApi<T = any>(path: string | null) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(Boolean(path));
  const [tick, setTick] = useState(0);

  useEffect(() => {
    if (!path) return;
    let alive = true;
    setLoading(true);
    setError(null);
    api<T>(path)
      .then((d) => {
        if (alive) setData(d);
      })
      .catch((e) => {
        if (alive) setError(friendlyError(e));
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [path, tick]);

  const retry = useCallback(() => setTick((t) => t + 1), []);
  return { data, error, loading, retry };
}
