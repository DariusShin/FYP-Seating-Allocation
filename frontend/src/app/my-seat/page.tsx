import type { Metadata } from "next";

import { PublicSeatView } from "@/components/public/public-seat-view";
import { loadAllocationResult } from "@/lib/allocation";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "My Seat",
  description: "Look up your assigned seat for the event",
};

export default async function MySeatPage({
  searchParams,
}: {
  searchParams: Promise<{ participant?: string }>;
}) {
  const { participant } = await searchParams;
  const result = await loadAllocationResult();
  return (
    <PublicSeatView
      initialResult={result}
      initialParticipantId={participant ?? null}
    />
  );
}
