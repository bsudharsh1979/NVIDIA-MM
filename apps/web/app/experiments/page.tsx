"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";

export default function ExperimentsPage() {
  const [kind, setKind] = useState("json");
  const [name, setName] = useState("aiperf-run");
  const [raw, setRaw] = useState('{"cilp_valid_loss": 3.12, "finetuned_accuracy": 0.96, "freeze_lidar_cnn": true, "split": "val"}');
  const [rows, setRows] = useState<any[]>([]);
  const [imported, setImported] = useState<any>(null);
  const [cmp, setCmp] = useState<any>(null);
  useEffect(() => {
    api<any[]>("/api/experiments").then(setRows);
  }, [imported]);
  async function upload() {
    const fd = new FormData();
    fd.set("kind", kind);
    fd.set("name", name);
    fd.set("raw_text", raw);
    const res = await fetch("/api/experiments/import", { method: "POST", body: fd });
    setImported(await res.json());
  }
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold">Experiments</h1>
      <p className="text-sm text-[var(--muted)]">
        Imports are stored as <EvidenceBadge type="ACTUAL_RUN" />. The original payload is never overwritten. Twins remain{" "}
        <EvidenceBadge type="SIMULATED_RESULT" />
      </p>
      <div className="card space-y-2">
        <select className="btn-ghost bg-transparent" value={kind} onChange={(e) => setKind(e.target.value)}>
          {["json", "csv", "aiperf", "prometheus", "kubectl", "logs", "otel"].map((k) => (
            <option key={k}>{k}</option>
          ))}
        </select>
        <input className="w-full rounded-lg border border-[var(--line)] bg-transparent px-2 py-1" value={name} onChange={(e) => setName(e.target.value)} />
        <textarea className="w-full rounded-lg border border-[var(--line)] bg-transparent p-2 font-mono text-xs" rows={6} value={raw} onChange={(e) => setRaw(e.target.value)} />
        <button className="btn" onClick={upload}>
          Import as ACTUAL_RUN
        </button>
      </div>
      {imported && (
        <div className="card text-sm">
          <h2 className="font-semibold">Explainer</h2>
          <pre className="mt-2 overflow-auto text-xs">{JSON.stringify(imported.explainer, null, 2)}</pre>
        </div>
      )}
      <div className="card">
        <h2 className="font-semibold">Compare two synthetic ACTUAL_RUN payloads</h2>
        <button
          className="btn mt-3"
          onClick={async () =>
            setCmp(
              await api("/api/experiments/compare", {
                method: "POST",
                body: JSON.stringify({
                  a: { metadata: { architecture: "concat", dataset: "colored_cubes", freeze_lidar_cnn: true, split: "val" }, metrics: { valid_error: 0.24 } },
                  b: { metadata: { architecture: "lidar", dataset: "mixed_shapes", freeze_lidar_cnn: false, split: "train" }, metrics: { valid_error: 0.12 } },
                }),
              })
            )
          }
        >
          Detect confounders
        </button>
        {cmp && <pre className="mt-3 overflow-auto text-xs">{JSON.stringify(cmp, null, 2)}</pre>}
      </div>
      <ul className="text-sm">
        {rows.map((r) => (
          <li key={r.id} className="card mt-2">
            {r.name} · {r.kind} · {r.evidence_type}
          </li>
        ))}
      </ul>
    </div>
  );
}
