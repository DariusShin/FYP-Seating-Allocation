"""JSON stdin/stdout application adapter for the local Next.js host."""

import copy
import json
import os
import sys
from pathlib import Path

from seat_solver.models import read_json
from seat_solver.plan_store import PlanStore, participant_view
from seat_solver.policy import ROOT, DomainError
from seat_solver.production import error, solve


def dispatch(body, store=None):
    if not isinstance(body, dict):
        raise DomainError("INVALID_INPUT", "Command must be an object")
    store = store or PlanStore(
        os.environ.get("SEAT_PLAN_DB", str(ROOT / "output/plans.sqlite3"))
    )
    command = body.get("command")
    event = body.get("event_id", "PJKIT-2026")
    actor = body.get("actor", "local-cli")
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
