"""Transactional local reference store. Immutable snapshots, explicit approval and publication.

Replace the persistence adapter for host deployment; SQLite is for this runnable repository.
"""

import copy
import hashlib
import json
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path

from seat_solver.production.policy import DomainError
from seat_solver.production.production import format_result, now
from seat_solver.production.production_validator import audit_result, validate_placements


def digest(body):
    return hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class PlanStore:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript(
                """CREATE TABLE IF NOT EXISTS plans (id TEXT PRIMARY KEY,event TEXT NOT NULL,body TEXT NOT NULL,hash TEXT NOT NULL,state TEXT NOT NULL,actor TEXT NOT NULL,created TEXT NOT NULL,approved_by TEXT,approved_at TEXT,published_by TEXT,published_at TEXT); CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY,published TEXT); CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY,event TEXT,plan TEXT,action TEXT,actor TEXT,at TEXT);"""
            )

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def _load(self, db, pid):
        row = db.execute("SELECT * FROM plans WHERE id=?", (pid,)).fetchone()
        if row is None:
            raise DomainError("NOT_FOUND", "Plan version not found")
        body = json.loads(row["body"])
        body.update(
            publication_status=row["state"],
            validation_revision=row["hash"],
            created_by=row["actor"],
            approved_by=row["approved_by"],
            approved_at=row["approved_at"],
            published_by=row["published_by"],
            published_at=row["published_at"],
        )
        return body

    def get(self, pid):
        with self.connection() as db:
            return self._load(db, pid)

    def published(self, event):
        with self.connection() as db:
            row = db.execute(
                "SELECT published FROM events WHERE id=?", (event,)
            ).fetchone()
            return (
                self._load(db, row["published"]) if row and row["published"] else None
            )

    def latest(self, event):
        with self.connection() as db:
            row = db.execute(
                "SELECT id FROM plans WHERE event=? ORDER BY rowid DESC LIMIT 1",
                (event,),
            ).fetchone()
            return self._load(db, row["id"]) if row else None

    def save(self, result, actor, predecessor=None, predecessor_revision=None):
        report = audit_result(result)
        if not report["passed"]:
            raise DomainError(
                "OUTPUT_VALIDATION_FAILED", "Draft validation failed", report
            )
        body = copy.deepcopy(result)
        body["plan_version_id"] = "PLAN-" + uuid.uuid4().hex
        body["predecessor_plan_version_id"] = predecessor
        body["created_at"] = now()
        body["publication_status"] = "DRAFT"
        event = body["event_id"]
        with self.connection() as db:
            if predecessor_revision is not None:
                prior = self._load(db, predecessor)
                if (
                    prior["event_id"] != event
                    or prior["validation_revision"] != predecessor_revision
                    or prior["publication_status"]
                    not in ("DRAFT", "UNDER_REVIEW", "APPROVED")
                ):
                    raise DomainError(
                        "STALE_BASELINE", "Edited revision is no longer editable"
                    )
                db.execute(
                    "UPDATE plans SET state='SUPERSEDED', approved_by=NULL, approved_at=NULL WHERE id=?",
                    (predecessor,),
                )
                db.execute(
                    "INSERT INTO audit(event,plan,action,actor,at) VALUES(?,?,?,?,?)",
                    (event, predecessor, "EDIT_SUPERSEDED", actor, now()),
                )
            pointer = db.execute(
                "SELECT published FROM events WHERE id=?", (event,)
            ).fetchone()
            body["expected_published_version_id"] = (
                pointer["published"] if pointer else None
            )
            if (
                body["generation_mode"] == "REPAIR_PUBLISHED"
                and body["source_request"]["baseline_plan_version_id"]
                != body["expected_published_version_id"]
            ):
                raise DomainError(
                    "STALE_BASELINE", "Published version changed during repair"
                )
            db.execute(
                "INSERT INTO plans(id,event,body,hash,state,actor,created) VALUES(?,?,?,?,?,?,?)",
                (
                    body["plan_version_id"],
                    event,
                    json.dumps(body),
                    digest(body),
                    "DRAFT",
                    actor,
                    now(),
                ),
            )
            db.execute(
                "INSERT INTO audit(event,plan,action,actor,at) VALUES(?,?,?,?,?)",
                (
                    event,
                    body["plan_version_id"],
                    "GENERATED" if not body["manually_modified"] else "EDITED",
                    actor,
                    now(),
                ),
            )
            return self._load(db, body["plan_version_id"])

    def edit(self, pid, assignments, actor, revision):
        prior = self.get(pid)
        if prior["validation_revision"] != revision:
            raise DomainError("STALE_BASELINE", "Draft revision changed")
        if prior["publication_status"] not in ("DRAFT", "UNDER_REVIEW", "APPROVED"):
            raise DomainError(
                "INVALID_TRANSITION",
                "Published/rejected versions cannot be edited; generate a new draft",
            )
        request = prior["source_request"]
        baseline = prior.get("baseline_snapshot")
        report = validate_placements(request, assignments, baseline)
        if not report["passed"]:
            raise DomainError(
                "OUTPUT_VALIDATION_FAILED",
                "Manual edit violates compulsory rules",
                report,
            )
        stats = copy.deepcopy(prior["solver"])
        stats.update(
            status="MANUALLY_MODIFIED", proof=[], canonicalization_complete=False
        )
        result = format_result(
            request,
            {a["participant_id"]: a["seat_ids"] for a in assignments},
            stats,
            baseline,
        )
        result.update(
            manually_modified=True,
            solver_status_at_generation=prior["solver_status_at_generation"],
        )
        return self.save(result, actor, predecessor=pid, predecessor_revision=revision)

    def transition(self, pid, action, actor, revision):
        with self.connection() as db:
            plan = self._load(db, pid)
            if plan["validation_revision"] != revision:
                raise DomainError(
                    "STALE_BASELINE", "Exact validated revision is required"
                )
            states = {
                "submit": ({"DRAFT"}, "UNDER_REVIEW"),
                "approve": ({"UNDER_REVIEW"}, "APPROVED"),
                "reject": ({"DRAFT", "UNDER_REVIEW", "APPROVED"}, "REJECTED"),
                "publish": ({"APPROVED"}, "PUBLISHED"),
            }
            if (
                action not in states
                or plan["publication_status"] not in states[action][0]
            ):
                raise DomainError(
                    "INVALID_TRANSITION", "Action is not valid for this plan state"
                )
            check = audit_result(plan)
            if not check["passed"]:
                raise DomainError(
                    "OUTPUT_VALIDATION_FAILED", "Plan failed fresh validation", check
                )
            event = plan["event_id"]
            stamp = now()
            if action == "publish":
                pointer = db.execute(
                    "SELECT published FROM events WHERE id=?", (event,)
                ).fetchone()
                current = pointer["published"] if pointer else None
                if current != plan["expected_published_version_id"]:
                    raise DomainError(
                        "STALE_BASELINE",
                        "Another plan was published; review a new draft against the latest baseline",
                    )
                if current:
                    db.execute(
                        "UPDATE plans SET state='SUPERSEDED' WHERE id=?", (current,)
                    )
                db.execute(
                    "INSERT INTO events(id,published) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET published=excluded.published",
                    (event, pid),
                )
                db.execute(
                    "UPDATE plans SET published_by=?,published_at=? WHERE id=?",
                    (actor, stamp, pid),
                )
            if action == "approve":
                db.execute(
                    "UPDATE plans SET approved_by=?,approved_at=? WHERE id=?",
                    (actor, stamp, pid),
                )
            db.execute("UPDATE plans SET state=? WHERE id=?", (states[action][1], pid))
            db.execute(
                "INSERT INTO audit(event,plan,action,actor,at) VALUES(?,?,?,?,?)",
                (event, pid, action, actor, stamp),
            )
            return self._load(db, pid)

    def history(self, event):
        with self.connection() as db:
            return [
                dict(row)
                for row in db.execute(
                    "SELECT id,state,actor,created,approved_by,published_by FROM plans WHERE event=? ORDER BY rowid DESC",
                    (event,),
                )
            ]


