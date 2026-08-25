"use client";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { TwinStudio } from "@/components/TwinStudio";

function Inner({ slug }: { slug: string }) {
  const sp = useSearchParams();
  return <TwinStudio slug={slug} initialPrediction={sp.get("prediction") || ""} />;
}

export default function TwinPage({ params }: { params: { slug: string } }) {
  return (
    <Suspense fallback={<p>Loading twin…</p>}>
      <Inner slug={params.slug} />
    </Suspense>
  );
}
