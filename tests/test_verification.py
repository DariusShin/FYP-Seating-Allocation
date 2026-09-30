import copy
import json
import time

import pytest

from seat_solver.production.plan_store import PlanStore
from seat_solver.production.policy import DomainError
from seat_solver.production.production import solve
from seat_solver.production.production_data import generate
from seat_solver.production.service import dispatch
from seat_solver.production.verification import check
from seat_solver.production.workspace import WorkspaceStore, initial_state


@pytest.fixture
def session(tmp_path):
    request = generate(emperor=0, merit=3, bodhi=0)
    request['layout']['row_count'] = 3
    request['layout']['seats'] = [s for s in request['layout']['seats'] if s['row_number'] <= 3]
    request['solver'].update(max_time_seconds=5, num_search_workers=1)
    for p, amount in zip(request['participants'], [5000, 4000, 3000]):
        p['contribution_amount_rm'] = amount
    store = PlanStore(tmp_path / 'review.db')
    plan = store.save(solve(request), 'generator')
    ws = WorkspaceStore(store)
    state = initial_state(plan)
    state['items']['P0001']['seat_ids'] = ['R03-S01']
    state['items']['P0002']['seat_ids'] = ['R02-S01']
    state['items']['P0003']['seat_ids'] = ['R01-S01']
    saved = ws.action(plan['event_id'], 'staff', dict(command='workspace_save', plan_version_id=plan['plan_version_id'], revision=0, state=state))
    def act(command, **fields):
        return ws.action(plan['event_id'], 'reviewer', dict(command=command, plan_version_id=plan['plan_version_id'], revision=saved['revision'], **fields))
    return store, ws, plan, state, saved, act


def test_entry_gate_and_unreviewed_publication(session):
    _, _, plan, state, _, act = session
    with pytest.raises(DomainError, match='Submit the saved'):
        act('workspace_publish')
    state['items']['P0001']['seat_ids'] = []
    with pytest.raises(DomainError, match='Assign every paid'):
        check(plan, state)
    with pytest.raises(DomainError, match='Submit the saved'):
        act('workspace_check', state=state)


def test_ack_persistence_revocation_and_atomic_publication(session):
    store, ws, plan, state, saved, act = session
    report = act('workspace_check')
    red = [f for f in report['findings'] if f['severity'] == 'RED']
    assert len(red) == 3
    with pytest.raises(DomainError, match='blocking safeguard'):
        act('workspace_publish', state=initial_state(plan), acknowledgements=[f['finding_id'] for f in red])
    assert store.published(plan['event_id']) is None
    for f in red:
        act('workspace_ack', finding_id=f['finding_id'], status='ACKED', note='Staff decision')
    loaded = WorkspaceStore(store).load(plan['event_id'])
    assert loaded['review']['summary']['open_blocking'] == 0
    assert loaded['review']['summary']['open_advisory'] > 0
    act('workspace_ack', finding_id=red[0]['finding_id'], status='OPEN')
    with pytest.raises(DomainError, match='blocking safeguard'):
        act('workspace_publish')
    act('workspace_ack', finding_id=red[0]['finding_id'], status='ACKED', note='Approved again')
    published = act('workspace_publish')
    audit = published['base']['safeguard_review']
    assert audit['review_status'] == 'PASSED'
    assert audit['acknowledgements'][red[0]['finding_id']]['actor'] == 'reviewer'
    assert audit['acknowledgements'][red[0]['finding_id']]['note'] == 'Approved again'
    venue = dispatch({'command': 'venue', 'event_id': plan['event_id']}, store)
    public = dispatch({'command': 'public', 'event_id': plan['event_id'], 'participant_id': 'P0001'}, store)
    assert 'Staff decision' not in json.dumps([venue, public])
    assert 'safeguard_review' not in venue and 'safeguard_review' not in public
    with pytest.raises(DomainError, match='newer draft'):
        act('workspace_ack', finding_id=red[0]['finding_id'], status='OPEN')
    revised = ws.action(plan['event_id'], 'staff', dict(command='workspace_save', plan_version_id=published['base']['plan_version_id'], revision=published['revision'], state=state))
    assert revised['review']['review_status'] == 'NOT_CHECKED'


