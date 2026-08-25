"use client";

import { useState } from "react";
import { api } from "@/lib/api";

export function NotesPanel({ targetType, targetId }: { targetType: string; targetId: string }) {
  const [body, setBody] = useState("");
  const [msg, setMsg] = useState("");
  return (
    <div className="card space-y-2 text-sm">
      <h2 className="font-semibold">Learner note</h2>
      <textarea
        className="w-full rounded-lg border border-[var(--line)] bg-transparent p-2"
        rows={3}
        value={body}
        onChange={(e) => setBody(e.target.value)}
        placeholder="Attach a note to this source…"
        aria-label="Learner note"
      />
      <div className="flex flex-wrap gap-2">
        <button
          className="btn"
          type="button"
          onClick={async () => {
            await api("/api/notes", { method: "POST", body: JSON.stringify({ target_type: targetType, target_id: targetId, body }) });
            setMsg("Note saved.");
          }}
        >
          Save note
        </button>
        <button
          className="btn-ghost"
          type="button"
          onClick={async () => {
            await api("/api/bookmarks", { method: "POST", body: JSON.stringify({ target_type: targetType, target_id: targetId, body: body || targetId }) });
            setMsg("Bookmarked for Review Later.");
          }}
        >
          Bookmark
        </button>
        <a className="btn-ghost" href={`/tutor?note=${encodeURIComponent(body || `Explain ${targetId}`)}`}>
          Ask tutor about my note
        </a>
      </div>
      {msg && <p className="text-xs text-nv-green">{msg}</p>}
    </div>
  );
}
