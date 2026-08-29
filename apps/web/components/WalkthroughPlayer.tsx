"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "@/lib/api";

type Step = {
  kind: string;
  title: string;
  text: string;
  start?: number;
  end?: number;
  crux?: string;
  cells?: number[];
  concept_slug?: string;
};

type Walkthrough = {
  filename: string;
  depth: string;
  title: string;
  steps: Step[];
  stages: { title: string; start: number; end: number; crux?: string }[];
  n_cells: number;
  disclaimer?: string;
};

const DEPTH_KEY = "mta-walkthrough-depth";

function estimateSeconds(text: string, speed: number) {
  const words = Math.max(1, (text || "").split(/\s+/).length);
  return Math.max(4, Math.round(words / (2.4 * speed)));
}

export function WalkthroughPlayer({
  notebookKey,
  onStage,
  autoOpen = false,
}: {
  notebookKey: string;
  onStage?: (start: number | null, end: number | null) => void;
  autoOpen?: boolean;
}) {
  const [open, setOpen] = useState(autoOpen);
  const [depth, setDepth] = useState<"simple" | "expert">("simple");
  const [data, setData] = useState<Walkthrough | null>(null);
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [err, setErr] = useState<string | null>(null);
  const [unavailable, setUnavailable] = useState(false);
  const [loading, setLoading] = useState(false);
  const cache = useRef<Map<string, Walkthrough>>(new Map());
  const instant = useRef<number[]>([]);
  const playGen = useRef(0);

  useEffect(() => {
    const stored = window.localStorage.getItem(DEPTH_KEY);
    if (stored === "expert" || stored === "simple") setDepth(stored);
  }, []);

  const load = useCallback(
    async (nextDepth: "simple" | "expert") => {
      const hit = cache.current.get(nextDepth);
      if (hit) {
        setData(hit);
        return hit;
      }
      setLoading(true);
      setErr(null);
      try {
        const wt = await api<Walkthrough>(`/api/notebooks/${encodeURIComponent(notebookKey)}/walkthrough?depth=${nextDepth}`);
        cache.current.set(nextDepth, wt);
        setData(wt);
        return wt;
      } catch (e) {
        setErr(String(e));
        return null;
      } finally {
        setLoading(false);
      }
    },
    [notebookKey]
  );

  useEffect(() => {
    if (open) load(depth);
  }, [open, depth, load]);

  useEffect(() => {
    if (autoOpen) setOpen(true);
  }, [autoOpen]);

  const step = data?.steps[index];
  useEffect(() => {
    if (step && step.kind === "stage") onStage?.(step.start ?? null, step.end ?? null);
    else onStage?.(null, null);
  }, [step, onStage]);

  const stopSpeech = () => {
    if (typeof window !== "undefined" && window.speechSynthesis) window.speechSynthesis.cancel();
  };

  const speak = async (text: string) => {
    const t0 = performance.now();
    try {
      await api("/api/voice/tts", {
        method: "POST",
        body: JSON.stringify({ text, provider: "auto", clip: false }),
      });
    } catch {
      /* browser fallback below */
    }
    if (!window.speechSynthesis) {
      return performance.now() - t0;
    }
    return new Promise<number>((resolve) => {
      const u = new SpeechSynthesisUtterance(text);
      u.rate = Math.min(2, Math.max(0.7, speed * 0.93));
      u.onend = () => resolve(performance.now() - t0);
      u.onerror = () => resolve(performance.now() - t0);
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(u);
    });
  };

  const go = useCallback(
    (next: number) => {
      if (!data) return;
      setIndex(Math.max(0, Math.min(data.steps.length - 1, next)));
    },
    [data]
  );

  useEffect(() => {
    if (!playing || !data || unavailable) return;
    const gen = ++playGen.current;
    let cancelled = false;
    (async () => {
      for (let i = index; i < data.steps.length; i++) {
        if (cancelled || playGen.current !== gen) return;
        setIndex(i);
        const elapsed = await speak(data.steps[i].text);
        if (cancelled || playGen.current !== gen) return;
        if (elapsed < 400) {
          instant.current = [...instant.current.slice(-1), elapsed];
          if (instant.current.length >= 2) {
            setUnavailable(true);
            setPlaying(false);
            stopSpeech();
            return;
          }
        } else {
          instant.current = [];
        }
      }
      setPlaying(false);
    })();
    return () => {
      cancelled = true;
      stopSpeech();
    };
    // speak closes over speed; restart when speed or index-driven play changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playing, data, unavailable, speed]);

  async function toggleDepth() {
    const next = depth === "simple" ? "expert" : "simple";
    cache.current.delete(next);
    window.localStorage.setItem(DEPTH_KEY, next);
    setDepth(next);
    setPlaying(false);
    stopSpeech();
    instant.current = [];
    setUnavailable(false);
    const wt = await load(next);
    if (wt) setIndex((i) => Math.min(i, wt.steps.length - 1));
  }

  const durations = useMemo(() => (data ? data.steps.map((s) => estimateSeconds(s.text, speed)) : []), [data, speed]);

  if (!open) {
    return (
      <button className="btn" onClick={() => setOpen(true)} type="button">
        Play audio lecture
      </button>
    );
  }

  return (
    <div className="sticky bottom-3 z-40 rounded-2xl border border-nv-green/40 bg-[var(--panel)]/95 p-4 shadow-2xl backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="text-[10px] uppercase tracking-[0.2em] text-nv-green">Audio lecture</div>
          <h2 className="text-lg font-semibold">{data?.title || "Walkthrough"}</h2>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            className={`rounded-full border px-3 py-1 text-xs ${depth === "simple" ? "border-nv-green text-nv-green" : "border-[var(--line)]"}`}
            onClick={() => depth !== "simple" && toggleDepth()}
          >
            SIMPLE
          </button>
          <button
            type="button"
            className={`rounded-full border px-3 py-1 text-xs ${depth === "expert" ? "border-nv-green text-nv-green" : "border-[var(--line)]"}`}
            onClick={() => depth !== "expert" && toggleDepth()}
          >
            EXPERT
          </button>
          <button type="button" className="btn-ghost text-xs" onClick={() => { setOpen(false); setPlaying(false); stopSpeech(); onStage?.(null, null); }}>
            Close
          </button>
        </div>
      </div>
      {loading && <p className="mt-2 text-sm text-[var(--muted)]">Loading lecture…</p>}
      {err && <p className="mt-2 text-sm text-amber-300">{err}</p>}
      {unavailable && <p className="mt-2 text-sm text-amber-200">audio unavailable — step through manually</p>}
      {step && (
        <div className="mt-3 space-y-2">
          <div className="text-xs uppercase text-[var(--muted)]">
            {step.kind.replace("_", " ")} · {index + 1}/{data?.steps.length}
            {step.kind === "stage" && typeof step.start === "number" ? ` · cells ${step.start}–${step.end} (narrating this stage)` : ""}
          </div>
          <h3 className="font-semibold">{step.title}</h3>
          <p className="text-sm leading-relaxed">{step.text}</p>
        </div>
      )}
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <button type="button" className="btn-ghost text-xs" onClick={() => { setPlaying(false); stopSpeech(); go(index - 1); }}>
          Prev
        </button>
        <button
          type="button"
          className="btn text-xs"
          onClick={() => {
            if (unavailable) return;
            setPlaying((p) => !p);
            if (playing) stopSpeech();
          }}
        >
          {playing ? "Pause" : "Play"}
        </button>
        <button type="button" className="btn-ghost text-xs" onClick={() => { setPlaying(false); stopSpeech(); go(index + 1); }}>
          Next
        </button>
        <label className="ml-2 text-xs text-[var(--muted)]">
          Speed
          <select
            className="ml-1 rounded border border-[var(--line)] bg-transparent px-1"
            value={speed}
            onChange={(e) => setSpeed(Number(e.target.value))}
          >
            {[0.75, 1, 1.25, 1.5].map((s) => (
              <option key={s} value={s}>
                {s}×
              </option>
            ))}
          </select>
        </label>
      </div>
      {data && (
        <ol className="mt-3 max-h-40 overflow-auto text-xs">
          {data.steps.map((s, i) => (
            <li key={`${s.kind}-${i}`}>
              <button
                type="button"
                className={`w-full rounded px-2 py-1 text-left ${i === index ? "bg-nv-green/15 text-nv-green" : "text-[var(--muted)]"}`}
                onClick={() => {
                  setPlaying(false);
                  stopSpeech();
                  setIndex(i);
                }}
              >
                {s.title}
                <span className="ml-2 opacity-70">{durations[i]}s</span>
              </button>
            </li>
          ))}
        </ol>
      )}
      <p className="mt-2 text-[10px] text-[var(--muted)]">{data?.disclaimer}</p>
    </div>
  );
}
