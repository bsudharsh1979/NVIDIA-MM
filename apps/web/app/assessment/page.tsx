"use client";

import { useState } from "react";
import Link from "next/link";
import { api, friendlyError } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { EvidenceBadge } from "@/components/EvidenceBadge";
import { ErrorCard, LoadingCard } from "@/components/Status";

export default function AssessmentPage() {
  const { data: spec, error, loading, retry } = useApi<any>("/api/assessment");
  const [architecture, setArchitecture] = useState("cilp_plus_projector_frozen_head");
  const [recipe, setRecipe] = useState("freeze_lidar_and_cilp_train_projector");
  const [defense, setDefense] = useState("");
  const [grade, setGrade] = useState<any>(null);
  const [gradeErr, setGradeErr] = useState<string | null>(null);
  if (loading) return <LoadingCard label="Loading the assessment arena" />;
  if (error) return <ErrorCard error={error} retry={retry} title="Could not load the assessment" />;
  if (!spec) return null;
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold">{spec.title}</h1>
      <p className="text-sm text-[var(--muted)]">
        Grounded in {spec.source.file}. The tutor grades reasoning, not only the dropdown. Twin numbers stay <EvidenceBadge type="SIMULATED_RESULT" />
      </p>
      <ol className="space-y-3">
        {spec.steps.map((s: any) => (
          <li key={s.id} className="card text-sm">
            <h2 className="font-semibold">{s.title}</h2>
            {s.text && <p className="mt-1 text-[var(--muted)]">{s.text}</p>}
            {s.twin && (
              <Link className="btn mt-2" href={`/twins/${s.twin}`}>
                Run twin
              </Link>
            )}
          </li>
        ))}
      </ol>
      <div className="card space-y-3">
        <label className="block text-sm">
          Architecture
          <select className="mt-1 w-full rounded-lg border border-[var(--line)] bg-transparent p-2" value={architecture} onChange={(e) => setArchitecture(e.target.value)}>
            <option value="rgb_finetune_lidar_cnn">Fine-tune lidar_cnn on RGB pixels</option>
            <option value="cilp_plus_projector_frozen_head">CILP + projector + frozen LiDAR head</option>
            <option value="early_fusion_net8">Early fusion Net(8)</option>
            <option value="vss_summarize_pngs">VSS summarize on PNGs</option>
          </select>
        </label>
        <label className="block text-sm">
          Recipe
          <select className="mt-1 w-full rounded-lg border border-[var(--line)] bg-transparent p-2" value={recipe} onChange={(e) => setRecipe(e.target.value)}>
            <option value="unfreeze_all">Unfreeze everything</option>
            <option value="freeze_lidar_and_cilp_train_projector">Freeze lidar_cnn and CILP; train projector</option>
            <option value="train_only_lidar_on_rgb">Train only lidar net on RGB</option>
          </select>
        </label>
        <textarea className="w-full rounded-lg border border-[var(--line)] bg-transparent p-2" rows={4} placeholder="Defend your recommendation…" value={defense} onChange={(e) => setDefense(e.target.value)} />
        <button
          className="btn"
          onClick={async () => {
            try {
              setGradeErr(null);
              setGrade(await api("/api/assessment/grade", { method: "POST", body: JSON.stringify({ architecture, recipe, defense }) }));
            } catch (e) {
              setGradeErr(friendlyError(e));
            }
          }}
        >
          Grade reasoning
        </button>
        {gradeErr && <p className="text-sm text-amber-300">{gradeErr}</p>}
        {grade && <pre className="overflow-auto text-xs">{JSON.stringify(grade, null, 2)}</pre>}
      </div>
    </div>
  );
}
