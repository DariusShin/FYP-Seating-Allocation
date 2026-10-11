"use client";

import { useState } from "react";
import { Pencil } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import type { Registration, WorkingItem, DetailChanges } from "./types";

/** Registration facts stay read-only; display details are drafted locally until Save succeeds. */
export function AllocationDetails({
  person,
  item,
  location,
  busy,
  canEdit,
  onSave,
  onSeatPrepared,
  onSetAttendance,
}: {
  person: Registration;
  item: WorkingItem;
  location: string;
  busy: boolean;
  canEdit: boolean;
  onSave: (details: DetailChanges) => Promise<boolean>;
  onSeatPrepared: (prepared: boolean) => void;
  onSetAttendance: (status: "PRESENT" | "ABSENT") => void;
}) {
  const [draft, setDraft] = useState<{ name: string; note: string } | null>(
    null,
  );
  const changed =
    !!draft &&
    (draft.name !== item.display_names[0] || draft.note !== item.note);
  const absent = item.attendance_status === "ABSENT";
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
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h2 className="text-2xl font-medium leading-tight">
            {person.full_name}
          </h2>
          <p className="text-[13px] text-muted-foreground">{location}</p>
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          <Badge variant="secondary">{person.contribution_tier}</Badge>
          <Badge
            variant={absent ? "destructive" : "outline"}
            className={absent ? "" : "border-emerald-600 text-emerald-700"}
          >
            {absent ? "Absent" : "Present"}
          </Badge>
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label="Edit display details"
            disabled={busy || !canEdit}
            onClick={() =>
              setDraft((current) =>
                current
                  ? null
                  : { name: item.display_names[0], note: item.note },
              )
            }
          >
            <Pencil />
          </Button>
        </div>
      </div>
      <section aria-label="Participant details" className="rounded-lg border p-3">
        <h3 className="text-[15px] font-medium">Participant details</h3>
        <dl className="mt-2 grid gap-2.5 text-sm">
          <div className="grid gap-1">
            <dt className="text-[13px] text-muted-foreground">
              Display name · payer
            </dt>
            <dd>
              {draft ? (
                <Input
                  aria-label="Display name"
                  maxLength={80}
                  value={draft.name}
                  disabled={busy}
                  onChange={(e) =>
                    setDraft(
                      (current) =>
                        current && { ...current, name: e.target.value },
                    )
                  }
                />
              ) : (
                item.display_names[0]
              )}
            </dd>
          </div>
          <div className="grid gap-1 sm:grid-cols-2 sm:gap-3">
            <div className="grid gap-1">
              <dt className="text-[13px] text-muted-foreground">
                Contribution tier
              </dt>
              <dd>{person.contribution_tier}</dd>
            </div>
            <div className="grid gap-1">
              <dt className="text-[13px] text-muted-foreground">
                Contribution amount
              </dt>
              <dd>
                RM {person.contribution_amount_rm.toLocaleString()}
              </dd>
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="grid gap-1">
              <dt className="text-[13px] text-muted-foreground">Attendance</dt>
              <dd>
                <Select
                  value={absent ? "ABSENT" : "PRESENT"}
                  disabled={busy || !canEdit}
                  onValueChange={(value) =>
                    onSetAttendance(value as "PRESENT" | "ABSENT")
                  }
                >
                  <SelectTrigger aria-label="Participant attendance">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="PRESENT">Present</SelectItem>
                    <SelectItem value="ABSENT">Absent</SelectItem>
                  </SelectContent>
                </Select>
              </dd>
            </div>
            <div className="flex items-end gap-2 pb-0.5">
              <Switch
                id="seat-prepared"
                checked={!!item.seat_prepared}
                disabled={busy || !canEdit}
                onCheckedChange={onSeatPrepared}
              />
              <Label htmlFor="seat-prepared">Seat prepared</Label>
            </div>
          </div>
        </dl>
        <div className="mt-2.5 grid gap-1">
          {draft ? (
            <Textarea
              aria-label="Staff note"
              maxLength={2000}
              rows={2}
              value={draft.note}
              disabled={busy}
              onChange={(e) =>
                setDraft(
                  (current) => current && { ...current, note: e.target.value },
                )
              }
            />
          ) : (
            <>
              <p className="text-[13px] text-muted-foreground">Staff note</p>
              <p className="text-sm">{item.note || "—"}</p>
            </>
          )}
        </div>
        {draft && (
          <div className="mt-3 flex gap-2">
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
          </div>
        )}
      </section>
    </div>
  );
}
