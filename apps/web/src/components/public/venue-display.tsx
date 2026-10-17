"use client";
import { useEffect, useRef, useState } from "react";
import type { AllocationResult } from "@/lib/allocation-types";
import { HallMap } from "@/components/seat/hall-map";
import { chineseVenueName } from "@/lib/venue-names";
import { Button } from "@/components/ui/button";
import {
  saveVenuePdf,
  saveVenuePng,
  venueFileName,
} from "@/lib/venue-export";
import { eventApi } from "@/components/seat/helpers";
type Venue = {
  status: string;
  floor_plan?: AllocationResult["floor_plan"];
  published_at?: string;
  pair_display?: Record<string, { primary_name: string }>;
};

/** Direct exports bypass the print dialog; Print stays for physical copies. */
export function VenueActions({
  disabled,
  saving,
  onPrint,
  onSave,
}: {
  disabled: boolean;
  saving: "pdf" | "png" | "";
  onPrint: () => void;
  onSave: (format: "pdf" | "png") => void;
}) {
  return (
    <div className="flex gap-2">
      <Button variant="outline" size="sm" disabled={disabled} onClick={onPrint}>
        Print
      </Button>
      <Button
        variant="outline"
        size="sm"
        disabled={disabled || !!saving}
        onClick={() => onSave("pdf")}
      >
        {saving === "pdf" ? "Rendering…" : "Save PDF"}
      </Button>
      <Button
        variant="outline"
        size="sm"
        disabled={disabled || !!saving}
        onClick={() => onSave("png")}
      >
        {saving === "png" ? "Rendering…" : "Save PNG"}
      </Button>
    </div>
  );
}
export function VenueDisplay({ eventId }: { eventId: string }) {
  const [value, setValue] = useState<Venue | null>(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState<"pdf" | "png" | "">("");
  const root = useRef<HTMLDivElement>(null);
  const sheet = useRef<HTMLDivElement>(null);
  useEffect(() => {
    let active = true;
    let pending = false;
    async function load() {
      if (pending) return;
      pending = true;
      try {
        const r = await fetch(eventApi("/api/venue", eventId), {
          cache: "no-store",
          signal: AbortSignal.timeout(10000),
        });
        if (!r.ok)
          throw Error(
            "Venue display unavailable. An online connection is required.",
          );
        const v = await r.json();
        if (active && navigator.onLine) {
          setValue(v);
          setError("");
        }
      } catch (e) {
        if (active) {
          setValue(null);
          setError(String(e));
        }
      } finally {
        pending = false;
      }
    }
    const offline = () => {
      setValue(null);
      setError("Venue display unavailable. An online connection is required.");
    };
    window.addEventListener("offline", offline);
    void load();
    const id = setInterval(load, 10000);
    return () => {
      active = false;
      clearInterval(id);
      window.removeEventListener("offline", offline);
    };
  }, [eventId]);
  const names: Record<string, string> = {};
  const owners: Record<string, string> = {};
  value?.floor_plan?.rows.forEach((r) =>
    r.seats.forEach((s) => {
      if (s.participant_id) names[s.seat_id] = chineseVenueName(s.display_name);
      if (s.participant_id) owners[s.seat_id] = s.participant_id;
    }),
  );
  async function save(format: "pdf" | "png") {
    if (!sheet.current) return;
    setSaving(format);
    try {
      if (format === "pdf")
        await saveVenuePdf(sheet.current, venueFileName(eventId, "pdf"));
      else await saveVenuePng(sheet.current, venueFileName(eventId, "png"));
    } catch {
      setError("Unable to export the seating map. Try again or use Print.");
    } finally {
      setSaving("");
    }
  }
  return (
    <div
      className="venue-page flex h-dvh flex-col bg-background screen:max-[1280px]:[&_.hall-scroll]:overflow-x-auto screen:max-[1280px]:[&_.paper-hall]:min-w-7xl print:block print:h-auto print:bg-white print:text-black"
      ref={root}
    >
      <div className="flex justify-between px-5 py-2 text-sm print:hidden">
        <span>
          PJKIT · Published seating{" "}
          {value?.published_at
            ? `· ${new Date(value.published_at).toLocaleString()}`
            : ""}
        </span>
        <div className="flex gap-2">
          <VenueActions
            disabled={!value?.floor_plan}
            saving={saving}
            onPrint={() => window.print()}
            onSave={(format) => void save(format)}
          />
          <Button
            size="sm"
            onClick={() =>
              root.current
                ?.requestFullscreen()
                .catch(() =>
                  setError("Full screen unavailable in this browser."),
                )
            }
          >
            Full screen
          </Button>
        </div>
      </div>
      {error && (
        <p
          role="alert"
          className="bg-muted px-6 py-2.25 text-sm text-foreground"
        >
          {error}
        </p>
      )}
      {value?.floor_plan ? (
        <div ref={sheet} className="flex min-h-0 flex-1 flex-col">
          <h1 className="my-2 text-center text-[26px] font-semibold print:mb-[5mm] print:mt-0 print:font-[Songti_SC,PMingLiU,serif] print:text-[18pt] print:leading-[1.2]">
            <span className="hidden print:inline">2026年 </span>
            梁皇寶懺大法會功德主排位
          </h1>
          <HallMap
            presentation
            floor={value.floor_plan}
            names={names}
            owners={owners}
            primaryNames={Object.fromEntries(
              Object.entries(value.pair_display ?? {}).map(([id, p]) => [
                id,
                chineseVenueName(p.primary_name) || undefined,
              ]),
            )}
          />
        </div>
      ) : (
        <p className="p-8">
          {error
            ? "請連線以查看已公布的座位表。"
            : value
              ? "No published seating plan yet."
              : "Loading published seating…"}
        </p>
      )}
    </div>
  );
}
