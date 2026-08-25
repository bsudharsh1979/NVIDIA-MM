"use client";

import { useEffect, useState } from "react";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";

export function TwinStudio({ slug, initialPrediction = "" }: { slug: string; initialPrediction?: string }) {
  const [meta, setMeta] = useState<any>(null);
  const [controls, setControls] = useState<Record<string, any>>({});
  const [prediction, setPrediction] = useState(initialPrediction);
  const [revealed, setRevealed] = useState(false);
  const [state, setState] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api<any[]>("/api/twins").then((rows) => {
      const t = rows.find((r) => r.slug === slug);
      setMeta(t);
      const next: Record<string, any> = {};
      for (const c of t?.controls || []) next[c.key] = c.default;
      setControls(next);
    });
  }, [slug]);

  async function run() {
    setErr(null);
    if (!prediction.trim()) {
      setErr("Predict first — the twin will not reveal metrics until you write a hypothesis.");
      return;
    }
    const r = await api<any>(`/api/twins/${slug}/run`, {
      method: "POST",
      body: JSON.stringify({ controls, prediction }),
    });
    setState(r.state);
    setRevealed(true);
  }

  if (!meta) return <p>Loading twin…</p>;
  const series = state?.series?.train_error?.map((v: number, i: number) => ({
    epoch: i + 1,
    train: v,
    valid: state.series.valid_error?.[i],
  }));

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-3xl font-semibold">{meta.title}</h1>
        <EvidenceBadge type="SIMULATED_RESULT" />
      </div>
      <p className="text-sm text-[var(--muted)]">{meta.summary} Never shown as an actual measurement.</p>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card space-y-3">
          <h2 className="font-semibold">Controls</h2>
          {meta.controls.map((c: any) => (
            <label key={c.key} className="block text-sm">
              <span className="text-[var(--muted)]">{c.label}</span>
              {c.type === "bool" ? (
                <input className="ml-2" type="checkbox" checked={!!controls[c.key]} onChange={(e) => setControls({ ...controls, [c.key]: e.target.checked })} />
              ) : c.type === "enum" ? (
                <select className="mt-1 w-full rounded-lg border border-[var(--line)] bg-transparent px-2 py-1" value={controls[c.key]} onChange={(e) => setControls({ ...controls, [c.key]: e.target.value })}>
                  {c.options.map((o: string) => (
                    <option key={o} value={o}>
                      {o}
                    </option>
                  ))}
                </select>
              ) : c.type === "text" ? (
                <input className="mt-1 w-full rounded-lg border border-[var(--line)] bg-transparent px-2 py-1" value={controls[c.key] || ""} onChange={(e) => setControls({ ...controls, [c.key]: e.target.value })} />
              ) : (
                <input
                  className="mt-1 w-full"
                  type="range"
                  min={c.min}
                  max={c.max}
                  step={c.step}
                  value={controls[c.key] ?? c.default}
                  onChange={(e) => setControls({ ...controls, [c.key]: Number(e.target.value) })}
                />
              )}
              {c.type !== "bool" && c.type !== "enum" && c.type !== "text" && <span className="ml-2 text-xs">{controls[c.key]}</span>}
            </label>
          ))}
          <label className="block text-sm">
            <span className="text-[var(--muted)]">Your prediction (required)</span>
            <textarea className="mt-1 w-full rounded-lg border border-[var(--line)] bg-transparent p-2" rows={3} value={prediction} onChange={(e) => setPrediction(e.target.value)} />
          </label>
          {err && <p className="text-sm text-amber-300">{err}</p>}
          <button className="btn" onClick={run}>
            Run simulation
          </button>
        </div>
        <div className="card">
          <TwinVisual slug={slug} controls={controls} state={revealed ? state : null} />
        </div>
      </div>
      {revealed && state && (
        <div className="card">
          <h2 className="font-semibold">Observe</h2>
          <p className="text-xs text-[var(--muted)]">Prediction: {prediction}</p>
          <dl className="mt-3 grid grid-cols-2 gap-2 text-sm md:grid-cols-4">
            {Object.entries(state.metrics).map(([k, v]) => (
              <div key={k}>
                <dt className="text-[var(--muted)]">{k}</dt>
                <dd className="font-mono">{typeof v === "number" ? v.toFixed(3) : String(v)}</dd>
              </div>
            ))}
          </dl>
          {series && (
            <div className="mt-4 h-56">
              <ResponsiveContainer>
                <LineChart data={series}>
                  <XAxis dataKey="epoch" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="train" stroke="#76b900" dot={false} />
                  <Line type="monotone" dataKey="valid" stroke="#c084fc" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
          <ul className="mt-3 list-disc pl-5 text-sm">
            {state.notes?.map((n: string) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function TwinVisual({ slug, controls, state }: { slug: string; controls: any; state: any }) {
  if (slug === "lidar-geometry") {
    const x = state?.metrics?.x ?? 0;
    const y = state?.metrics?.y ?? 25;
    const z = state?.metrics?.z ?? 0;
    return (
      <svg viewBox="0 0 400 260" className="h-64 w-full" role="img" aria-label="LiDAR beam">
        <rect width="400" height="260" fill="#0b0f14" />
        <text x="12" y="20" fill="#76b900" fontSize="11">
          Sensor (0,25,0)
        </text>
        <circle cx="200" cy="40" r="6" fill="#76b900" />
        <line x1="200" y1="40" x2={200 + x * 6} y2={40 + (25 - Math.min(y, 40)) * 4} stroke="#7dd3fc" strokeWidth="2" />
        <circle cx={200 + x * 6} cy={40 + (25 - Math.min(y, 40)) * 4} r="5" fill={state?.metrics?.valid_return ? "#76b900" : "#f87171"} />
        <text x="12" y="240" fill="#9bb0c5" fontSize="11">
          az {controls.azimuth_deg}° ze {controls.zenith_deg}° d {controls.depth} {state ? "" : "(predict before run)"}
        </text>
      </svg>
    );
  }
  if (slug === "fusion-lab") {
    return (
      <svg viewBox="0 0 420 260" className="h-64 w-full" aria-label="Fusion architecture">
        <rect width="420" height="260" fill="#0b0f14" />
        <rect x="20" y="40" width="80" height="40" rx="6" fill="#1e3a2f" stroke="#76b900" />
        <text x="36" y="64" fill="#e8eef5" fontSize="11">
          RGB
        </text>
        <rect x="20" y="140" width="80" height="40" rx="6" fill="#1e2a3a" stroke="#7dd3fc" />
        <text x="32" y="164" fill="#e8eef5" fontSize="11">
          XYZA
        </text>
        <rect x="160" y="90" width="100" height="50" rx="6" fill="#241e38" stroke="#c084fc" />
        <text x="178" y="120" fill="#e8eef5" fontSize="11">
          {controls.architecture}
        </text>
        <rect x="310" y="90" width="90" height="50" rx="6" fill="#2a2410" stroke="#fbbf24" />
        <text x="328" y="120" fill="#e8eef5" fontSize="11">
          xyz×3
        </text>
        <line x1="100" y1="60" x2="160" y2="105" stroke="#76b900" />
        <line x1="100" y1="160" x2="160" y2="125" stroke="#7dd3fc" />
        <line x1="260" y1="115" x2="310" y2="115" stroke="#fbbf24" />
      </svg>
    );
  }
  if (slug === "vss-pipeline") {
    const chunks = state?.metrics?.chunks ?? Math.ceil((controls.video_length_s || 120) / (controls.chunk_duration_s || 20));
    return (
      <svg viewBox="0 0 420 120" className="h-40 w-full" aria-label="VSS chunks">
        <rect width="420" height="120" fill="#0b0f14" />
        {Array.from({ length: Math.min(24, Math.max(1, Number(chunks) || 1)) }).map((_, i) => (
          <rect key={i} x={10 + i * 16} y="40" width="12" height="40" fill="#76b900" opacity={0.4 + (i % 3) * 0.2} />
        ))}
        <text x="12" y="20" fill="#9bb0c5" fontSize="11">
          chunks {revealedText(state, chunks)} · frames {state?.metrics?.processed_frames ?? "?"}
        </text>
      </svg>
    );
  }
  if (slug === "graph-rag") {
    return (
      <svg viewBox="0 0 420 220" className="h-56 w-full" aria-label="Warehouse graph">
        <rect width="420" height="220" fill="#0b0f14" />
        <circle cx="80" cy="80" r="22" fill="#1e3a2f" stroke="#76b900" />
        <text x="58" y="84" fill="#e8eef5" fontSize="10">
          worker
        </text>
        <circle cx="220" cy="80" r="22" fill="#1e2a3a" stroke="#7dd3fc" />
        <text x="208" y="84" fill="#e8eef5" fontSize="10">
          box
        </text>
        <circle cx="220" cy="170" r="22" fill="#2a2410" stroke="#fbbf24" />
        <text x="206" y="174" fill="#e8eef5" fontSize="10">
          PPE
        </text>
        <line x1="102" y1="80" x2="198" y2="80" stroke="#c084fc" />
        <line x1="80" y1="102" x2="200" y2="160" stroke="#76b900" />
        <text x="12" y="20" fill="#9bb0c5" fontSize="11">
          {controls.mode} · enable_chat={String(controls.enable_chat)}
        </text>
      </svg>
    );
  }
  if (slug === "contrastive-space" && state?.scene?.similarity) {
    const m = state.scene.similarity as number[][];
    return (
      <div className="grid gap-1" style={{ gridTemplateColumns: `repeat(${m.length}, 1fr)` }}>
        {m.flatMap((row, i) =>
          row.map((v, j) => (
            <div key={`${i}-${j}`} className="aspect-square rounded-sm" style={{ background: `rgba(118,185,0,${v})` }} title={`${i},${j}=${v.toFixed(2)}`} />
          ))
        )}
      </div>
    );
  }
  return (
    <div className="text-sm text-[var(--muted)]">
      Architecture preview for <span className="text-nv-green">{slug}</span>. Run after you predict to fill metrics.
      {state?.scene && <pre className="mt-3 overflow-auto text-xs">{JSON.stringify(state.scene, null, 2)}</pre>}
    </div>
  );
}

function revealedText(state: any, fallback: any) {
  return state ? fallback : "?";
}
