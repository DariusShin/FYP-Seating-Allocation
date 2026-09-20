import type {
	AllocationResult,
	Assignment,
	AssignmentSeat,
} from "./allocation-types";

/** An editor draft is deliberately separate from the validated solver document. */
export type SeatPlacements = Record<string, string[]>;
export type EditOutcome =
	| { placements: SeatPlacements; message: string }
	| { error: string };

export function initialPlacements(result: AllocationResult): SeatPlacements {
	return Object.fromEntries(
		result.assignments.map((a) => [a.participant_id, [...a.seat_ids]]),
	);
}

function destination(
	result: AllocationResult,
	participant: Assignment,
	seatId: string,
): string[] | string {
	const row = result.floor_plan.rows.find((r) =>
		r.seats.some((s) => s.seat_id === seatId),
	);
	const seat = row?.seats.find((s) => s.seat_id === seatId);
	if (!row || !seat || seat.is_blocked)
		return "Blocked seats cannot be assigned.";
	let seats = [seat];
	if (participant.allocation_type === "EMPEROR_PAIR") {
		// Fixed adjacent physical pairs: 1–2, 3–4, …; never pair across the aisle.
		const start =
			seat.physical_position % 2 === 0
				? seat.physical_position - 1
				: seat.physical_position;
		seats = row.seats.filter(
			(s) => s.physical_position === start || s.physical_position === start + 1,
		);
		if (
			seats.length !== 2 ||
			seats.some((s) => s.is_blocked) ||
			seats[0].side !== seats[1].side
		) {
			return "Emperor registrations need two adjacent available seats on the same side of the aisle.";
		}
	}
	if (
		participant.requires_accessible_seat &&
		!seats.some((s) => s.is_accessible)
	) {
		return "This participant needs an accessible seat at the edge of the hall.";
	}
	return seats.map((s) => s.seat_id);
}

/** Move or swap whole registrations atomically. A rejected edit never changes the draft. */
export function placeParticipant(
	result: AllocationResult,
	placements: SeatPlacements,
	participantId: string,
	seatId: string,
): EditOutcome {
	const participant = result.assignments.find(
		(a) => a.participant_id === participantId,
	);
	if (!participant) return { error: "Participant not found." };
	const target = destination(result, participant, seatId);
	if (typeof target === "string") return { error: target };
	const source = placements[participantId] ?? [];
	if (
		source.length === target.length &&
		source.every((id) => target.includes(id))
	)
		return {
			placements,
			message: "This participant is already in these seats.",
		};
	const occupants = Object.entries(placements).filter(
		([id, seats]) =>
			id !== participantId && seats.some((s) => target.includes(s)),
	);
	if (occupants.length > 1)
		return {
			error:
				"These seats contain separate registrations. Remove them before placing a pair here.",
		};
	const next = { ...placements, [participantId]: target };
	if (occupants.length) {
		const [otherId, otherSeats] = occupants[0];
		if (
			otherSeats.length !== target.length ||
			!otherSeats.every((s) => target.includes(s))
		) {
			return {
				error:
					"Swap single seats with single seats, or Emperor pairs with pairs. Remove the current assignment first.",
			};
		}
		if (source.length) {
			const other = result.assignments.find(
				(a) => a.participant_id === otherId,
			)!;
			const returnSeats = destination(result, other, source[0]);
			if (typeof returnSeats === "string")
				return { error: `Cannot swap: ${returnSeats}` };
			next[otherId] = returnSeats;
		} else {
			// Replacing an occupant with an unassigned registration returns them to the list.
			next[otherId] = [];
		}
	}
	return {
		placements: next,
		message: occupants.length
			? "Assignment updated. Both registrations have been accounted for."
			: `${participant.full_name} moved to ${target.join(" + ")}.`,
	};
}

export function removeParticipant(
	placements: SeatPlacements,
	participantId: string,
): SeatPlacements {
	return { ...placements, [participantId]: [] };
}

/** Build display data only; callers must not present baseline solver metrics as draft validation. */
export function draftAssignments(
	result: AllocationResult,
	placements: SeatPlacements,
): Assignment[] {
	const cells = new Map(
		result.floor_plan.rows.flatMap((row) =>
			row.seats.map(
				(seat) =>
					[seat.seat_id, { ...seat, row_number: row.row_number }] as const,
			),
		),
	);
	return result.assignments.map((assignment) => {
		const ids = placements[assignment.participant_id] ?? [];
		const seats: AssignmentSeat[] = ids.map((id, index) => {
			const seat = cells.get(id)!;
			return {
				seat_id: id,
				row_number: seat.row_number,
				physical_position: seat.physical_position,
				priority_rank: seat.priority_rank,
				zone: seat.zone,
				display_name:
					assignment.seats[index]?.display_name ?? assignment.full_name,
			};
		});
		return { ...assignment, seat_ids: ids, seats };
	});
}
