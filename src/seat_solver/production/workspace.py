"""Private, revision-checked drafts and explicit staff publication.

Business-rule review is persisted separately from the editable seating state.
This module retains draft integrity, immutable snapshots and stale-write checks.
"""

import copy
import json
import uuid

from seat_solver.production.policy import ELIGIBLE, DomainError, validate_request
from seat_solver.production.production import format_result, now
from seat_solver.production.production_scoring import options


def normalize_display_names(state):
    """Retire legacy partner overrides while preserving the editable payer name."""
    for item in state["items"].values():
        names = item.get("display_names")
        if isinstance(names, list) and names:
            item["display_names"] = [names[0]] * len(names)
        item.pop("partner_name_edited", None)
    return state


def initial_state(plan):
    assigned = {a["participant_id"]: a for a in plan["assignments"]}
    items = {}
    for p in plan["source_request"]["participants"]:
        pid = p["participant_id"]
        a = assigned.get(pid)
        # Generated pairs place the contributor at the better priority position.
        # Normalize occupant order once so unlink always retains the contributor.
        ordered = (
            sorted(a["seats"], key=lambda seat: seat["priority_rank"]) if a else []
        )
        items[pid] = {
            "seat_ids": [seat["seat_id"] for seat in ordered],
            "display_names": [p["full_name"]] * (2 if p["contribution_tier"] == "EMPEROR" else 1),
            "note": "",
            "dock_reason": "",
            "previous_seat_ids": [],
            "changed_at": None,
        }
        if pid in plan.get("operations", {}):
            items[pid].update(copy.deepcopy(plan["operations"][pid]))
            items[pid]["seat_ids"] = a["seat_ids"] if a else []
    return normalize_display_names({
        "participants": copy.deepcopy(plan["source_request"]["participants"]),
        "items": items,
    })


def validate_metadata(request, metadata):
    if not isinstance(metadata, dict):
        raise DomainError("INVALID_INPUT", "Invalid participant details")
    people = {p["participant_id"]: p for p in request["participants"]}
    for pid, m in metadata.items():
        if pid not in people or not isinstance(m, dict):
            raise DomainError("INVALID_INPUT", "Unknown participant details")
        for key in ("note", "dock_reason"):
            if not isinstance(m.get(key), str) or len(m[key]) > 2000:
                raise DomainError("INVALID_INPUT", "Invalid note")
        if set(m) != {"seat_ids", "display_names", "note", "dock_reason", "previous_seat_ids", "changed_at"}:
            raise DomainError("INVALID_INPUT", "Unsupported working-draft fields")
        if m["changed_at"] is not None and not isinstance(m["changed_at"], str):
            raise DomainError("INVALID_INPUT", "Invalid change timestamp")
        names = m.get("display_names")
        expected = 2 if people[pid]["contribution_tier"] == "EMPEROR" else 1
        if (
            not isinstance(names, list)
            or len(names) != expected
            or any(
                not isinstance(n, str) or not n.strip() or len(n) > 80 for n in names
            )
        ):
            raise DomainError(
                "INVALID_INPUT",
                "Provide a display name for each registered occupant (maximum 80 characters)",
            )


def apply_display(result, metadata):
    for a in result["assignments"]:
        m = metadata.get(a["participant_id"])
        if m:
            for seat in a["seats"]:
                seat["display_name"] = m["display_names"][0]
    names = {
        s["seat_id"]: s["display_name"]
        for a in result["assignments"]
        for s in a["seats"]
    }
    for row in result["floor_plan"]["rows"]:
        for seat in row["seats"]:
            seat["display_name"] = names.get(seat["seat_id"])


def validate_state(plan, state):
    if not isinstance(state, dict) or set(state) != {"participants", "items"}:
        raise DomainError("INVALID_INPUT", "Invalid working draft")
    request = copy.deepcopy(plan["source_request"])
    request["participants"] = state["participants"]
    validate_request(request)
    original = {p["participant_id"]: p for p in plan["source_request"]["participants"]}
    current = {p["participant_id"]: p for p in request["participants"]}
    if current != original:
        raise DomainError("INVALID_INPUT", "Registered details are read-only; edit the display name instead")
    items = state["items"]
    if set(items) != set(current):
        raise DomainError(
            "INVALID_INPUT", "Every registration must remain accounted for"
        )
    validate_items(request, items)
    return request


