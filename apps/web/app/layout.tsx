import type { Metadata } from "next";
import { AppShell } from "@/components/AppShell";
import "./globals.css";

export const metadata: Metadata = {
  title: "Modality Twin Academy",
  description: "Personalized technical learning for NVIDIA multimodal AI — fusion, contrastive pre-training, VSS, Graph-RAG, CILP. Not affiliated with or endorsed by NVIDIA.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
