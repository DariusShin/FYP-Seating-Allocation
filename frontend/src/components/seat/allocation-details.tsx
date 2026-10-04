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
    <div className="space-y-3">
      <h2 className="mb-0.5 text-2xl font-medium">{item.display_names[0]}</h2>
      <p className="my-1.75 mb-3 text-[13px] leading-[1.65] text-muted-foreground">
        Registered: {person.full_name} · {person.contribution_tier}
      </p>
      <p className="my-1.75 mb-3 text-[13px] leading-[1.65] text-muted-foreground">
        {location}
      </p>
      <fieldset className="grid gap-4" disabled={!draft || busy}>
        <legend className="sr-only">Display details</legend>
        <label className="grid gap-1 text-sm">
          Display name · payer
          <input
            className="mt-1 w-full rounded-md border border-input bg-background px-2 py-1.5 text-[15px] text-foreground disabled:bg-muted disabled:text-muted-foreground"
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
            className="mt-1 w-full rounded-md border border-input bg-background px-2 py-1.5 text-[15px] text-foreground disabled:bg-muted disabled:text-muted-foreground"
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
