import { identity } from "@/lib/production-service";
import { redirect } from "next/navigation";
import { venuePath } from "@/components/seat/helpers";
export const dynamic = "force-dynamic";
export default async function VenuePage() {
  const user = await identity();
  if (user?.role !== "admin" && user?.role !== "staff")
    return (
      <main className="p-8">
        Sign in as venue staff to open the published display.
      </main>
    );
  redirect(venuePath(user.event_id));
}
