export const EVIDENCE: Record<string, { label: string; className: string; hint: string }> = {
  COURSE_SOURCE: { label: "NVIDIA COURSE SOURCE", className: "bg-sky-500/15 text-sky-300 border-sky-500/40", hint: "Explicitly present in supplied notebooks or slides." },
  EXPECTED_RESULT: { label: "EXPECTED RESULT", className: "bg-amber-500/15 text-amber-200 border-amber-500/40", hint: "The notebook says this should happen; this clone does not prove it with stored outputs." },
  SIMULATED_RESULT: { label: "SIMULATION", className: "bg-violet-500/15 text-violet-300 border-violet-500/40", hint: "Produced by TwinStateEngine. Not a measurement." },
  ACTUAL_RUN: { label: "ACTUAL RUN", className: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40", hint: "Imported from a real file, endpoint, or telemetry export." },
  TUTOR_INTERPRETATION: { label: "TUTOR INTERPRETATION", className: "bg-zinc-500/15 text-zinc-300 border-zinc-500/40", hint: "Model-generated explanation derived from evidence." },
  EXTERNAL_RESEARCH: { label: "EXTERNAL RESEARCH", className: "bg-fuchsia-500/15 text-fuchsia-300 border-fuchsia-500/40", hint: "Retrieved outside the supplied course. Must not overwrite course definitions." },
};
