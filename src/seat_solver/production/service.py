"""JSON stdin/stdout application adapter for the local Next.js host."""

import copy
import json
import os
import sys

from seat_solver.prototype.models import read_json
from seat_solver.production.plan_store import PlanStore, participant_view
from seat_solver.production.policy import ROOT, DomainError
from seat_solver.production.production import error, solve


def dispatch(body, store=None):
    if not isinstance(body, dict):
        raise DomainError("INVALID_INPUT", "Command must be an object")
    store = store or PlanStore(
        os.environ.get("SEAT_PLAN_DB", str(ROOT / "output/plans.sqlite3"))
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
        # Reuse registrations and preferences, but take current venue obstacles
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
            "baseline_plan_version_id",
            "participants",
        ):
            if key in body:
                req[key] = body[key]
        baseline = None
        if req["generation_mode"] == "REPAIR_PUBLISHED":
            baseline = store.published(event)
            if not baseline:
                raise DomainError("STALE_BASELINE", "No published baseline exists")
            expected = body.get("baseline_plan_version_id")
            if expected is not None and expected != baseline["plan_version_id"]:
                raise DomainError(
                    "STALE_BASELINE", "Requested baseline is no longer published"
                )
            req["baseline_plan_version_id"] = baseline["plan_version_id"]
        else:
            req["baseline_plan_version_id"] = None
        result = solve(req, baseline)
        return (
            store.save(result, actor, baseline["plan_version_id"] if baseline else None)
            if result["status"] == "success"
            else result
        )
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
