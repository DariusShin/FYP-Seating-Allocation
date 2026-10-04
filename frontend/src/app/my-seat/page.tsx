import { PublishedSeat } from "@/components/public/published-seat";
export const dynamic = "force-dynamic";
export default async function MySeatPage({
  searchParams,
}: {
  searchParams: Promise<{ participant?: string }>;
}) {
  const { participant } = await searchParams;
  return <PublishedSeat participant={participant} />;
}
