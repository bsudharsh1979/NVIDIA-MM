"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";

type Msg = { role: string; text: string; citations?: any[]; telemetry?: any };

export default function TutorPage() {
  const [mode, setMode] = useState("course");
  const [depth, setDepth] = useState("engineer");
  const [provider, setProvider] = useState("demo");
  const [input, setInput] = useState("Explain late fusion vs intermediate concat on the colored cubes task.");
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [sessionId, setSessionId] = useState<number | undefined>();
  const [busy, setBusy] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    api<{ selected: { tutor_provider: string; depth: string; course_mode: string } }>("/api/providers").then((d) => {
      setProvider(d.selected.tutor_provider);
      setDepth(d.selected.depth);
      setMode(d.selected.course_mode);
    });
  }, []);
  async function send(text: string) {
    setBusy(true);
    setMsgs((m) => [...m, { role: "user", text }]);
    try {
      const r = await api<any>("/api/tutor", {
        method: "POST",
        body: JSON.stringify({ message: text, mode, depth, provider, session_id: sessionId }),
      });
      setSessionId(r.session_id);
      setMsgs((m) => [...m, { role: "assistant", text: r.text, citations: r.citations, telemetry: r.telemetry }]);
    } finally {
      setBusy(false);
      setInput("");
    }
  }
  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_280px]">
      <div>
        <h1 className="text-3xl font-semibold">Tutor</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">Course Mode uses only notebooks. Research Mode may call Perplexity and is labeled EXTERNAL_RESEARCH.</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <select value={mode} onChange={(e) => setMode(e.target.value)} className="btn-ghost bg-transparent" aria-label="Tutor mode">
            <option value="course">Course Mode</option>
            <option value="research">Research Mode</option>
          </select>
          <select value={depth} onChange={(e) => setDepth(e.target.value)} className="btn-ghost bg-transparent" aria-label="Depth">
            <option value="school">School</option>
            <option value="engineer">Engineer</option>
            <option value="research">Research depth</option>
          </select>
          <select value={provider} onChange={(e) => setProvider(e.target.value)} className="btn-ghost bg-transparent" aria-label="Tutor engine">
            <option value="demo">Demo (offline)</option>
            <option value="openai">OpenAI</option>
            <option value="nim">NVIDIA NIM</option>
            <option value="huggingface">Hugging Face</option>
          </select>
        </div>
        <div ref={box} className="mt-4 space-y-3">
          {msgs.map((m, i) => (
            <article key={i} className="card text-sm whitespace-pre-wrap">
              <div className="text-xs uppercase text-[var(--muted)]">{m.role}</div>
              <div className="mt-2">{m.text}</div>
              {m.citations?.length ? (
                <ul className="mt-3 space-y-1 text-xs">
                  {m.citations.map((c: any, j: number) => (
                    <li key={j}>
                      <EvidenceBadge type="COURSE_SOURCE" /> {c.locator?.file} cell {c.locator?.cell_index} — {c.title}
                    </li>
                  ))}
                </ul>
              ) : null}
              {m.telemetry ? (
                <details className="mt-3 text-xs">
                  <summary className="cursor-pointer text-nv-green">How this answer was served</summary>
                  <pre className="mt-2 overflow-auto">{JSON.stringify(m.telemetry, null, 2)}</pre>
                  <p className="mt-2">Use these metrics as a live example of latency vs tokens — not as VSS chunk_duration.</p>
                </details>
              ) : null}
            </article>
          ))}
        </div>
        <form
          className="mt-4 flex gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            if (input.trim()) send(input.trim());
          }}
        >
          <input className="flex-1 rounded-lg border border-[var(--line)] bg-transparent px-3 py-2" value={input} onChange={(e) => setInput(e.target.value)} aria-label="Message" />
          <button className="btn" disabled={busy}>
            {busy ? "…" : "Send"}
          </button>
        </form>
      </div>
      <aside className="card h-fit text-sm">
        <h2 className="font-semibold">Intents</h2>
        <ul className="mt-2 space-y-1 text-[var(--muted)]">
          {["simpler", "show source", "quiz me", "show digital twin", "let me teach it back", "how this answer was served"].map((x) => (
            <li key={x}>
              <button className="text-left text-nv-green" onClick={() => send(x)}>
                {x}
              </button>
            </li>
          ))}
        </ul>
      </aside>
    </div>
  );
}
