import type { WorkingState } from "./workspace";
import type { TierName } from "./allocation-types";
export interface ReviewParticipant {
	participant_id: string;
	display_name: string;
	contribution_tier: TierName;
	contribution_amount_rm: number;
	seat_ids: string[];
	row_number: number;
}
export interface Finding {
	finding_id: string;
	rule_id: "C12" | "C13" | "C15" | "C16";
	severity: "RED" | "YELLOW";
	participants: ReviewParticipant[];
	involved_seat_ids: string[];
	status: "OPEN" | "ACKED";
	is_new: boolean;
	resolution_hint: {
		actor_participant_id: string;
		action: string;
		target_rows: number[];
		swap_candidates: ReviewParticipant[];
		message: string;
		locked_conflict: boolean;
	};
}
export interface Review {
	attribution?: { groups: AttributedEdit[]; message: string | null };
	review_status: "NOT_CHECKED" | "IN_PROGRESS" | "PASSED";
	findings?: Finding[];
	summary?: {
		open_blocking: number;
		open_advisory: number;
		acked: number;
		resolved: number;
	};
	acknowledgements?: Record<
		string,
		{
			status: "ACKED" | "OPEN";
			note: string;
			actor: string;
			changed_at: string;
		}
	>;
}
// One card per actor, while each underlying pair retains its own acknowledgement.
export function groupFindings(findings: Finding[]) {
	const groups = new Map<string, Finding[]>();
	for (const finding of findings) {
		const actor = finding.resolution_hint.actor_participant_id;
		groups.set(actor, [...(groups.get(actor) ?? []), finding]);
	}
	return [...groups.entries()];
}

export interface AttributedEdit {
  operation_id: string;
  participant_ids: string[];
  finding_ids: string[];
  focus_seat_ids: string[];
  changes: import("./manual-history").EditChange[];
}
export function focusedGroups(findings: Finding[], attribution?: Review["attribution"]): [string, Finding[]][] {
  const owners = new Map((attribution?.groups ?? []).flatMap(g => g.finding_ids.map(id => [id, `edit:${g.operation_id}`] as const)));
  const groups = new Map<string, Finding[]>();
  for (const f of findings) {
    const key = owners.get(f.finding_id) ?? f.resolution_hint.actor_participant_id;
    groups.set(key, [...(groups.get(key) ?? []), f]);
  }
  return [...groups].sort(([a], [b]) => Number(b.startsWith("edit:")) - Number(a.startsWith("edit:")));
}
export function restorationResolves(before: Finding[], after: Finding[], linked: string[]) {
  const prior = new Set(before.map(f => f.finding_id));
  const remaining = new Set(after.map(f => f.finding_id));
  return linked.every(id => !remaining.has(id)) && after.every(f => prior.has(f.finding_id));
}


export function participantSeats(ids: string[], state: WorkingState): string[] {
  return [...new Set(ids.flatMap(pid => state.items[pid]?.seat_ids ?? []))];
}

export function findingSeats(finding: Finding, state: WorkingState): string[] {
  const oldParticipantSeats = new Set(finding.participants.flatMap(p => p.seat_ids));
  const occupied = new Set(Object.values(state.items).flatMap(item => item.seat_ids));
  // Gap findings refer to an actual empty location; those do not travel with a
  // registration. Stop marking a former gap as soon as somebody fills it.
  const gaps = finding.involved_seat_ids.filter(sid => !oldParticipantSeats.has(sid) && !occupied.has(sid));
  return [...participantSeats(finding.participants.map(p => p.participant_id), state), ...gaps];
}

export function reviewSeatHighlights(review: Review | null, state: WorkingState): Record<string, "RED" | "YELLOW"> {
  const result: Record<string, "RED" | "YELLOW"> = {};
  for (const finding of review?.findings ?? []) {
    if (finding.status !== "OPEN") continue;
    const group = review?.attribution?.groups.find(g => g.finding_ids.includes(finding.finding_id));
    const seats = group ? participantSeats(group.participant_ids, state) : findingSeats(finding, state);
    for (const sid of seats) if (result[sid] !== "RED") result[sid] = finding.severity;
  }
  return result;
}

export function followSelectedSeat(selected: string | null, before: WorkingState, after: WorkingState): string | null {
  if (!selected) return null;
  const owner = Object.keys(before.items).find(pid => before.items[pid].seat_ids.includes(selected));
  return owner ? after.items[owner]?.seat_ids[0] ?? null : selected;
}
