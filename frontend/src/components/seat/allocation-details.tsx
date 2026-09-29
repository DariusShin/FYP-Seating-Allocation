"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import type { Registration } from "@/lib/allocation-types";
import type { WorkingItem } from "@/lib/workspace";

/** Details stay local until Save succeeds; Cancel never mutates the workspace. */
export function AllocationDetails({
	person,
	item,
	location,
	busy,
	onSave,
	onClose,
}: {
	person: Registration;
	item: WorkingItem;
	location: string;
	busy: boolean;
	onSave: (
		details: Pick<WorkingItem, "display_names" | "note">,
	) => Promise<boolean>;
	onClose: () => void;
}) {
	const [draft, setDraft] = useState<{ name: string; note: string } | null>(
		null,
	);
	const changed =
		!!draft &&
		(draft.name !== item.display_names[0] || draft.note !== item.note);
	async function save() {
		if (!draft || busy || !changed || !draft.name.trim()) return;
		if (
			await onSave({
				display_names: item.display_names.map(() => draft.name.trim()),
				note: draft.note,
			})
		)
			setDraft(null);
	}
	return (
		<div className="allocation-details space-y-3">
			<h2>{item.display_names[0]}</h2>
			<p className="muted-copy">
				Registered: {person.full_name} · {person.contribution_tier}
			</p>
			<p className="muted-copy">{location}</p>
			<fieldset className="grid gap-4" disabled={!draft || busy}>
				<legend className="sr-only">Display details</legend>
				<label className="grid gap-1 text-sm">
					Display name · payer
					<input
						className="rounded-md border bg-muted/30 p-2 disabled:text-muted-foreground"
						maxLength={80}
						value={draft?.name ?? item.display_names[0]}
						onChange={(e) =>
							setDraft(
								(current) => current && { ...current, name: e.target.value },
							)
						}
					/>
				</label>
				<label className="grid gap-1 text-sm">
					Staff note
					<textarea
						className="rounded-md border bg-muted/30 p-2 disabled:text-muted-foreground"
						maxLength={2000}
						rows={2}
						value={draft?.note ?? item.note}
						onChange={(e) =>
							setDraft(
								(current) => current && { ...current, note: e.target.value },
							)
						}
					/>
				</label>
			</fieldset>
			<div className="mt-4 flex gap-2">
				{draft ? (
					<>
						<Button
							disabled={busy || !changed || !draft.name.trim()}
							onClick={() => void save()}
						>
							Save draft
						</Button>
						<Button
							variant="outline"
							disabled={busy}
							onClick={() => setDraft(null)}
						>
							Cancel
						</Button>
					</>
				) : (
					<>
						<Button
							disabled={busy}
							onClick={() =>
								setDraft({ name: item.display_names[0], note: item.note })
							}
						>
							Edit
						</Button>
						<Button variant="outline" disabled={busy} onClick={onClose}>
							Done
						</Button>
					</>
				)}
			</div>
		</div>
	);
}
