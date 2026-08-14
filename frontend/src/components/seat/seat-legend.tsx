import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { TierName } from "@/lib/allocation-types";

import { TIER_STYLES } from "./seat-theme";

/** Colour key for the seat map. Lives in the sidebar so the map itself
 * stays uncluttered and can use the full viewport width. */
export function SeatLegend() {
  return (
    <div className="flex flex-col gap-2 text-[11px] text-muted-foreground">
      {(Object.keys(TIER_STYLES) as TierName[]).map((tier) => (
        <span key={tier} className="flex items-center gap-2">
          <span
            className={cn(
              "size-3 rounded-sm border",
              TIER_STYLES[tier].cell.split(" hover:")[0],
            )}
          />
          {TIER_STYLES[tier].label}
        </span>
      ))}
      <span className="flex items-center gap-2">
        <span className="size-3 rounded-sm border border-dashed border-muted-foreground/40 bg-muted/30" />
        Empty
      </span>
      <span className="flex items-center gap-2">
        <span className="flex size-3 items-center justify-center rounded-sm border border-destructive/40 bg-destructive/10 text-[8px] text-destructive">
          ✕
        </span>
        Blocked
      </span>
      <Badge variant="outline" className="mt-1 w-fit font-normal">
        ☸ monastic · ★ elderly · ♿ accessible · ↻ moved
      </Badge>
    </div>
  );
}
