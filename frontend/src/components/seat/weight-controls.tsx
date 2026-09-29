"use client";
import { useRef, useState } from "react";
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
	onResult,
    onSolvingChange,
	hasDraft = false,
}: {
	result: AllocationResult;
	onResult: (result: AllocationResult) => Promise<void>;
    onSolvingChange: (busy: boolean) => void;
	hasDraft?: boolean;
}) {
	const [preferences, setPreferences] = useState<Preference[]>(
		() => result.preferences ?? DEFAULTS,
	);
    const inFlight = useRef(false);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    const [generated, setGenerated] = useState<AllocationResult | null>(null);
    const changed = JSON.stringify(preferences) !== JSON.stringify(result.preferences ?? DEFAULTS);
    async function generate() {
        if (inFlight.current || busy || !changed) return;
        inFlight.current = true;
        setBusy(true); onSolvingChange(true); setError("");
        try {
            let next = generated;
            if (!next) {
                const response = await fetch("/api/solve", {
                    method: "POST", headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ generation_mode: "REGENERATE_DRAFT", preference_profile_version: "ranked-v1", preferences }),
                });
                next = await response.json();
                if (!response.ok || next?.status !== "success") throw new Error("Unable to generate the draft. Please try again.");
                setGenerated(next);
            }
            await onResult(next);
        } catch (e) { setError(e instanceof Error ? e.message : "Generation failed"); }
        finally { inFlight.current = false; setBusy(false); onSolvingChange(false); }
    }
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
            <fieldset className="space-y-4" disabled={busy || !!generated}>
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
			{hasDraft && (
				<p className="text-xs text-amber-700">
					Generation opens a new draft. Save your current edits first to retain
					them in this version.
				</p>
			)}
            </fieldset>
            <Button disabled={busy || !changed} onClick={() => void generate()} className="w-full">
                {busy ? "Preparing draft…" : generated ? "Retry opening draft" : "Generate new draft"}
            </Button>
            {error && <p role="alert" className="text-xs text-destructive">{error}</p>}
			<p className="text-xs text-muted-foreground">
				Generating does not publish. Review and publish the resulting version
				separately.
			</p>
		</section>
	);
}
