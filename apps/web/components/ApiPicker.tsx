"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

const ENGINES = [
  { value: "demo", label: "Demo — offline, no key" },
  { value: "openai", label: "OpenAI" },
  { value: "nim", label: "NVIDIA NIM" },
  { value: "huggingface", label: "Hugging Face" },
];

export function ApiPicker({ compact = false }: { compact?: boolean }) {
  const [tutor, setTutor] = useState("demo");
  const [msg, setMsg] = useState("");
  useEffect(() => {
    api<{ selected: { tutor_provider: string } }>("/api/providers").then((d) => setTutor(d.selected.tutor_provider));
  }, []);
  return (
    <div className={compact ? "space-y-2" : "card space-y-3"}>
      <h2 className="font-semibold">Which API do you want?</h2>
      <p className="text-sm text-[var(--muted)]">
        Default is Demo. Switching to OpenAI, NIM, or Hugging Face requires an env key; if the vendor is offline the tutor
        discloses a Demo fallback instead of switching silently.
      </p>
      <div className="flex flex-wrap gap-2">
        {ENGINES.map((e) => (
          <button
            key={e.value}
            type="button"
            className={`btn-ghost ${tutor === e.value ? "border-nv-green text-nv-green" : ""}`}
            onClick={() => setTutor(e.value)}
          >
            {e.label}
          </button>
        ))}
      </div>
      <button
        className="btn"
        type="button"
        onClick={async () => {
          const r = await api<{ warning?: string }>("/api/providers", {
            method: "PUT",
            body: JSON.stringify({ tutor_provider: tutor, voice_provider: "off", research_provider: "off", depth: "engineer", course_mode: "course" }),
          });
          setMsg(r.warning || `Tutor engine set to ${tutor}.`);
        }}
      >
        Use this tutor engine
      </button>
      {msg && <p className="text-sm text-nv-green">{msg}</p>}
    </div>
  );
}
