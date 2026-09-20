"use client";

import { useRef, useState, type PointerEvent } from "react";

/** Pointer capture keeps a drag alive across seat children, aisles and scroll containers. */
export function useSeatDrag(
	onMove: (participantId: string, seatId: string) => void,
) {
	const [dragId, setDragId] = useState<string | null>(null);
	const [target, setTarget] = useState<string | null>(null);
	const gesture = useRef<{
		id: string;
		x: number;
		y: number;
		dragging: boolean;
	} | null>(null);
	const suppressClick = useRef(false);

	function destination(event: PointerEvent<HTMLButtonElement>) {
		const element = document.elementFromPoint(event.clientX, event.clientY);
		return (
			element?.closest<HTMLButtonElement>("button[data-seat-id]")?.dataset
				.seatId ?? null
		);
	}

	function cancel() {
		if (gesture.current?.dragging) suppressClick.current = true;
		gesture.current = null;
		setDragId(null);
		setTarget(null);
	}

	function onPointerDown(event: PointerEvent<HTMLButtonElement>, id?: string) {
		suppressClick.current = false;
		if (!id || event.button !== 0 || !event.isPrimary) return;
		gesture.current = {
			id,
			x: event.clientX,
			y: event.clientY,
			dragging: false,
		};
		event.currentTarget.setPointerCapture(event.pointerId);
	}

	function onPointerMove(event: PointerEvent<HTMLButtonElement>) {
		const current = gesture.current;
		if (!current) return;
		if (
			!current.dragging &&
			Math.hypot(event.clientX - current.x, event.clientY - current.y) < 6
		)
			return;
		current.dragging = true;
		suppressClick.current = true;
		setDragId(current.id);
		setTarget(destination(event));
	}

	function onPointerUp(event: PointerEvent<HTMLButtonElement>) {
		const current = gesture.current;
		const seat = destination(event);
		cancel();
		if (event.currentTarget.hasPointerCapture(event.pointerId))
			event.currentTarget.releasePointerCapture(event.pointerId);
		if (current?.dragging && seat) onMove(current.id, seat);
	}

	function consumeClick() {
		if (!suppressClick.current) return false;
		suppressClick.current = false;
		return true;
	}

	return {
		dragId,
		target,
		cancel,
		consumeClick,
		onPointerDown,
		onPointerMove,
		onPointerUp,
	};
}
