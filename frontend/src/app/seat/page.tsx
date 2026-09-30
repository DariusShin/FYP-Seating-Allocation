import { redirect } from "next/navigation";
import { identity } from "@/lib/production-service";

export const dynamic = "force-dynamic";
export default async function SeatPage() {
    const user = await identity();
    if ((user?.role !== "admin" && user?.role !== "staff")) return <main className="p-8">Sign in as event staff through the host platform.</main>;
    redirect(`/event/${encodeURIComponent(user.event_id)}/seat`);
}
