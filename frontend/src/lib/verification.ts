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
