"use client";
import { useState } from "react";
import { ArrowUp, ArrowDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import type {
	AllocationResult,
	Preference,
} from "@/lib/allocation-types";
const LABELS = {
	contribution_seat: "Give higher contributors more desirable seats",
	activeness: "Favour participants who attend more PJKIT events",
	category_zone: "Match seats to participant categories",
};
const DEFAULTS: Preference[] = [
	{ key: "contribution_seat", enabled: true },
	{ key: "activeness", enabled: true },
	{ key: "category_zone", enabled: true },
];
export function WeightControls({
	result,
	onGenerate,
	hasDraft = false,
}: {
	result: AllocationResult;
	onGenerate: (request: { generation_mode: string; preferences: Preference[] }) => void;
	hasDraft?: boolean;
}) {
	const [preferences, setPreferences] = useState<Preference[]>(
		() => result.preferences ?? DEFAULTS,
	);
	const [mode, setMode] = useState("REGENERATE_DRAFT");
	function move(index: number, delta: number) {
		setPreferences((current) => {
			const next = [...current];
			[next[index], next[index + delta]] = [next[index + delta], next[index]];
			return next;
		});
	}
	let rank = 0;
	return (
		<section className="space-y-4">
			<h2 className="text-sm font-semibold">Seating preferences</h2>
			<p className="text-xs text-muted-foreground">
				Higher preferences receive more emphasis during optimization. Compulsory
				seating rules always apply.
			</p>
			<ol className="space-y-3">
				{preferences.map((item, index) => (
					<li key={item.key} className="rounded-md border p-2">
						<div className="flex items-start gap-2">
							<span className="text-xs">
								{item.enabled ? `${++rank}.` : "Off"}
							</span>
							<label htmlFor={`pref-${item.key}`} className="flex-1 text-xs">
								{LABELS[item.key]}
							</label>
							<Switch
								id={`pref-${item.key}`}
								checked={item.enabled}
								onCheckedChange={(enabled) =>
									setPreferences((current) =>
										current.map((p) =>
											p.key === item.key ? { ...p, enabled } : p,
										),
									)
								}
							/>
						</div>
						<div className="mt-2 flex gap-2">
							<Button
								type="button"
								variant="outline"
								size="sm"
								aria-label={`Move ${LABELS[item.key]} up`}
								disabled={index === 0}
								onClick={() => move(index, -1)}
							>
								<ArrowUp className="size-3" />
							</Button>
							<Button
								type="button"
								variant="outline"
								size="sm"
								aria-label={`Move ${LABELS[item.key]} down`}
								disabled={index === preferences.length - 1}
								onClick={() => move(index, 1)}
							>
								<ArrowDown className="size-3" />
							</Button>
						</div>
					</li>
				))}
			</ol>
			<label className="block text-xs">
				Operation
				<select
					className="mt-1 w-full rounded border bg-background p-2"
					value={mode}
					onChange={(e) => setMode(e.target.value)}
				>
					<option value="REGENERATE_DRAFT">Regenerate draft</option>
					<option value="REPAIR_PUBLISHED">Repair published plan</option>
					<option value="FULL_REGENERATION">Full regeneration</option>
				</select>
			</label>
			{mode === "REPAIR_PUBLISHED" && (
				<p className="rounded border p-2 text-xs">
					System-controlled: preserve published assignments first, then minimize
					movement distance. The published plan is the baseline.
				</p>
			)}
			{hasDraft && (
				<p className="text-xs text-amber-700">
					Generation opens a new draft. Save your current edits first to retain
					them in this version.
				</p>
			)}
			<Button onClick={() => onGenerate({ generation_mode: mode, preferences })} className="w-full">
                {mode === "REPAIR_PUBLISHED" ? "Repair into new draft" : "Generate new draft"}
            </Button>
			<p className="text-xs text-muted-foreground">
				Generating does not publish. Review and approve the resulting version
				separately.
			</p>
		</section>
	);
}
