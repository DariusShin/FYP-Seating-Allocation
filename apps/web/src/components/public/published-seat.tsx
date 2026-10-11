"use client";
import { useEffect, useState } from "react";
import type { PublishedAllocation } from "@/lib/public-allocation-types";
import { PublicSeatView } from "./public-seat-view";

export function PublishedSeat({ participant }: { participant?: string }) {
  const [value, setValue] = useState<PublishedAllocation | null>(null);
  const [refreshError, setRefreshError] = useState(false);
  useEffect(() => {
    let active = true;
    let inFlight = false;
    async function load() {
      if (inFlight) return;
      inFlight = true;
      try {
        const response = await fetch(
          `/api/allocation${participant ? `?participant=${encodeURIComponent(participant)}` : ""}`,
          { cache: "no-store" },
        );
        if (!response.ok && response.status !== 401 && response.status !== 403)
          throw new Error("Refresh failed");
        const next: PublishedAllocation = await response.json();
        if (active) {
          setValue(next);
          setRefreshError(false);
        }
      } catch {
        if (active) setRefreshError(true);
      } finally {
        inFlight = false;
      }
    }
    void load();
    const timer = setInterval(load, 10000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [participant]);
  if (!value)
    return (
      <main className="p-8">
        {refreshError
          ? "暂时无法载入，请稍候自动重试。Unable to load; retrying automatically."
          : "正在载入座位图… Loading published seating…"}
      </main>
    );
  if (value.status !== "published")
    return (
      <main className="p-8">
        {value.message ?? "暂无已公布座位图 / No published plan available."}
      </main>
    );
  return (
    <>
      {refreshError && (
        <p
          role="status"
          className="bg-amber-100 p-2 text-center text-xs text-amber-900"
        >
          暂时无法更新，正在显示上次公布的座位图。Showing the last loaded plan;
          retrying automatically.
        </p>
      )}
      <PublicSeatView result={value} />
    </>
  );
}
