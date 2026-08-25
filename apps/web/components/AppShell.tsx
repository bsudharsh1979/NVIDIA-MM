"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpen,
  Brain,
  ClipboardCheck,
  FlaskConical,
  GitGraph,
  Home,
  Library,
  LineChart,
  Map,
  MessageSquare,
  Repeat,
  Settings,
  Sparkles,
  Boxes,
} from "lucide-react";
import { useEffect, useState } from "react";

const NAV = [
  { href: "/", label: "Home", icon: Home },
  { href: "/learn", label: "Learn", icon: Sparkles },
  { href: "/tutor", label: "Tutor", icon: MessageSquare },
  { href: "/concepts", label: "Concept Map", icon: Map },
  { href: "/notebooks", label: "Notebooks", icon: BookOpen },
  { href: "/twins", label: "Digital Twins", icon: Boxes },
  { href: "/experiments", label: "Experiments", icon: FlaskConical },
  { href: "/practice", label: "Practice", icon: Brain },
  { href: "/review", label: "Review", icon: Repeat },
  { href: "/assessment", label: "Assessment", icon: ClipboardCheck },
  { href: "/progress", label: "Progress", icon: LineChart },
  { href: "/sources", label: "Sources", icon: Library },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const [dark, setDark] = useState(true);
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--fg)]">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 bg-nv-green text-black px-3 py-2 rounded">
        Skip to content
      </a>
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 flex-col border-r border-[var(--line)] bg-[var(--panel)] md:flex">
        <div className="px-5 py-6">
          <div className="text-[10px] uppercase tracking-[0.25em] text-nv-green">NVIDIA DLI</div>
          <div className="mt-1 font-semibold leading-tight">Modality Twin Academy</div>
          <div className="mt-1 text-xs text-[var(--muted)]">Multimodal AI · fusion · VSS · CILP</div>
        </div>
        <nav className="flex-1 overflow-y-auto px-2 pb-6" aria-label="Main">
          {NAV.map((item) => {
            const active = item.href === "/" ? path === "/" : path.startsWith(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`mb-0.5 flex items-center gap-2 rounded-lg px-3 py-2 text-sm ${
                  active ? "bg-nv-green/15 text-nv-green" : "text-[var(--muted)] hover:bg-white/5 hover:text-[var(--fg)]"
                }`}
              >
                <Icon size={16} aria-hidden />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <button
          type="button"
          onClick={() => setDark((d) => !d)}
          className="m-3 rounded-lg border border-[var(--line)] px-3 py-2 text-xs"
        >
          {dark ? "Light mode" : "Dark mode"}
        </button>
      </aside>
      <div className="md:pl-60">
        <header className="sticky top-0 z-20 flex items-center justify-between border-b border-[var(--line)] bg-[var(--bg)]/90 px-4 py-3 backdrop-blur md:hidden">
          <span className="font-semibold">Modality Twin Academy</span>
          <Link href="/settings" className="text-nv-green text-sm">
            APIs
          </Link>
        </header>
        <nav className="flex gap-2 overflow-x-auto border-b border-[var(--line)] px-3 py-2 md:hidden" aria-label="Mobile">
          {NAV.map((item) => (
            <Link key={item.href} href={item.href} className="whitespace-nowrap rounded-full border border-[var(--line)] px-3 py-1 text-xs">
              {item.label}
            </Link>
          ))}
        </nav>
        <main id="main" className="mx-auto max-w-6xl px-4 py-8">
          {children}
        </main>
      </div>
    </div>
  );
}
