import type { AllocationResult, Registration } from "./allocation-types";
export interface WorkingItem {
    seat_ids: string[];
    display_names: string[];
    name_checked: boolean;
    attendance_confirmed: boolean;
    seat_reviewed: boolean;
    locked: boolean;
    note: string;
    companion_absent: boolean;
    absence_reason: string;
    dock_reason: string;
    previous_seat_ids: string[];
    changed_at: string | null;
}
export interface WorkingState {
    participants: Registration[];
    items: Record<string, WorkingItem>;
}
export interface Workspace {
    base: AllocationResult & {
        published_at?: string;
    };
    state: WorkingState;
    revision: number;
    saved_at: string | null;
    actor: string | null;
    has_newer_plan?: boolean;
}
export const eligible = (p: Registration) => ["CONFIRMED", "REPLACEMENT_CONFIRMED"].includes(p.registration_status);
export function move(state: WorkingState, base: AllocationResult, pid: string, sid: string): WorkingState {
    const p = state.participants.find(p => p.participant_id === pid);
    const m = state.items[pid];
    if (!p || !eligible(p) || m.locked)
        throw Error("Unlock this allocation before moving it.");
    const cells = base.floor_plan.rows.flatMap(r => r.seats.map(s => ({ ...s, row: r.row_number })));
    const target = cells.find(s => s.seat_id === sid);
    if (!target || target.is_blocked)
        throw Error("This structural position cannot be assigned.");
    function destination(person: Registration, item: WorkingItem, cell: typeof target): string[] {
        if (!cell)
            throw Error("Choose a destination.");
        const pair = person.contribution_tier === "EMPEROR" && !item.companion_absent;
        const start = cell.physical_position % 2 ? cell.physical_position : cell.physical_position - 1;
        const seats = pair ? cells.filter(s => s.row === cell.row && [start, start + 1].includes(s.physical_position)) : [cell];
        if (seats.length !== (pair ? 2 : 1) || seats.some(s => s.is_blocked || s.side !== cell.side))
            throw Error("A pair needs two adjacent seats on the same side of the aisle.");
        if (person.requires_accessible_seat && seats.some(s => !s.is_accessible))
            throw Error("This allocation requires accessible seats.");
        return seats.map(s => s.seat_id);
    }
    const ids = destination(p, m, target);
    const others = Object.entries(state.items).filter(([id, v]) => id !== pid && v.seat_ids.some(s => ids.includes(s)));
    if (others.length > 1)
        throw Error("Move the separate occupants to the dock first.");
    const next = structuredClone(state);
    const stamp = new Date().toISOString();
    if (others.length) {
        const [otherId, other] = others[0];
        if (other.locked)
            throw Error("Unlock the destination allocation before swapping.");
        if (other.seat_ids.length !== ids.length || !other.seat_ids.every(s => ids.includes(s)))
            throw Error("Swap individuals with individuals or pairs with pairs; use the dock to rearrange different sizes.");
        next.items[otherId].seat_ids = m.seat_ids.length ? destination(state.participants.find(p => p.participant_id === otherId)!, other, cells.find(s => s.seat_id === m.seat_ids[0])) : [];
        next.items[otherId].previous_seat_ids = other.seat_ids;
        next.items[otherId].dock_reason = m.seat_ids.length ? "" : "Displaced during assignment";
        next.items[otherId].changed_at = stamp;
    }
    next.items[pid] = { ...m, seat_ids: ids, previous_seat_ids: m.seat_ids, dock_reason: "", changed_at: stamp };
    return next;
}
export function dock(state: WorkingState, pid: string): WorkingState {
    const m = state.items[pid];
    if (m.locked)
        throw Error("Unlock the allocation before sending it to the dock.");
    const next = structuredClone(state);
    next.items[pid] = { ...m, seat_ids: [], previous_seat_ids: m.seat_ids, dock_reason: "Manual rearrangement", changed_at: new Date().toISOString() };
    return next;
}