def validate_items(request, items, valid_options=None):
    """Validate placement edits against already-validated immutable registration inputs."""
    current = {p["participant_id"]: p for p in request["participants"]}
    validate_metadata(request, items)
    seats = {s["seat_id"]: s for s in request["layout"]["seats"]}
    occupied = set()
    for pid, m in items.items():
        ids = m.get("seat_ids")
        if not isinstance(ids, list) or any(
            not isinstance(s, str) or s not in seats or seats[s]["is_blocked"]
            for s in ids
        ):
            raise DomainError("INVALID_INPUT", "Unknown or blocked seat")
        if len(ids) != len(set(ids)) or occupied.intersection(ids):
            raise DomainError("INVALID_INPUT", "Seat assignments overlap")
        occupied.update(ids)
        if current[pid]["registration_status"] not in ELIGIBLE and ids:
            raise DomainError(
                "INVALID_INPUT", "Unconfirmed registrations cannot occupy paid seats"
            )
        if ids and tuple(sorted(ids)) not in (valid_options[pid] if valid_options is not None else {
            tuple(sorted(seat["seat_id"] for seat in option)) for option in options(request, current[pid])
        }):
            raise DomainError("INVALID_INPUT", "Keep the paid seat count, valid adjacent pairs and required accessibility")
        if not isinstance(m.get("previous_seat_ids"), list) or any(
            s not in seats for s in m["previous_seat_ids"]
        ):
            raise DomainError("INVALID_INPUT", "Invalid previous seat location")
    return request


def snapshot(plan, state):
    request = validate_state(plan, state)
    stats = copy.deepcopy(plan["solver"])
    stats.update(status="MANUALLY_MODIFIED", proof=[], canonicalization_complete=False)
    placements = {
        p["participant_id"]: state["items"][p["participant_id"]]["seat_ids"]
        for p in request["participants"]
        if p["registration_status"] in ELIGIBLE
    }
    if any(not seats for seats in placements.values()):
        raise DomainError(
            "INVALID_INPUT", "Assign every paid registration before publishing"
        )
    result = format_result(request, placements, stats)
    result["operations"] = copy.deepcopy(state["items"])
    result["manually_modified"] = True
    # format_result normally describes validated solver output; staff publication
    # must not claim its manually edited layout passed the removed review.
    result["hard_constraint_validation"] = {"checked": False}
    result["solver_status_at_generation"] = plan["solver_status_at_generation"]
    apply_display(result, state["items"])
    return result


