import Link from "next/link";
import { Armchair, ArrowRight, BookOpen, CalendarDays, MapPin, Users } from "lucide-react";
import { identity, runProduction } from "@/lib/production-service";
import { loadAllocationResult } from "@/lib/allocation";
import type { AllocationResult } from "@/lib/allocation-types";

export const dynamic = "force-dynamic";

export default async function EventPage() {
  const user = await identity();
  if (user?.role !== "admin") return <main className="p-8">Sign in as an event administrator through the host platform.</main>;
  const [setup, plan] = await Promise.all([
    runProduction<{ floor_plan: AllocationResult["floor_plan"]; registrations: number }>({ command: "setup", event_id: user.event_id }),
    loadAllocationResult(),
  ]);
  const seatPath = `/event/${encodeURIComponent(user.event_id)}/seat`;
  const available = setup.floor_plan.rows.flatMap(row => row.seats).filter(seat => !seat.is_blocked).length;
  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900 md:flex">
      <aside className="flex flex-col border-b p-5 md:w-60 md:shrink-0 md:border-r md:border-b-0">
        <div className="mb-8 flex items-center gap-3"><div className="rounded-xl bg-zinc-900 p-2 text-white"><BookOpen size={22}/></div><div><p className="font-semibold">寺务管理系统</p><p className="text-xs text-zinc-500">PJKIT · Staff portal</p></div></div>
        <p className="mb-3 text-xs text-zinc-500">运营管理 · Operations</p>
        <nav aria-label="Staff navigation" className="flex gap-2 md:flex-col">
          <Link href="/event" aria-current="page" className="flex items-center gap-3 rounded-lg bg-zinc-200/60 px-3 py-2 text-sm font-medium"><CalendarDays size={17}/>法会活动 · Events</Link>
          <Link href={seatPath} className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm hover:bg-zinc-100"><Armchair size={17}/>座位安排 · Seating</Link>
        </nav>
        <p className="mt-auto hidden pt-12 text-xs text-zinc-500 md:block">八打灵观音亭<br/>PJ Kwan Inn Teng</p>
      </aside>
      <main className="m-2 min-w-0 flex-1 rounded-2xl border bg-white shadow-sm">
        <header className="border-b px-6 py-4 text-sm text-zinc-500">Staff portal <span className="mx-3">/</span> Events</header>
        <div className="mx-auto max-w-6xl p-6 lg:p-10">
          <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">Event management</p>
          <h1 className="mt-2 text-2xl font-semibold">法会活动 <span className="font-normal text-zinc-400">/ Events</span></h1>
          <p className="mt-2 text-sm text-zinc-500">Manage the assembly and prepare seating for arriving participants.</p>
          <div className="my-8 grid gap-4 sm:grid-cols-3">
            {[{ label: "Current event", value: "2026", icon: CalendarDays }, { label: "Registrations", value: setup.registrations.toLocaleString(), icon: Users }, { label: "Assignable seats", value: available.toLocaleString(), icon: Armchair }].map(({ label, value, icon: Icon }) => <div key={label} className="rounded-2xl border p-5 shadow-sm"><p className="flex items-center gap-2 text-sm text-zinc-500"><Icon size={16}/>{label}</p><p className="mt-5 text-3xl font-semibold">{value}</p></div>)}
          </div>
          <section className="overflow-hidden rounded-2xl border" aria-labelledby="event-title">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b bg-zinc-50 px-6 py-4"><span className="text-sm font-medium">法会 · Dharma assembly</span><span className="rounded-full bg-white px-3 py-1 text-xs ring-1 ring-zinc-200">{plan ? "Seating plan available" : "Ready for allocation"}</span></div>
            <div className="p-6 lg:p-8">
              <h2 id="event-title" className="text-2xl font-semibold">2026 梁皇寶懺大法會</h2>
              <p className="mt-2 text-zinc-500">Emperor Liang Repentance Dharma Assembly</p>
              <div className="mt-6 flex flex-wrap gap-5 text-sm text-zinc-600"><span className="flex items-center gap-2"><MapPin size={16}/>PJ Kwan Inn Teng Main Hall</span><span className="flex items-center gap-2"><Users size={16}/>{setup.registrations} registrations</span></div>
              <div className="mt-8 border-t pt-6">
                <h3 className="font-medium">座位分配 · Seating allocation</h3>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-500">Open the seating workspace to load the latest draft or generate a new one from the event registrations. Review the seating map, adjust allocations, and publish when ready.</p>
                <div className="mt-5 flex flex-wrap items-center gap-4">
                  <Link href={seatPath} prefetch={false} className="inline-flex items-center gap-2 rounded-lg bg-zinc-900 px-5 py-3 text-sm font-medium text-white hover:bg-zinc-700">Enter seating allocation <ArrowRight size={16}/></Link>
                </div>
                <p className="mt-3 text-xs text-zinc-500">Choose how to begin. Published seating stays unchanged.</p>
              </div>
            </div>
          </section>
          <ol className="mt-8 grid gap-4 text-sm text-zinc-500 sm:grid-cols-3"><li><span className="mr-2 font-semibold text-zinc-900">01</span>Open event seating</li><li><span className="mr-2 font-semibold text-zinc-900">02</span>Generate & review the map</li><li><span className="mr-2 font-semibold text-zinc-900">03</span>Adjust & publish</li></ol>
        </div>
      </main>
    </div>
  );
}
