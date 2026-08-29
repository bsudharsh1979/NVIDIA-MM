import Link from "next/link";
import { EvidenceBadge } from "@/components/EvidenceBadge";

export const metadata = { title: "How it works · Modality Twin Academy" };

const EVIDENCE_ROWS = [
  ["COURSE_SOURCE", "Text or code taken directly from your course notebooks, with a file + cell locator."],
  ["EXPECTED_RESULT", "What the course narrative says should happen — no stored output exists in this clone."],
  ["SIMULATED_RESULT", "A number produced by an educational digital twin. The twin engine is typed so it can never claim to be a real run."],
  ["ACTUAL_RUN", "Only data you import yourself on the Experiments page (AIPerf, CSV, Prometheus…)."],
  ["TUTOR_INTERPRETATION", "The tutor's own reasoning on top of retrieved sources."],
  ["EXTERNAL_RESEARCH", "Optional web research (Perplexity), clearly separated from course facts."],
] as const;

export default function AboutPage() {
  return (
    <div className="max-w-3xl space-y-6">
      <header>
        <h1 className="text-3xl font-semibold">How this academy works</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">
          A digital-twin learning platform for the NVIDIA DLI course <em>Building Multimodal AI Applications</em>. Not
          affiliated with or endorsed by NVIDIA — the notebooks under <code>course-materials/</code> are your own
          personal-use copies, and every explanation here is original teaching text grounded in them.
        </p>
      </header>

      <section className="card space-y-2 text-sm">
        <h2 className="text-lg font-semibold">The learning loop</h2>
        <p>
          Learn → Predict → Experiment → Observe → Explain → Diagnose → Practice → Prove mastery. Every simulation has a
          predict-before-run gate: you write a hypothesis before the twin reveals metrics, because guessing first is what
          makes feedback stick.
        </p>
      </section>

      <section className="card space-y-3 text-sm">
        <h2 className="text-lg font-semibold">Every number carries exactly one evidence label</h2>
        <ul className="space-y-2">
          {EVIDENCE_ROWS.map(([type, hint]) => (
            <li key={type} className="flex flex-wrap items-start gap-2">
              <EvidenceBadge type={type} />
              <span className="text-[var(--muted)]">{hint}</span>
            </li>
          ))}
        </ul>
        <p className="text-[var(--muted)]">
          This is enforced in code and tests: the simulation engine rejects the <code>ACTUAL_RUN</code> label at the type
          level, so a twin curve can never be laundered into a measurement.
        </p>
      </section>

      <section className="card space-y-2 text-sm">
        <h2 className="text-lg font-semibold">Digital twins</h2>
        <p>
          Eleven interactive simulations mirror the systems the course teaches: LiDAR beam geometry, the fusion lab
          (early/late/concat/matmul), modality explorer (audio, CT), CLIP-style contrastive space, projection lab, the OCR
          pipeline, VSS chunking, Graph-RAG, the CILP assessment, an incident-diagnosis drill that withholds ground truth
          until you commit a cause, and an operational risk radar. All outputs are <em>simulated</em> teaching signals.
        </p>
        <Link className="btn mt-1 w-fit" href="/twins">
          Open the twins
        </Link>
      </section>

      <section className="card space-y-2 text-sm">
        <h2 className="text-lg font-semibold">Audio lectures</h2>
        <p>
          Each notebook has a narrated walkthrough: the big idea, a mental model (simple everyday analogies by default, a
          research-grade version on the EXPERT toggle), concept dives, the game plan, one brief stage per section of cells,
          and the one thing to remember. Simple mode glosses jargon on first mention. Audio uses ElevenLabs when configured
          and falls back to the voice built into your browser — never required.
        </p>
      </section>

      <section className="card space-y-2 text-sm">
        <h2 className="text-lg font-semibold">Safety and keys</h2>
        <p>
          Notebook code is data: it is parsed and displayed, never executed. Shell and cluster commands are flagged{" "}
          <code>never_execute</code> with a visible banner. The whole core app runs with zero API keys (offline Demo tutor,
          browser voice); OpenAI, NVIDIA NIM, Hugging Face, ElevenLabs, Sarvam, and Perplexity only enhance it, and any
          fallback is disclosed — never silent. Keys live in server-side environment secrets, never in this repository.
        </p>
        <Link className="btn-ghost mt-1 w-fit" href="/setup">
          See what is configured
        </Link>
      </section>

      <section className="card space-y-2 text-sm">
        <h2 className="text-lg font-semibold">Why links never rot</h2>
        <p>
          Content ids are deterministic — <code>sha1</code> of the file path for artifacts and of{" "}
          <code>artifact:locator:kind:seq</code> for spans — so a redeploy or a fresh database regenerates the exact same
          ids. Notebooks also resolve by plain file name, and 404s explain staleness instead of guessing.
        </p>
      </section>
    </div>
  );
}