def participant_view(plan, pid):
    if not plan:
        return {
            "status": "unpublished",
            "message": "No published seating plan is available.",
        }
    assignment = next(
        (a for a in plan["assignments"] if a["participant_id"] == pid), None
    )
    # Public geometry includes only this participant's labels/identity. Other occupants are anonymous.
    floor = copy.deepcopy(plan["floor_plan"])
    for row in floor["rows"]:
        for seat in row["seats"]:
            if seat["participant_id"] != pid:
                seat["participant_id"] = None
            seat["display_name"] = None
            seat.pop("tier", None)
    return {
        "status": "published",
        "plan_version_id": plan["plan_version_id"],
        "event_id": plan["event_id"],
        "event_details": copy.deepcopy(
            plan["source_request"].get(
                "event_details",
                {
                    "name": plan.get("case_study", plan["event_id"]),
                    "date": None,
                    "time": None,
                    "timezone": "Asia/Kuala_Lumpur",
                    "venue": None,
                },
            )
        ),
        "floor_plan": floor,
        "assignment": (
            {
                "participant_id": pid,
                "full_name": assignment["full_name"],
                "seat_ids": assignment["seat_ids"],
                "seats": [
                    {
                        key: seat[key]
                        for key in (
                            "seat_id",
                            "row_number",
                            "physical_position",
                            "display_name",
                        )
                    }
                    for seat in assignment["seats"]
                ],
            }
            if assignment
            else None
        ),
    }
