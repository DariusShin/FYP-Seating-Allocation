"use client";

import { useState } from "react";
import { Loader2, RotateCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import type { AllocationResult, SolverWeights } from "@/lib/allocation-types";

const WEIGHT_KEYS = [
  "priority_seat_weight",
  "category_zone_weight",
  "movement_weight",
  "activeness_weight",
] as const;

type WeightKey = (typeof WEIGHT_KEYS)[number];

const WEIGHT_FIELDS: {
  key: WeightKey;
  label: string;
  hint: string;
}[] = [
  {
    key: "priority_seat_weight",
    label: "Care & accessibility",
    hint: "Give monks, elderly guests, and wheelchair users the seats nearest the altar.",
  },
  {
    key: "category_zone_weight",
    label: "Right area for each group",
    hint: "Keep monastics, committee members, volunteers, and devotees in their usual part of the hall.",
  },
  {
    key: "movement_weight",
    label: "Keep current seats",
    hint: "Avoid moving people away from the seats they already have.",
  },
  {
    key: "activeness_weight",
    label: "Reward active members",
    hint: "Give people who joined more events recently a better seat.",
  },
];

/**
 * Return integer percentages summing exactly to `total`, distributed in
 * proportion to `shares` (largest-remainder rounding; equal split when all
 * shares are zero).
 */
function apportion(shares: number[], total: number): number[] {
  const shareSum = shares.reduce((sum, share) => sum + share, 0);
  const exact = shares.map((share) =>
    shareSum === 0 ? total / shares.length : (share / shareSum) * total,
  );
  const floors = exact.map(Math.floor);
  let leftover = total - floors.reduce((sum, value) => sum + value, 0);
  const order = exact
    .map((value, index) => ({ index, fraction: value - Math.floor(value) }))
    .sort((a, b) => b.fraction - a.fraction || a.index - b.index);
  for (const { index } of order) {
    if (leftover <= 0) break;
    floors[index] += 1;
    leftover -= 1;
  }
  return floors;
}

/** Scale an arbitrary weight set so the four values sum to exactly 100. */
function normalizeTo100(weights: SolverWeights): SolverWeights {
  const values = apportion(
    WEIGHT_KEYS.map((key) => Math.max(0, weights[key])),
    100,
  );
  const next = { ...weights };
  WEIGHT_KEYS.forEach((key, index) => {
    next[key] = values[index];
  });
  return next;
}

/**
 * Set one weight and rebalance the other three proportionally so the total
 * stays exactly 100%.
 */
function rebalance(
  current: SolverWeights,
  changedKey: WeightKey,
  rawValue: number,
): SolverWeights {
  const value = Math.min(100, Math.max(0, Math.round(rawValue)));
  const otherKeys = WEIGHT_KEYS.filter((key) => key !== changedKey);
  const otherValues = apportion(
    otherKeys.map((key) => current[key]),
    100 - value,
  );
  const next = { ...current, [changedKey]: value };
  otherKeys.forEach((key, index) => {
    next[key] = otherValues[index];
  });
  return next;
}

export function WeightControls({
  result,
  onResult,
}: {
  result: AllocationResult;
  onResult: (next: AllocationResult) => void;
}) {
  const [weights, setWeights] = useState<SolverWeights>(() =>
    normalizeTo100(result.weights),
  );
  const [solving, setSolving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRun, setLastRun] = useState<{ moved: number; kept: number } | null>(
    null,
  );

  async function regenerate() {
    setSolving(true);
    setError(null);
    try {
      const response = await fetch("/api/solve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          weights,
          previous_allocation: result.assignments.map((assignment) => ({
            participant_id: assignment.participant_id,
            seat_ids: assignment.seat_ids,
          })),
        }),
      });
      const payload = await response.json();
      if (!response.ok || payload.status !== "success") {
        const message =
          payload?.error?.message ?? payload?.error ?? "solver request failed";
        setError(`${payload?.error?.code ?? "ERROR"}: ${message}`);
        return;
      }
      const next = payload as AllocationResult;
      setLastRun({
        moved: next.assignments.filter((a) => a.moved === true).length,
        kept: next.assignments.filter((a) => a.moved === false).length,
      });
      onResult(next);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setSolving(false);
    }
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm">Seating priorities</CardTitle>
        <CardDescription className="text-xs">
          Decide what matters most when seats are assigned. The four priorities
          always share 100% — raising one automatically lowers the others.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {WEIGHT_FIELDS.map((field) => (
          <div key={field.key} className="space-y-1.5">
            <div className="flex items-baseline justify-between">
              <Label htmlFor={field.key} className="text-xs">
                {field.label}
              </Label>
              <span className="text-xs font-semibold tabular-nums">
                {weights[field.key]}%
              </span>
            </div>
            <Slider
              id={field.key}
              min={0}
              max={100}
              step={1}
              value={[weights[field.key]]}
              disabled={solving}
              onValueChange={([value]) =>
                setWeights((current) => rebalance(current, field.key, value))
              }
            />
            <p className="text-[10px] leading-tight text-muted-foreground">
              {field.hint}
            </p>
          </div>
        ))}

        <div className="flex items-baseline justify-between border-t pt-2 text-xs">
          <span className="text-muted-foreground">Total</span>
          <span className="font-semibold tabular-nums">100%</span>
        </div>

        <Button className="w-full" onClick={regenerate} disabled={solving}>
          {solving ? (
            <>
              <Loader2 className="animate-spin" />
              Recalculating seats…
            </>
          ) : (
            <>
              <RotateCcw />
              Regenerate seating plan
            </>
          )}
        </Button>

        {solving && (
          <p className="text-center text-[11px] text-muted-foreground">
            Finding the best possible plan can take up to ~30 seconds.
          </p>
        )}
        {error && (
          <p className="rounded-md border border-destructive/40 bg-destructive/10 p-2 text-[11px] text-destructive">
            {error}
          </p>
        )}
        {lastRun && !solving && !error && (
          <p className="rounded-md border border-emerald-600/40 bg-emerald-500/10 p-2 text-[11px] text-emerald-700 dark:text-emerald-300">
            Best possible plan found: {lastRun.kept} participants kept their
            seats, {lastRun.moved} moved.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
