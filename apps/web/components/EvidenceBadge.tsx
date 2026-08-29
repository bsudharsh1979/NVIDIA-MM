import { EVIDENCE } from "@/lib/evidence";

export function EvidenceBadge({ type }: { type: string }) {
  const meta = EVIDENCE[type] || EVIDENCE.TUTOR_INTERPRETATION;
  return (
    <span title={meta.hint} className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold tracking-wide ${meta.className}`}>
      {type === "COURSE_SOURCE" ? "🔵" : type === "SIMULATED_RESULT" ? "🟣" : type === "ACTUAL_RUN" ? "🟢" : "⚪"} {meta.label}
    </span>
  );
}
