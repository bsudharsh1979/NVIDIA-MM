"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, use } from "react";
import { TwinStudio } from "@/components/TwinStudio";

function Inner({ slug }: { slug: string }) {
  const sp = useSearchParams();
  return <TwinStudio slug={slug} initialPrediction={sp.get("prediction") || ""} scenario={sp.get("scenario") || ""} />;
}

export default function TwinPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  return (
    <Suspense fallback={<p>Loading twin…</p>}>
      <Inner slug={slug} />
    </Suspense>
  );
}
