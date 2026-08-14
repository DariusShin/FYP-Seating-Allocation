"use client";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import type { AllocationResult, TierName } from "@/lib/allocation-types";

import { COMPONENT_LABELS, formatNumber, TIER_STYLES } from "./seat-theme";

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-2">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-xs font-medium tabular-nums">{value}</span>
    </div>
  );
}

export function StatsSidebar({ result }: { result: AllocationResult }) {
  const summary = result.input_summary;
  const solver = result.solver;
  const weighted = result.penalty_summary.weighted;
  const tierCounts: Record<TierName, { registrations: number; seats: number }> = {
    EMPEROR: { registrations: summary.emperor_count, seats: summary.emperor_count * 2 },
    BODHI: { registrations: summary.bodhi_count, seats: summary.bodhi_count },
    MERIT: { registrations: summary.merit_count, seats: summary.merit_count },
  };
  const penaltyComponents = [
    {
      key: "priority_seat",
      label: COMPONENT_LABELS.priority_seat,
      value: weighted.priority_seat,
    },
    {
      key: "category_zone",
      label: COMPONENT_LABELS.category_zone,
      value: weighted.category_zone,
    },
    { key: "movement", label: COMPONENT_LABELS.movement, value: weighted.movement },
    {
      key: "activeness",
      label: COMPONENT_LABELS.activeness,
      value: weighted.activeness,
    },
  ];
  const maxComponent = Math.max(1, ...penaltyComponents.map((c) => c.value));
  const kept = result.assignments.filter((a) => a.moved === false).length;
  const movedCount = result.assignments.filter((a) => a.moved === true).length;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Distribution</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {(Object.keys(tierCounts) as TierName[]).map((tier) => (
            <div key={tier} className="flex items-center gap-2 text-xs">
              <span className={cn("size-2.5 shrink-0 rounded-full", TIER_STYLES[tier].dot)} />
              <span className="w-20 shrink-0">{TIER_STYLES[tier].label}</span>
              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                <div
                  className={cn("h-full", TIER_STYLES[tier].bar)}
                  style={{
                    width: `${(tierCounts[tier].seats / summary.total_seat_count) * 100}%`,
                  }}
                />
              </div>
              <span className="w-20 shrink-0 text-right tabular-nums text-muted-foreground">
                {tierCounts[tier].registrations} · {tierCounts[tier].seats} seats
              </span>
            </div>
          ))}
          <Separator />
          <Stat
            label="Occupied seats"
            value={`${summary.required_seat_count} / ${summary.total_seat_count}`}
          />
          <Stat label="Empty seats" value={String(summary.empty_seat_count)} />
          <Stat
            label="Kept previous seat"
            value={`${kept} kept · ${movedCount} moved`}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm">Solver</CardTitle>
            <Badge className="bg-emerald-600 text-white hover:bg-emerald-600 dark:bg-emerald-500">
              {solver.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-1.5">
          <Stat label="Engine" value={solver.engine.replace("Google ", "")} />
          <Stat label="Weighted penalty" value={formatNumber(solver.main_penalty)} />
          <Stat label="Objective (scaled)" value={formatNumber(solver.objective_value)} />
          <Stat label="Optimality gap" value={String(solver.optimality_gap)} />
          <Stat
            label="Wall time"
            value={`${solver.wall_time_seconds.toFixed(3)} s`}
          />
          <Stat label="Conflicts / branches" value={`${formatNumber(solver.num_conflicts)} / ${formatNumber(solver.num_branches)}`} />
          <Stat
            label="Bool vars / constraints"
            value={`${formatNumber(solver.num_boolean_variables)} / ${formatNumber(solver.num_constraints)}`}
          />
          <Stat
            label="All hard constraints"
            value={
              result.hard_constraint_validation.all_constraints_satisfied
                ? "✓ satisfied"
                : "✗ violated"
            }
          />
          <Stat
            label="Front-fill rows (HC13)"
            value={result.constraint_config.enforce_front_fill ? "enforced" : "off"}
          />
          <Stat
            label="Middle-out fill (HC14)"
            value={result.constraint_config.enforce_middle_fill ? "enforced" : "off"}
          />
          <Stat
            label="Penalty normalization"
            value={
              result.constraint_config.normalize_penalties
                ? `on (0–${result.constraint_config.normalization_scale})`
                : "off"
            }
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Penalty breakdown (weighted)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2.5">
          {penaltyComponents.map((component) => (
            <div key={component.key} className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">{component.label}</span>
                <span className="font-medium tabular-nums">
                  {formatNumber(component.value)}
                </span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-primary/70"
                  style={{ width: `${(component.value / maxComponent) * 100}%` }}
                />
              </div>
            </div>
          ))}
          <Separator />
          <Stat label="Tie-break" value={formatNumber(weighted.tie_break)} />
          <Stat label="Weighted total" value={formatNumber(weighted.total)} />
          <div className="flex flex-wrap gap-1 pt-1">
            <Badge variant="secondary" className="font-normal">
              priority ×{result.weights.priority_seat_weight}
            </Badge>
            <Badge variant="secondary" className="font-normal">
              zone ×{result.weights.category_zone_weight}
            </Badge>
            <Badge variant="secondary" className="font-normal">
              move ×{result.weights.movement_weight}
            </Badge>
            <Badge variant="secondary" className="font-normal">
              active ×{result.weights.activeness_weight}
            </Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
