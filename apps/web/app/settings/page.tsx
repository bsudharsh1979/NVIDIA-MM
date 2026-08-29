"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function SettingsPage() {
  const [data, setData] = useState<any>(null);
  const [form, setForm] = useState({
    tutor_provider: "demo",
    voice_provider: "off",
    research_provider: "off",
    depth: "engineer",
    course_mode: "course",
  });
  const [msg, setMsg] = useState("");
  useEffect(() => {
    api<any>("/api/providers")
      .then((d) => {
        setData(d);
        setForm((f) => ({ ...f, ...d.selected }));
      })
      .catch((e) => setMsg(`Could not load provider status: ${e}`));
  }, []);
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold">Which API do you want?</h1>
      <p className="text-sm text-[var(--muted)]">
        The academy boots in <strong>Demo</strong> with no keys. Pick a tutor engine when you have credentials in the environment
        (never committed). Voice and Perplexity are optional. Providers never switch silently — fallbacks are disclosed.
      </p>
      <div className="card space-y-3">
        <label className="block text-sm">
          Tutor engine
          <select className="mt-1 w-full rounded-lg border border-[var(--line)] bg-transparent p-2" value={form.tutor_provider} onChange={(e) => setForm({ ...form, tutor_provider: e.target.value })}>
            <option value="demo">Demo — offline retriever (default)</option>
            <option value="openai">OpenAI Responses / Chat Completions</option>
            <option value="nim">NVIDIA NIM (OpenAI-compatible NIM_BASE_URL)</option>
            <option value="huggingface">Hugging Face Inference</option>
          </select>
        </label>
        <label className="block text-sm">
          Voice
          <select className="mt-1 w-full rounded-lg border border-[var(--line)] bg-transparent p-2" value={form.voice_provider} onChange={(e) => setForm({ ...form, voice_provider: e.target.value })}>
            <option value="off">Off</option>
            <option value="elevenlabs">ElevenLabs</option>
            <option value="sarvam">Sarvam (Indic; keep NVIDIA terms in English)</option>
            <option value="openai_realtime">OpenAI Realtime (barge-in)</option>
          </select>
        </label>
        <label className="block text-sm">
          Research
          <select className="mt-1 w-full rounded-lg border border-[var(--line)] bg-transparent p-2" value={form.research_provider} onChange={(e) => setForm({ ...form, research_provider: e.target.value })}>
            <option value="off">Off (Course Mode only)</option>
            <option value="perplexity">Perplexity</option>
          </select>
        </label>
        <button
          className="btn"
          onClick={async () => {
            try {
              const r = await api<any>("/api/providers", { method: "PUT", body: JSON.stringify(form) });
              setMsg(r.warning || "Saved.");
            } catch (e) {
              setMsg(`Save failed: ${e}`);
            }
          }}
        >
          Save provider choice
        </button>
        {msg && <p className="text-sm text-nv-green">{msg}</p>}
      </div>
      <div className="card">
        <h2 className="font-semibold">Health</h2>
        <ul className="mt-2 space-y-1 text-sm">
          {data?.matrix?.map((p: any) => (
            <li key={p.name} className="flex justify-between">
              <span>{p.name}</span>
              <span className={p.status === "connected" ? "text-nv-green" : "text-[var(--muted)]"}>{p.status}</span>
            </li>
          ))}
        </ul>
        <p className="mt-3 text-xs text-[var(--muted)]">{data?.ask}</p>
      </div>
    </div>
  );
}
