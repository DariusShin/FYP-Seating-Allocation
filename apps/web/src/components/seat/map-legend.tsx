import { Accessibility, Star, StickyNote } from "lucide-react";
import { TIER_STYLES } from "./seat-theme";
export function MapLegend() {
  return (
    <div className="space-y-5">
      <div className="grid gap-3 sm:grid-cols-2">
        {(
          [
            ["EMPEROR", "Emperor · Pair registration"],
            ["MERIT", "Merit · Individual registration"],
            ["BODHI", "Bodhi · Individual registration"],
          ] as const
        ).map(([tier, label]) => (
          <div
            key={tier}
            className="flex min-w-0 items-center gap-2.25 text-[13px] leading-[1.4]"
          >
            <span
              className={`inline-flex size-5.5 shrink-0 items-center justify-center rounded-md border border-border ${TIER_STYLES[tier].cell.split(" hover:")[0]}`}
            />
            <span>{label}</span>
          </div>
        ))}
        <div className="flex min-w-0 items-center gap-2.25 text-[13px] leading-[1.4]">
          <span className="inline-flex size-5.5 shrink-0 items-center justify-center rounded-md border border-dashed border-border bg-background" />{" "}
          Empty seat · available
        </div>
        <div className="flex min-w-0 items-center gap-2.25 text-[13px] leading-[1.4]">
          <span className="inline-flex size-5.5 shrink-0 items-center justify-center rounded-md border border-[color-mix(in_oklab,var(--destructive)_35%,var(--border))] bg-[repeating-linear-gradient(135deg,transparent,transparent_4px,var(--muted)_4px,var(--muted)_6px)] text-destructive">
            ×
          </span>{" "}
          Building structure · unavailable
        </div>
      </div>
      <section>
        <h3 className="mb-2.25 text-[13px] font-semibold">
          Participant indicators
        </h3>
        <div className="grid gap-2 sm:grid-cols-2">
          <div className="flex min-w-0 items-center gap-2.25 text-[13px] leading-[1.4]">
            <span className="inline-flex size-6.5 shrink-0 items-center justify-center rounded-[7px] border border-border bg-muted text-foreground [&>svg]:size-3.75 [&>svg]:stroke-[2.2]">
              <Accessibility />
            </span>{" "}
            Accessible seating required
          </div>
          <div className="flex min-w-0 items-center gap-2.25 text-[13px] leading-[1.4]">
            <span className="inline-flex size-6.5 shrink-0 items-center justify-center rounded-[7px] border border-border bg-muted text-foreground [&>svg]:size-3.75 [&>svg]:stroke-[2.2]">
              <Star />
            </span>{" "}
            Elderly participant
          </div>
          <div className="flex min-w-0 items-center gap-2.25 text-[13px] leading-[1.4]">
            <span className="inline-flex size-6.5 shrink-0 items-center justify-center rounded-[7px] border border-border bg-muted text-foreground [&>svg]:size-3.75 [&>svg]:stroke-[2.2]">
              <StickyNote />
            </span>{" "}
            Staff note recorded
          </div>
        </div>
      </section>
    </div>
  );
}