class WorkspaceStore:
    def __init__(self, store):
        self.store = store
        with store.connection() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS workspaces (event TEXT PRIMARY KEY, base TEXT NOT NULL, revision INTEGER NOT NULL, body TEXT NOT NULL, saved_at TEXT NOT NULL, actor TEXT NOT NULL)"
            )

            db.execute("CREATE TABLE IF NOT EXISTS workspace_reviews (event TEXT NOT NULL, base TEXT NOT NULL, body TEXT NOT NULL, PRIMARY KEY(event,base))")

            db.execute(
                "CREATE TABLE IF NOT EXISTS workspace_versions (event TEXT NOT NULL, base TEXT NOT NULL, body TEXT NOT NULL, saved_at TEXT NOT NULL, actor TEXT NOT NULL, PRIMARY KEY(event,base))"
            )

    def review(self, db, event, base):
        row = db.execute("SELECT body FROM workspace_reviews WHERE event=? AND base=?", (event, base)).fetchone()
        return json.loads(row["body"]) if row else {"review_status": "NOT_CHECKED"}

    def save_review(self, db, event, base, review):
        db.execute("INSERT INTO workspace_reviews(event,base,body) VALUES(?,?,?) ON CONFLICT(event,base) DO UPDATE SET body=excluded.body",
                   (event, base, json.dumps(review)))

    def open(self, event, actor, plan_id=None):
        """Explicitly select a plan, preserving saved edits and stale-write protection."""
        with self.store.connection() as db:
            if plan_id is None:
                latest = db.execute(
                    "SELECT id FROM plans WHERE event=? ORDER BY rowid DESC LIMIT 1", (event,)
                ).fetchone()
                if not latest:
                    raise DomainError("NOT_FOUND", "No seating draft exists for this event")
                plan_id = latest["id"]
            plan = self.store._load(db, plan_id)
            if plan["event_id"] != event:
                raise DomainError("NOT_FOUND", "Plan not in this event")
            current = db.execute("SELECT * FROM workspaces WHERE event=?", (event,)).fetchone()
            if current and current["base"] == plan_id:
                return {
                    "review": self.review(db, event, plan_id),
                    "base": plan, "state": normalize_display_names(json.loads(current["body"])),
                    "revision": current["revision"], "saved_at": current["saved_at"],
                    "actor": current["actor"], "has_newer_plan": False,
                }
            if current:
                db.execute(
                    "INSERT INTO workspace_versions(event,base,body,saved_at,actor) VALUES(?,?,?,?,?) ON CONFLICT(event,base) DO UPDATE SET body=excluded.body,saved_at=excluded.saved_at,actor=excluded.actor",
                    (event, current["base"], current["body"], current["saved_at"], current["actor"]),
                )
            archived = db.execute(
                "SELECT * FROM workspace_versions WHERE event=? AND base=?", (event, plan_id)
            ).fetchone()
            state = normalize_display_names(json.loads(archived["body"])) if archived else initial_state(plan)
            revision = current["revision"] + 1 if current else 0
            stamp = archived["saved_at"] if archived else plan.get("published_at") or now()
            owner = archived["actor"] if archived else actor
            db.execute(
                "INSERT INTO workspaces(event,base,revision,body,saved_at,actor) VALUES(?,?,?,?,?,?) ON CONFLICT(event) DO UPDATE SET base=excluded.base,revision=excluded.revision,body=excluded.body,saved_at=excluded.saved_at,actor=excluded.actor",
                (event, plan_id, revision, json.dumps(state), stamp, owner),
            )
            db.execute("INSERT INTO audit(event,plan,action,actor,at) VALUES(?,?,?,?,?)",
                       (event, plan_id, "WORKSPACE_OPEN", actor, now()))
            return {"review": self.review(db, event, plan_id), "base": plan, "state": state, "revision": revision,
                    "saved_at": stamp, "actor": owner, "has_newer_plan": False}

    def load(self, event):
        plan = self.store.latest(event)
        if not plan:
            return None
        with self.store.connection() as db:
            row = db.execute(
                "SELECT * FROM workspaces WHERE event=?", (event,)
            ).fetchone()
            if row:
                base = self.store._load(db, row["base"])
                return {
                    "review": self.review(db, event, row["base"]),
                    "base": base,
                    "state": normalize_display_names(json.loads(row["body"])),
                    "revision": row["revision"],
                    "saved_at": row["saved_at"],
                    "actor": row["actor"],
                    "has_newer_plan": base["plan_version_id"]
                    != plan["plan_version_id"],
                }
        return {
            "base": plan,
            "state": initial_state(plan),
            "revision": 0,
            "saved_at": None,
            "actor": None,
            "has_newer_plan": False,
        }

    def action(self, event, actor, body):
        command = body["command"]
        if command == "workspace_load":
            return self.load(event)
        if command == "workspace_open":
            return self.open(event, actor, body.get("plan_version_id"))
        if command not in {"workspace_save", "workspace_publish", "workspace_check", "workspace_ack"}:
            raise DomainError("INVALID_INPUT", "Unknown workspace operation")
        # All state checks, updates and publication occur in the same transaction.
        with self.store.connection() as db:
            plan = self.store._load(db, body["plan_version_id"])
            if plan["event_id"] != event:
                raise DomainError("NOT_FOUND", "Plan not in this event")
            row = db.execute(
                "SELECT * FROM workspaces WHERE event=?", (event,)
            ).fetchone()
            revision = row["revision"] if row else 0
            if body.get("revision") != revision or (
                row and row["base"] != plan["plan_version_id"]
            ):
                raise DomainError(
                    "STALE_BASELINE",
                    "Another staff member saved a newer draft. Reload before editing.",
                )
            state = normalize_display_names(json.loads(row["body"])) if row else initial_state(plan)
            from seat_solver.production.verification import check
            review = self.review(db, event, plan["plan_version_id"])
            if command in {"workspace_check", "workspace_ack"}:
                feedback = command == "workspace_check" and body.get("state") is not None
                if (feedback or command == "workspace_ack") and review["review_status"] == "NOT_CHECKED":
                    raise DomainError("INVALID_INPUT", "Submit the saved draft for review first")
                checked = check(plan, body["state"] if feedback else state, review)
                if command == "workspace_ack":
                    fid, status, note = body.get("finding_id"), body.get("status"), body.get("note", "")
                    if status not in {"ACKED", "OPEN"} or not isinstance(note, str) or len(note) > 2000:
                        raise DomainError("INVALID_INPUT", "Invalid review acknowledgement")
                    if not any(f["finding_id"] == fid for f in checked["findings"]):
                        raise DomainError("INVALID_INPUT", "Finding is no longer present; refresh review")
                    checked["acknowledgements"][fid] = {"status": status, "note": note, "actor": actor, "changed_at": now()}
                    checked = check(plan, state, checked)
                    db.execute("INSERT INTO audit(event,plan,action,actor,at) VALUES(?,?,?,?,?)",
                               (event, plan["plan_version_id"], f"REVIEW_{status}:{fid}", actor, now()))
                if not feedback:
                    if row is None:
                        db.execute("INSERT INTO workspaces(event,base,revision,body,saved_at,actor) VALUES(?,?,?,?,?,?)",
                                   (event, plan["plan_version_id"], revision, json.dumps(state), now(), actor))
                    checked["checked_revision"] = revision
                    self.save_review(db, event, plan["plan_version_id"], checked)
                from seat_solver.production.verification import attribute_history
                attribution = attribute_history(plan, body["state"] if feedback else state,
                                                checked["findings"], body.get("history_context"))
                return {**checked, "revision": revision, "attribution": attribution}
            if command == "workspace_save":
                new = copy.deepcopy(body["state"])
                if isinstance(new, dict) and isinstance(new.get("items"), dict):
                    for m in new["items"].values():
                        if isinstance(m, dict):
                            m.pop("partner_name_edited", None)
                validate_state(plan, new)
                new = normalize_display_names(new)
                if review["review_status"] == "PASSED":
                    review = {"review_status": "NOT_CHECKED"}
                elif review["review_status"] == "IN_PROGRESS":
                    review.pop("checked_revision", None)
                self.save_review(db, event, plan["plan_version_id"], review)
                revision += 1
                stamp = now()
                db.execute(
                    "INSERT INTO workspaces(event,base,revision,body,saved_at,actor) VALUES(?,?,?,?,?,?) ON CONFLICT(event) DO UPDATE SET base=excluded.base,revision=excluded.revision,body=excluded.body,saved_at=excluded.saved_at,actor=excluded.actor",
                    (
                        event,
                        plan["plan_version_id"],
                        revision,
                        json.dumps(new),
                        stamp,
                        actor,
                    ),
                )
                db.execute(
                    "INSERT INTO audit(event,plan,action,actor,at) VALUES(?,?,?,?,?)",
                    (
                        event,
                        plan["plan_version_id"],
                        f"WORKING_SAVE:{revision}",
                        actor,
                        stamp,
                    ),
                )
                return {
                    "base": plan,
                    "state": new,
                    "review": review,
                    "revision": revision,
                    "saved_at": stamp,
                    "actor": actor,
                }
            checked = check(plan, state, review)
            if review["review_status"] == "NOT_CHECKED":
                raise DomainError("REVIEW_REQUIRED", "Submit the saved draft for safeguard review before publishing")
            if checked["summary"]["open_blocking"]:
                raise DomainError("REVIEW_REQUIRED", "Resolve or override every blocking safeguard before publishing", checked)
            checked.update(review_status="PASSED", checked_revision=revision, actor=actor, published_at=now())
            pointer = db.execute(
                "SELECT published FROM events WHERE id=?", (event,)
            ).fetchone()
            published = pointer["published"] if pointer else None
            expected = (
                plan["plan_version_id"]
                if plan["publication_status"] == "PUBLISHED"
                else plan.get("expected_published_version_id")
            )
            if published != expected:
                raise DomainError(
                    "STALE_BASELINE",
                    "The published plan changed. Review against the latest version.",
                )
            result = snapshot(plan, state)
            result["safeguard_review"] = checked
            result["hard_constraint_validation"] = {"checked": True, "placement_integrity": True,
                "open_blocking": 0, "overrides": checked["summary"]["acked"]}
            from seat_solver.production.plan_store import digest

            pid = "PLAN-" + uuid.uuid4().hex
            stamp = now()
            result.update(
                plan_version_id=pid,
                predecessor_plan_version_id=plan["plan_version_id"],
                publication_status="PUBLISHED",
                created_at=stamp,
                expected_published_version_id=published,
                working_revision=revision,
            )
            db.execute(
                "INSERT INTO plans(id,event,body,hash,state,actor,created,published_by,published_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    pid,
                    event,
                    json.dumps(result),
                    digest(result),
                    "PUBLISHED",
                    actor,
                    stamp,
                    actor,
                    stamp,
                ),
            )
            if published:
                db.execute(
                    "UPDATE plans SET state='SUPERSEDED' WHERE id=?", (published,)
                )
            db.execute(
                "INSERT INTO events VALUES(?,?) ON CONFLICT(id) DO UPDATE SET published=excluded.published",
                (event, pid),
            )
            db.execute(
                "INSERT INTO audit(event,plan,action,actor,at) VALUES(?,?,?,?,?)",
                (event, pid, "PUBLISHED", actor, stamp),
            )
            # Monotonic revisions prevent old browser writes recreating a consumed draft.
            # Named columns also accept databases with the retired review column.
            db.execute(
                "INSERT INTO workspaces(event,base,revision,body,saved_at,actor) VALUES(?,?,?,?,?,?) ON CONFLICT(event) DO UPDATE SET base=excluded.base,revision=excluded.revision,body=excluded.body,saved_at=excluded.saved_at,actor=excluded.actor",
                (event, pid, revision + 1, json.dumps(state), stamp, actor),
            )
            self.save_review(db, event, plan["plan_version_id"], checked)
            self.save_review(db, event, pid, checked)
            return {
                "review": checked,
                "base": self.store._load(db, pid),
                "state": state,
                "revision": revision + 1,
                "saved_at": stamp,
                "actor": actor,
            }
