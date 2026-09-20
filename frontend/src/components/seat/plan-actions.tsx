"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import type { AllocationResult, Assignment } from "@/lib/allocation-types";
export function PlanActions({
	result,
	assignments,
	dirty,
	onResult,
}: {
	result: AllocationResult;
	assignments: Assignment[];
	dirty: boolean;
	onResult: (r: AllocationResult) => void;
}) {
	const [versions, setVersions] = useState<
		{ id: string; state: string; created: string }[]
	>([]);
	const [busy, setBusy] = useState(false);
	const [message, setMessage] = useState("");
	async function history() {
		setBusy(true);
		try {
			const response = await fetch("/api/plans");
			if (!response.ok) throw new Error("History unavailable");
			const value = await response.json();
			setVersions(value.plans);
		} catch (e) {
			setMessage(String(e));
		} finally {
			setBusy(false);
		}
	}
	async function load(id: string) {
		setBusy(true);
		try {
			const response = await fetch("/api/plans", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ command: "get", plan_version_id: id }),
			});
			const value = await response.json();
			if (!response.ok)
				throw new Error(value.error?.message ?? "Version unavailable");
			onResult(value);
		} catch (e) {
			setMessage(String(e));
		} finally {
			setBusy(false);
		}
	}
	async function action(command: string) {
		setBusy(true);
		setMessage("");
		try {
			const response = await fetch("/api/plans", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					command,
					plan_version_id: result.plan_version_id,
					validation_revision: result.validation_revision,
					...(command === "manual"
						? {
								assignments: assignments.map((a) => ({
									participant_id: a.participant_id,
									seat_ids: a.seat_ids,
								})),
							}
						: {}),
				}),
			});
			const value = await response.json();
			if (!response.ok) {
				const issues = value.error?.details?.issues
					?.map(
						(i: { rule_id: string; message: string }) =>
							`${i.rule_id}: ${i.message}`,
					)
					.join("; ");
				throw new Error(issues ?? value.error?.message ?? "Operation failed");
			}
			onResult(value);
			setMessage(
				command === "manual"
					? "Edits validated and saved as a new draft."
					: `Plan ${value.publication_status.toLowerCase()}.`,
			);
		} catch (e) {
			setMessage(String(e));
		} finally {
			setBusy(false);
		}
	}
	const state = result.publication_status ?? "DRAFT";
	return (
		<section className="space-y-2 border-t pt-3">
			<p className="text-xs">
				Version: {result.plan_version_id?.slice(0, 13)} · {state}
			</p>
			<p className="text-xs">
				Generation: {result.solver_status_at_generation ?? result.solver.status}
				{result.manually_modified ? " · Manually modified" : ""}
			</p>
			<p className="text-xs">
				{result.manually_modified
					? "Validated manual arrangement; optimality is not claimed."
					: result.solver.status === "OPTIMAL"
						? "Configured objective proven optimal within the reported solve scope."
						: "Valid arrangement; the best possible objective has not been proven."}
			</p>
			{result.quality && result.generation_mode === "REPAIR_PUBLISHED" && (
				<p className="text-xs">
					Published comparison: {result.quality.movement.moved_units}{" "}
					registrations moved, {result.quality.movement.unaffected_moved_units}{" "}
					unaffected registrations moved. Distance:{" "}
					{result.quality.movement.distance_doubled / 2} grid steps. Packing
					gaps: {result.quality.local_packing}.
				</p>
			)}
			<details className="text-xs">
				<summary>Proof details</summary>
				<p>
					Scope: {result.solver.optimality_scope}; repair stage:{" "}
					{result.solver.repair_scope ?? "n/a"}. Canonicalization:{" "}
					{result.solver.canonicalization_complete
						? "complete"
						: "not complete"}
					.
				</p>
				{result.solver.proof?.map((p) => (
					<p key={p.stage}>
						{p.stage}: {p.status}, value {p.value ?? "not reached"}, bound{" "}
						{p.best_bound ?? "unknown"}
					</p>
				))}
			</details>
			<Button
				variant="outline"
				size="sm"
				disabled={busy || dirty}
				onClick={history}
			>
				View version history
			</Button>
			{versions.length > 0 && (
				<select
					aria-label="Plan version history"
					className="w-full rounded border bg-background p-1 text-xs"
					value={result.plan_version_id ?? ""}
					disabled={busy || dirty}
					onChange={(e) => load(e.target.value)}
				>
					{versions.map((v) => (
						<option key={v.id} value={v.id}>
							{v.created} · {v.state} · {v.id.slice(0, 13)}
						</option>
					))}
				</select>
			)}
			<div className="flex flex-wrap gap-2">
				<Button
					size="sm"
					disabled={
						busy ||
						!dirty ||
						!["DRAFT", "UNDER_REVIEW", "APPROVED"].includes(state)
					}
					onClick={() => action("manual")}
				>
					Validate & save edits
				</Button>
				{state === "DRAFT" && (
					<Button
						size="sm"
						disabled={busy || dirty}
						onClick={() => action("submit")}
					>
						Submit for review
					</Button>
				)}
				{state === "UNDER_REVIEW" && (
					<Button
						size="sm"
						disabled={busy || dirty}
						onClick={() => action("approve")}
					>
						Approve revision
					</Button>
				)}
				{state === "APPROVED" && (
					<Button
						size="sm"
						disabled={busy || dirty}
						onClick={() => action("publish")}
					>
						Publish approved revision
					</Button>
				)}
				{["DRAFT", "UNDER_REVIEW", "APPROVED"].includes(state) && (
					<Button
						variant="outline"
						size="sm"
						disabled={busy}
						onClick={() => action("reject")}
					>
						Reject
					</Button>
				)}
				{state === "PUBLISHED" && (
					<Button variant="outline" size="sm" onClick={() => window.print()}>
						Print published map
					</Button>
				)}
			</div>
			{message && (
				<p role="status" className="text-xs">
					{message}
				</p>
			)}
			{dirty && (
				<p className="text-xs text-muted-foreground">
					Unsaved edits are not validated and cannot be published.
				</p>
			)}
		</section>
	);
}
