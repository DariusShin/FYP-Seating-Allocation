"use client";

import { CalendarClock, MapPin, UserRound } from "lucide-react";
import type { PublishedAllocation } from "@/lib/public-allocation-types";
import { PublicSeatMap } from "./public-seat-map";

export function PublicSeatView({ result }: { result: PublishedAllocation }) {
  const floor = result.floor_plan;
  const assignment = result.assignment;
  const mine = new Set(assignment?.seat_ids ?? []);
  const coordinates = assignment?.seats ?? [];
  const event = result.event_details;
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b px-4 py-4 sm:px-6">
        <h1 className="text-lg font-semibold">
          {event?.name ?? result.event_id ?? "PJKIT 2026"}
        </h1>
        <p className="mt-1 text-xs text-muted-foreground">
          我的座位 · My seat{" "}
          <span className="ml-3 inline-flex items-center gap-1">
            <span className="size-1.5 rounded-full bg-emerald-600" />
            已公布座位自动更新 / Published seats update automatically
          </span>
        </p>
      </header>
      <main className="grid w-full grid-cols-1 gap-4 p-4 sm:p-6 lg:grid-cols-[minmax(0,4fr)_minmax(0,1fr)]">
        <section
          className="min-w-0 rounded-xl border bg-card p-3 sm:p-4"
          aria-labelledby="hall-heading"
        >
          <h2 id="hall-heading" className="mb-3 text-sm font-semibold">
            全厅座位图 · Hall floor plan
          </h2>
          {floor && <PublicSeatMap floor={floor} mySeatIds={mine} />}
        </section>
        <aside className="min-w-0 space-y-4">
          <section className="space-y-4 rounded-xl border bg-card p-4">
            <h2 className="flex items-center gap-2 text-sm font-semibold">
              <UserRound className="size-4" />
              登记姓名 / Registered name
            </h2>
            <p className="wrap-break-word text-xl font-semibold">
              {assignment?.full_name ?? "暂无座位安排 / No assignment"}
            </p>
            <div className="border-t pt-3">
              <h3 className="mb-2 flex items-center gap-2 text-sm font-medium">
                <MapPin className="size-4" />
                座位位置 / Your seats
              </h3>
              <div className="space-y-2">
                {coordinates.map((seat) => (
                  <div
                    key={seat.seat_id}
                    className="rounded-lg border border-emerald-600/30 bg-emerald-500/10 p-3"
                  >
                    <p className="font-semibold text-emerald-800 dark:text-emerald-300">
                      {seat.physical_position <=
                      (floor?.aisle_after_position ?? 8)
                        ? "西单"
                        : "东单"}{" "}
                      第 {seat.row_number} 排
                    </p>
                    <p className="mt-2 wrap-break-word text-sm font-medium">
                      {seat.display_name}
                    </p>
                    <p className="mt-1 text-sm">
                      实体位置 {seat.physical_position}
                    </p>
                    <p className="mt-1 text-[11px] text-muted-foreground">
                      Row {seat.row_number} · Position {seat.physical_position}{" "}
                      · {seat.seat_id}
                    </p>
                  </div>
                ))}
              </div>
              {coordinates.length === 2 && (
                <p className="mt-2 text-xs text-muted-foreground">
                  绿色座位包括您与同行者的座位。Both seats in your registration
                  are highlighted.
                </p>
              )}
            </div>
          </section>
          <section className="space-y-3 rounded-xl border bg-card p-4">
            <h2 className="flex items-center gap-2 text-sm font-semibold">
              <CalendarClock className="size-4" />
              活动详情 / Event details
            </h2>
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="text-xs text-muted-foreground">日期 / Date</dt>
                <dd className="mt-1">
                  {event?.date ?? "待公布 / To be announced"}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">时间 / Time</dt>
                <dd className="mt-1">
                  {event?.time ?? "待公布 / To be announced"}
                </dd>
                <dd className="mt-1 text-[11px] text-muted-foreground">
                  {event?.timezone ?? "Asia/Kuala_Lumpur"}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">地点 / Venue</dt>
                <dd className="mt-1 wrap-break-word">
                  {event?.venue ?? "待公布 / To be announced"}
                </dd>
              </div>
            </dl>
          </section>
          <p className="text-[11px] text-muted-foreground">
            面向佛台：左侧为西单，右侧为东单。Facing the altar: west on your
            left, east on your right.
          </p>
        </aside>
      </main>
    </div>
  );
}
