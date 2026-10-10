"""JSON stdin/stdout application adapter for the local Next.js host."""

import copy
import json
import os
import sys

from seat_solver.prototype.models import read_json
from seat_solver.production.plan_store import PlanStore, participant_view
from seat_solver.production.policy import ROOT, DomainError, policy
from seat_solver.production.production import error, solve


def dispatch(body, store=None):
    if not isinstance(body, dict):
        raise DomainError("INVALID_INPUT", "Command must be an object")
    store = store or PlanStore(
        os.environ.get("SEAT_PLAN_DB", str(ROOT / "output/paid-seats-v4.sqlite3"))
    )
    command = body.get("command")
    event = body.get("event_id", "PJKIT-2026")
    actor = body.get("actor", "local-cli")
    if command and command.startswith("workspace_"):
        from seat_solver.production.workspace import WorkspaceStore

        result = WorkspaceStore(store).action(event, actor, body)
        if isinstance(result, dict) and "state" in result:
            from seat_solver.production.production_data import restore_synthetic_display_names

            restore_synthetic_display_names(result["state"])
        return result
    if command == "setup":
        req = read_json(
            os.environ.get(
                "SEAT_EVENT_REQUEST", str(ROOT / "data/production_request.json")
            )
        )
        layout = req["layout"]
        return {
            "floor_plan": {
                **layout,
                "total_seats": len(layout["seats"]),
                "rows": [
                    {
                        "row_number": r,
                        "tier_band": None,
                        "seats": [
                            {
                                **s,
                                "occupancy_status": "BLOCKED"
                                if s["is_blocked"]
                                else "EMPTY",
                                "participant_id": None,
                                "display_name": None,
                            }
                            for s in layout["seats"]
                            if s["row_number"] == r
                        ],
                    }
                    for r in range(1, layout["row_count"] + 1)
                ],
            },
            "registrations": len(req["participants"]),
        }
    if command == "venue":
        plan = store.published(event)
        if not plan:
            return {"status": "unpublished"}
        return {
            "status": "published",
            "floor_plan": plan["floor_plan"],
            "published_at": plan["published_at"],
            "pair_display": {
                a["participant_id"]: {
                    "primary_name": plan.get("operations", {})
                    .get(a["participant_id"], {})
                    .get("display_names", [a["full_name"]])[0],
                }
                for a in plan["assignments"]
            },
            "event_id": event,
        }
    if command == "public":
        return participant_view(store.published(event), body.get("participant_id"))
    if command == "history":
        return {"plans": store.history(event)}
    if command == "load":
        return store.latest(event)
    if command == "get":
        plan = store.get(body["plan_version_id"])
        if plan["event_id"] != event:
            raise DomainError("NOT_FOUND", "Plan not in this event")
        return plan
    if command == "solve":
        latest = store.latest(event)
        if latest and latest["policy_version_id"] != policy()["policy_version_id"]:
            raise DomainError("POLICY_VERSION_MISMATCH", "Use the fresh paid-seats-v4 demo store; old histories are read-only archives.")
        from seat_solver.production.workspace import WorkspaceStore, apply_display, validate_state
        workspaces = WorkspaceStore(store) if hasattr(store, "connection") else None
        saved = workspaces.load(event) if workspaces else None
        if body.get("generation_mode") == "REPAIR_ABSENCE":
            from seat_solver.production.absence_repair import repair
            if not saved or saved["saved_at"] is None:
                raise DomainError("INVALID_INPUT", "Save the working map before absence repair")
            if body.get("plan_version_id") != saved["base"]["plan_version_id"] or body.get("revision") != saved["revision"]:
                raise DomainError("STALE_BASELINE", "Reload the saved map before absence repair")
            result = repair(saved["base"], saved["state"], body.get("preferences"))
            guard = {"plan_version_id": saved["base"]["plan_version_id"], "revision": saved["revision"]}
            return store.save(result, actor, workspace_guard=guard) if result["status"] == "success" else result
        event_source = (
            latest["source_request"]
            if latest
            else read_json(
                os.environ.get(
                    "SEAT_EVENT_REQUEST", str(ROOT / "data/production_request.json")
                )
            )
        )
        req = copy.deepcopy(body.get("request") or event_source)
        guard = None
        if saved and not body.get("request"):
            req = validate_state(saved["base"], saved["state"])
            if saved["saved_at"] is not None:
                guard = {"plan_version_id": saved["base"]["plan_version_id"], "revision": saved["revision"]}
            if "revision" in body and (body["revision"] != saved["revision"] or body.get("plan_version_id") != saved["base"]["plan_version_id"]):
                raise DomainError("STALE_BASELINE", "Reload before regenerating the saved map")
        # Reuse registrations and preferences, but take current venue obstacles and ranks
        # when regenerating the same configured hall. Explicit requests own their layout.
        if latest and not body.get("request"):
            configured = read_json(os.environ.get(
                "SEAT_EVENT_REQUEST", str(ROOT / "data/production_request.json")
            ))
            def geometry(layout):
                return {(s["seat_id"], s["row_number"], s["physical_position"])
                        for s in layout["seats"]}
            if configured["event_id"] == event and geometry(configured["layout"]) == geometry(req["layout"]):
                req["layout"] = copy.deepcopy(configured["layout"])
                req["layout_version_id"] = configured["layout_version_id"]
        req["event_id"] = event
        for key in (
            "generation_mode",
            "preferences",
        ):
            if key in body:
                req[key] = body[key]
        if "baseline_plan_version_id" in body or "participants" in body:
            raise DomainError("INVALID_INPUT", "Regeneration accepts preferences, not attendance or registration changes")
        result = solve(req)
        if result["status"] == "success" and saved and not body.get("request"):
            result["operations"] = copy.deepcopy(saved["state"]["items"])
            assigned = {a["participant_id"]: a["seat_ids"] for a in result["assignments"]}
            for pid, item in result["operations"].items():
                item["seat_ids"] = assigned.get(pid, [])
                if item["seat_ids"]:
                    item["dock_reason"] = ""
            apply_display(result, result["operations"])
        return store.save(result, actor, workspace_guard=guard) if result["status"] == "success" else result
    if command in ("manual", "submit", "approve", "publish", "reject"):
        existing = store.get(body["plan_version_id"])
        if existing["event_id"] != event:
            raise DomainError("NOT_FOUND", "Plan not in this event")
        if command == "manual":
            return store.edit(
                body["plan_version_id"],
                body["assignments"],
                actor,
                body["validation_revision"],
            )
        return store.transition(
            body["plan_version_id"], command, actor, body["validation_revision"]
        )
    raise DomainError("INVALID_INPUT", "Unknown application operation")


def main():
    try:
        response = dispatch(json.load(sys.stdin))
    except DomainError as exc:
        response = error(exc.code, str(exc), exc.details)
    except (KeyError, ValueError, TypeError) as exc:
        response = error("INVALID_INPUT", str(exc))
    print(json.dumps(response, ensure_ascii=False))


if __name__ == "__main__":
    main()