def test_feedback_is_read_only_and_resolved_pairs_return_on_undo(session):
    _, ws, plan, state, _, act = session
    first = act('workspace_check')
    fid = next(f['finding_id'] for f in first['findings'] if f['rule_id'] == 'C13')
    act('workspace_ack', finding_id=fid, status='ACKED')
    before = ws.load(plan['event_id'])
    fixed = initial_state(plan)
    feedback = act('workspace_check', state=fixed)
    assert feedback['summary']['resolved'] > 0
    assert ws.load(plan['event_id']) == before
    undone = act('workspace_check', state=state)
    assert next(f for f in undone['findings'] if f['finding_id'] == fid)['status'] == 'ACKED'
    assert undone['summary']['open_blocking'] == 2


def test_invalid_and_cross_event_ack_rejected(session):
    _, ws, plan, _, saved, act = session
    act('workspace_check')
    for kwargs in [dict(finding_id='forged', status='ACKED'), dict(finding_id='x', status='PASSED'), dict(finding_id='x', status='ACKED', note=7)]:
        with pytest.raises(DomainError): act('workspace_ack', **kwargs)
    with pytest.raises(DomainError, match='Plan not in this event'):
        ws.action('other-event', 'staff', dict(command='workspace_check', plan_version_id=plan['plan_version_id'], revision=saved['revision']))


def test_publish_recomputes_after_edit_even_if_status_was_passed(session):
    store, ws, plan, state, saved, act = session
    act('workspace_check')
    with store.connection() as db:
        review = ws.review(db, plan['event_id'], plan['plan_version_id'])
        review['review_status'] = 'PASSED'
        review['summary']['open_blocking'] = 0
        ws.save_review(db, plan['event_id'], plan['plan_version_id'], review)
    with pytest.raises(DomainError, match='blocking safeguard'):
        act('workspace_publish')


def test_hint_candidates_preserve_integrity_and_fix_ordering(session):
    _, _, plan, state, _, act = session
    report = act('workspace_check')
    for finding in report['findings']:
        actor = finding['resolution_hint']['actor_participant_id']
        assert finding['resolution_hint']['message']
        assert len(finding['resolution_hint']['swap_candidates']) <= 5
        for candidate in finding['resolution_hint']['swap_candidates']:
            trial = copy.deepcopy(state)
            other = candidate['participant_id']
            trial['items'][actor]['seat_ids'], trial['items'][other]['seat_ids'] = trial['items'][other]['seat_ids'], trial['items'][actor]['seat_ids']
            checked = check(plan, trial)
            assert not any(f['severity'] == 'RED' and any(p['participant_id'] in (actor, other) for p in f['participants']) for f in checked['findings'])


def test_production_sized_check_latency_and_registration_group_bound():
    request = generate()
    # Deliberately reversed rank placements produce many pairs without spending
    # solver time; the check still enforces structural validity independently.
    from seat_solver.production.production_scoring import options
    plan = {'source_request': request}
    occupied = set()
    items = {}
    for p in request['participants']:
        choices = list(reversed(options(request, p)))
        choice = next(o for o in choices if not occupied.intersection(s['seat_id'] for s in o))
        ids = [s['seat_id'] for s in choice]
        occupied.update(ids)
        items[p['participant_id']] = dict(seat_ids=ids, display_names=[p['full_name']] * len(ids), note='', dock_reason='', previous_seat_ids=[], changed_at=None)
    state = {'participants': request['participants'], 'items': items}
    start = time.perf_counter()
    report = check(plan, state)
    elapsed = time.perf_counter() - start
    assert elapsed < 1, elapsed
    assert len({f['resolution_hint']['actor_participant_id'] for f in report['findings']}) <= len(request['participants'])
