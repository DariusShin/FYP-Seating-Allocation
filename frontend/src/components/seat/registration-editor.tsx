"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import type { AllocationResult, Registration } from "@/lib/allocation-types";
const STATUSES = [
	"CONFIRMED",
	"REPLACEMENT_CONFIRMED",
	"PENDING",
	"WAITLISTED",
	"CANCELLED",
	"ABSENT",
	"REPLACED",
];
/** Changes are submitted as event data for a new draft, never written into a published snapshot. */
export function RegistrationEditor({
	result,
	onResult,
}: {
	result: AllocationResult;
	onResult: (r: AllocationResult) => void;
}) {
	const [items, setItems] = useState<Registration[]>(
		() => result.source_request?.participants ?? [],
	);
	const [mode, setMode] = useState("REPAIR_PUBLISHED");
	const [busy, setBusy] = useState(false);
	const [message, setMessage] = useState("");
	function patch(index: number, values: Partial<Registration>) {
		setItems((old) =>
			old.map((p, i) => (i === index ? { ...p, ...values } : p)),
		);
	}
	async function generate() {
		setBusy(true);
		setMessage("");
		try {
			const response = await fetch("/api/solve", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					generation_mode: mode,
					preference_profile_version: "ranked-v1",
					preferences: result.preferences,
					participants: items,
				}),
			});
			const next = await response.json();
			if (!response.ok)
				throw new Error(next.error?.message ?? "Generation failed");
			onResult(next);
		} catch (e) {
			setMessage(String(e));
		} finally {
			setBusy(false);
		}
	}
	return (
		<details className="border-t pt-3">
			<summary className="cursor-pointer text-xs font-medium">
				Registration changes / absence / replacement
			</summary>
			<p className="my-2 text-xs text-muted-foreground">
				Published assignments stay active until a new version is approved. A
				replacement must reference an original marked REPLACED.
			</p>
			<div className="max-h-80 space-y-2 overflow-auto">
				{items.map((p, index) => (
					<fieldset
						className="space-y-1 rounded border p-2 text-xs"
						key={p.participant_id}
					>
						<legend>{p.participant_id}</legend>
						<input
							aria-label={`Name ${p.participant_id}`}
							className="w-full rounded border bg-background p-1"
							value={p.full_name}
							onChange={(e) => patch(index, { full_name: e.target.value })}
						/>
						<select
							aria-label={`Status ${p.participant_id}`}
							className="w-full rounded border bg-background p-1"
							value={p.registration_status}
							onChange={(e) =>
								patch(index, { registration_status: e.target.value })
							}
						>
							{STATUSES.map((s) => (
								<option key={s}>{s}</option>
							))}
						</select>
						<select
							aria-label={`Tier ${p.participant_id}`}
							value={p.contribution_tier}
							onChange={(e) =>
								patch(index, {
									contribution_tier: e.target
										.value as Registration["contribution_tier"],
								})
							}
						>
							<option>EMPEROR</option>
							<option>MERIT</option>
							<option>BODHI</option>
						</select>
						<label>
							{" "}
							Contribution RM
							<input
								type="number"
								min="0"
								className="w-24 rounded border bg-background p-1"
								value={p.contribution_amount_rm}
								onChange={(e) =>
									patch(index, {
										contribution_amount_rm: Number(e.target.value),
									})
								}
							/>
						</label>
						<label className="block">
							<input
								type="checkbox"
								checked={p.requires_accessible_seat}
								onChange={(e) =>
									patch(index, { requires_accessible_seat: e.target.checked })
								}
							/>{" "}
							Requires accessible seat
						</label>
						{p.registration_status === "REPLACEMENT_CONFIRMED" && (
							<input
								aria-label={`Replaces ${p.participant_id}`}
								placeholder="Original participant ID"
								value={p.replacement_for_participant_id ?? ""}
								onChange={(e) =>
									patch(index, {
										replacement_for_participant_id: e.target.value || null,
									})
								}
							/>
						)}
					</fieldset>
				))}
			</div>
			<Button
				variant="outline"
				size="sm"
				className="my-2"
				onClick={() =>
					setItems((old) => [
						...old,
						{
							participant_id: `P-${crypto.randomUUID().slice(0, 8)}`,
							full_name: "New registration",
							registration_status: "CONFIRMED",
							replacement_for_participant_id: null,
							contribution_tier: "BODHI",
							contribution_amount_rm: 2000,
							requires_accessible_seat: false,
							participant_category: "GENERAL_DEVOTEE",
							events_joined_last_2_years: 0,
							age: 30,
							adjacent_person_name: null,
						},
					])
				}
			>
				Add registration
			</Button>
			<select
				className="my-2 w-full rounded border bg-background p-1 text-xs"
				value={mode}
				onChange={(e) => setMode(e.target.value)}
			>
				<option value="REPAIR_PUBLISHED">Repair published plan</option>
				<option value="REGENERATE_DRAFT">Regenerate unpublished draft</option>
				<option value="FULL_REGENERATION">Explicit full regeneration</option>
			</select>
			<Button size="sm" disabled={busy} onClick={generate}>
				{busy ? "Solving…" : "Generate with changes"}
			</Button>
			{message && (
				<p role="alert" className="text-xs text-destructive">
					{message}
				</p>
			)}
		</details>
	);
}
