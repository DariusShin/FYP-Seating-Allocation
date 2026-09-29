"use client";

import { useId, useState } from "react";
import { Check, ChevronsUpDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import type { Assignment } from "@/lib/allocation-types";
import { TIER_STYLES } from "./seat-theme";
import { cn } from "@/lib/utils";

export function ParticipantPicker({
  participants,
  value,
  onChange,
  id,
  placeholder = "Select a participant…",
}: {
  participants: Assignment[];
  value: string | null;
  onChange: (id: string) => void;
  id?: string;
  placeholder?: string;
}) {
  const [open, setOpen] = useState(false);
  const listId = useId();
  const selected = participants.find((p) => p.participant_id === value);
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          id={id}
          variant="outline"
          role="combobox"
          aria-expanded={open}
          aria-controls={listId}
          className="w-full justify-between"
        >
          <span className="truncate">{selected?.full_name ?? placeholder}</span>
          <ChevronsUpDown data-icon="inline-end" />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        className="w-(--radix-popover-trigger-width) p-0"
        align="start"
      >
        <Command>
          <CommandInput
            placeholder="Search name, guest, ID or tier…"
            aria-label="Search participants"
          />
          <CommandList id={listId}>
            <CommandEmpty>
              No participants found. Try another name or ID.
            </CommandEmpty>
            <CommandGroup heading={`${participants.length} registrations`}>
              {participants.map((p) => (
                <CommandItem
                  key={p.participant_id}
                  value={p.participant_id}
                  keywords={[
                    p.full_name,
                    p.contribution_tier,
                    ...p.seats.map((s) => s.display_name),
                  ]}
                  onSelect={() => {
                    onChange(p.participant_id);
                    setOpen(false);
                  }}
                >
                  <span
                    className={cn(
                      "size-2 shrink-0 rounded-full",
                      TIER_STYLES[p.contribution_tier].dot,
                    )}
                  />
                  <span className="flex min-w-0 flex-1 flex-col gap-0.5">
                    <span className="truncate">{p.full_name}</span>
                    <span className="text-xs text-muted-foreground">
                      {p.participant_id} ·{" "}
                      {p.seat_ids.length
                        ? p.seat_ids.join(" + ")
                        : "Unassigned"}
                    </span>
                  </span>
                  {value === p.participant_id && <Check />}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
