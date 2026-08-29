"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";

type Msg = { role: string; text: string; citations?: any[]; telemetry?: any; evidence?: string };

function TutorInner() {
  const note = useSearchParams().get("note");
  const [mode, setMode] = useState("course");
  const [depth, setDepth] = useState("engineer");
  const [provider, setProvider] = useState("demo");
  const [input, setInput] = useState(note || "Explain late fusion vs intermediate concat on the colored cubes task.");
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [sessionId, setSessionId] = useState<number | undefined>();
  const [busy, setBusy] = useState(false);
  const [teach, setTeach] = useState("");
  const [teachConcept, setTeachConcept] = useState("late-fusion");
  const [teachResult, setTeachResult] = useState<any>(null);
  const [listening, setListening] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const speaking = useRef<SpeechSynthesisUtterance | null>(null);

  useEffect(() => {
    api<{ selected: { tutor_provider: string; depth: string; course_mode: string } }>("/api/providers")
      .then((d) => {
        setProvider(d.selected.tutor_provider);
        setDepth(d.selected.depth);
        setMode(d.selected.course_mode);
      })
      .catch(() => {});
  }, []);

  function interruptVoice() {
    window.speechSynthesis?.cancel();
    speaking.current = null;
    setListening(false);
  }

  function speak(text: string) {
    interruptVoice();
    if (!window.speechSynthesis) return;
    const u = new SpeechSynthesisUtterance(text.slice(0, 1200));
    speaking.current = u;
    window.speechSynthesis.speak(u);
  }

  function listen() {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) {
      setInput((t) => t || "(Browser speech recognition not available — type instead.)");
      return;
    }
    interruptVoice();
    const rec = new SR();
    rec.lang = "en-US";
    rec.onresult = (e: any) => {
      const said = e.results[0][0].transcript;
      setInput(said);
      setListening(false);
      send(said);
    };
    rec.onerror = () => setListening(false);
    setListening(true);
    rec.start();
  }

  async function send(text: string) {
    setBusy(true);
    setErr(null);
    setMsgs((m) => [...m, { role: "user", text }]);
    try {
      const r = await api<any>("/api/tutor", {
        method: "POST",
        body: JSON.stringify({ message: text, mode, depth, provider, session_id: sessionId }),
      });
      setSessionId(r.session_id);
      setMsgs((m) => [
        ...m,
        { role: "assistant", text: r.text, citations: r.citations, telemetry: r.telemetry, evidence: r.evidence_type || r.telemetry?.evidence_type },
      ]);
    } catch (e) {
      setErr(String(e));
      setMsgs((m) => [...m, { role: "assistant", text: `Tutor request failed: ${e}` }]);
    } finally {
      setBusy(false);
      setInput("");
    }
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_300px]">
      <div>
        <h1 className="text-3xl font-semibold">Tutor</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Course Mode uses only notebooks. Research Mode may call Perplexity and is labeled EXTERNAL_RESEARCH. Voice uses the
          browser; ElevenLabs/Sarvam stay optional in Settings.
        </p>
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
        <div className="mt-4 space-y-3">
          {err && <p className="mt-2 text-sm text-amber-300">{err}</p>}
          {msgs.map((m, i) => (
            <article key={i} className="card text-sm whitespace-pre-wrap">
              <div className="text-xs uppercase text-[var(--muted)]">{m.role}</div>
              <div className="mt-2">{m.text}</div>
              {m.citations?.length ? (
                <ul className="mt-3 space-y-1 text-xs">
                  {m.citations.map((c: any, j: number) => (
                    <li key={j}>
                      <EvidenceBadge type="COURSE_SOURCE" />{" "}
                      <a className="text-nv-green" href={`/sources?file=${encodeURIComponent(c.locator?.file || "")}`}>
                        View source {c.locator?.file} cell {c.locator?.cell_index}
                      </a>{" "}
                      — {c.title}
                    </li>
                  ))}
                </ul>
              ) : null}
              {m.evidence && <EvidenceBadge type={m.evidence} />}
              {m.telemetry ? (
                <details className="mt-3 text-xs">
                  <summary className="cursor-pointer text-nv-green">How this answer was served</summary>
                  <pre className="mt-2 overflow-auto">{JSON.stringify(m.telemetry, null, 2)}</pre>
                  <p className="mt-2">These tokens/latency are from the tutor call itself — not VSS chunk_duration and not an ACTUAL_RUN from a lab cluster.</p>
                </details>
              ) : null}
              {m.role === "assistant" && (
                <button className="btn-ghost mt-2 text-xs" type="button" onClick={() => speak(m.text)}>
                  Speak
                </button>
              )}
            </article>
          ))}
        </div>
        <form
          className="mt-4 flex flex-wrap gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            if (input.trim()) send(input.trim());
          }}
        >
          <input className="min-w-[12rem] flex-1 rounded-lg border border-[var(--line)] bg-transparent px-3 py-2" value={input} onChange={(e) => setInput(e.target.value)} aria-label="Message" />
          <button className="btn" disabled={busy}>
            {busy ? "…" : "Send"}
          </button>
          <button className="btn-ghost" type="button" onClick={listen}>
            {listening ? "Listening…" : "Voice in"}
          </button>
          <button className="btn-ghost" type="button" onClick={interruptVoice}>
            Stop / barge-in
          </button>
        </form>
      </div>
      <aside className="space-y-4">
        <div className="card h-fit text-sm">
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
        </div>
        <div className="card space-y-2 text-sm">
          <h2 className="font-semibold">Teach-back</h2>
          <p className="text-[var(--muted)]">Explain a concept in your own words. Mastery weights this highly.</p>
          <select className="w-full rounded-lg border border-[var(--line)] bg-transparent p-2" value={teachConcept} onChange={(e) => setTeachConcept(e.target.value)} aria-label="Teach-back concept">
            {["late-fusion", "early-fusion", "lidar-xyza", "clip-style", "cilp", "vss-chunk-duration", "graph-rag"].map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <textarea className="w-full rounded-lg border border-[var(--line)] bg-transparent p-2" rows={5} value={teach} onChange={(e) => setTeach(e.target.value)} placeholder="Let me explain…" />
          <button
            className="btn"
            type="button"
            onClick={async () => setTeachResult(await api("/api/teachback", { method: "POST", body: JSON.stringify({ text: teach, concept_slug: teachConcept }) }))}
          >
            Grade teach-back
          </button>
          {teachResult && <pre className="overflow-auto whitespace-pre-wrap text-xs">{teachResult.feedback}</pre>}
        </div>
      </aside>
    </div>
  );
}

export default function TutorPage() {
  return (
    <Suspense fallback={<p>Loading tutor…</p>}>
      <TutorInner />
    </Suspense>
  );
}
