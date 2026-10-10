"""Absence repair, shared attendance, saved baselines and publication isolation."""
import copy
import itertools

import pytest
from test_production import tiny

from seat_solver.production.absence_repair import movement, repair
from seat_solver.production.plan_store import PlanStore, participant_view
from seat_solver.production.policy import DomainError, policy
from seat_solver.production.production import solve
from seat_solver.production.production_data import generate
from seat_solver.production.production_scoring import candidate_cost, eligible
from seat_solver.production.production_validator import audit_result, validate_placements
from seat_solver.production.service import dispatch
from seat_solver.production.workspace import WorkspaceStore, initial_state


def absent(state, pid):
    state = copy.deepcopy(state)
    item = state['items'][pid]
    item.update(attendance_status='ABSENT', previous_seat_ids=item['seat_ids'], seat_ids=[], dock_reason='Marked absent')
    return state


def saved_session(tmp_path, request=None):
    store = PlanStore(tmp_path / 'absence.db')
    plan = store.save(solve(request or tiny(4)), 'generator')
    ws = WorkspaceStore(store)
    return store, ws, plan


def save(ws, plan, state, revision=0):
    return ws.action(plan['event_id'], 'staff', dict(command='workspace_save', plan_version_id=plan['plan_version_id'], revision=revision, state=state))


def command(saved, **kwargs):
    return dict(command='solve', event_id=saved['base']['event_id'], generation_mode='REPAIR_ABSENCE',
                plan_version_id=saved['base']['plan_version_id'], revision=saved['revision'], **kwargs)


def test_repair_uses_separate_path_and_matches_exhaustive_lexicographic_oracle(tmp_path, monkeypatch):
    store, ws, plan = saved_session(tmp_path)
    state = initial_state(plan)
    cells = {s['seat_id']: s for s in plan['source_request']['layout']['seats']}
    front = min(state['items'], key=lambda pid: cells[state['items'][pid]['seat_ids'][0]]['priority_rank'])
    saved = save(ws, plan, absent(state, front))
    from seat_solver.production import service
    monkeypatch.setattr(service, 'solve', lambda *_: pytest.fail('Generation solver must not run for repair'))
    result = dispatch(command(saved), store)
    assert audit_result(result)['passed'], result
    assert result['repair_summary']['moved_registrations'] == 1
    request = result['source_request']
    people = eligible(request)
    target = sorted(cells.values(), key=lambda s: s['priority_rank'])[:len(people)]
    def score(placements):
        ms = [movement(ids, saved['state']['items'][pid]['seat_ids'], cells) for pid, ids in placements.items()]
        return (sum(m for m, _ in ms), sum(d for _, d in ms),
                sum(candidate_cost(request, policy(), p, [cells[s] for s in placements[p['participant_id']]])['weighted']['total'] for p in people))
    oracle = min(score({p['participant_id']: [s['seat_id']] for p, s in zip(people, order)}) for order in itertools.permutations(target))
    actual = {a['participant_id']: a['seat_ids'] for a in result['assignments']}
    assert score(actual) == oracle
    assert len(result['assignments']) == 3
    assert result['operations'][front]['attendance_status'] == 'ABSENT'
    assert store.published(plan['event_id']) is None
    assert ws.load(plan['event_id'])['revision'] == saved['revision']
    bad = copy.deepcopy(result)
    bad['repair_summary']['moved_registrations'] += 1
    assert not audit_result(bad)['passed']


def test_emperor_absence_keeps_both_names_and_restoration_requires_complete_pair(tmp_path):
    store, ws, plan = saved_session(tmp_path, tiny(2, 'EMPEROR'))
    state = initial_state(plan)
    pid = plan['assignments'][0]['participant_id']
    saved = save(ws, plan, absent(state, pid))
    result = dispatch(command(saved), store)
    assert audit_result(result)['passed']
    opened = ws.open(plan['event_id'], 'staff', result['plan_version_id'])
    item = opened['state']['items'][pid]
    assert item['attendance_status'] == 'ABSENT'
    assert item['seat_ids'] == []
    assert len(item['display_names']) == 2
    attempted = copy.deepcopy(opened['state'])
    attempted['items'][pid]['seat_ids'] = state['items'][pid]['seat_ids']
    with pytest.raises(DomainError, match='Restore attendance'):
        save(ws, result, attempted, opened['revision'])
    attempted['items'][pid]['attendance_status'] = 'PRESENT'
    attempted['items'][pid]['seat_ids'] = ['R01-P01']
    with pytest.raises(DomainError):
        save(ws, result, attempted, opened['revision'])


def test_expands_only_on_infeasibility_and_keeps_outside_registrations_fixed(tmp_path):
    request = generate(emperor=0, merit=50, bodhi=0)
    request['layout']['row_count'] = 4
    request['layout']['seats'] = [s for s in request['layout']['seats'] if s['row_number'] <= 4]
    request['solver'].update(max_time_seconds=15, canonicalize=False)
    store, ws, plan = saved_session(tmp_path, request)
    state = initial_state(plan)
    cells = {s['seat_id']: s for s in request['layout']['seats']}
    pid = next(pid for pid, m in state['items'].items() if cells[m['seat_ids'][0]]['row_number'] == 3)
    saved = save(ws, plan, absent(state, pid))
    result = dispatch(command(saved), store)
    assert result['status'] == 'success', result
    assert audit_result(result)['passed']
    assert result['repair_summary']['attempts'][0] == {'rows': [3], 'status': 'INFEASIBLE'}
    assert result['repair_summary']['scope_rows'] == [2, 3, 4]
    for a in result['assignments']:
        old = state['items'][a['participant_id']]['seat_ids']
        if cells[old[0]]['row_number'] == 1:
            assert set(a['seat_ids']) == set(old)


def test_absent_dock_allows_review_publication_but_temporary_dock_blocks(tmp_path):
    store, ws, plan = saved_session(tmp_path)
    pid = plan['assignments'][-1]['participant_id']
    saved = save(ws, plan, absent(initial_state(plan), pid))
    args = dict(event_id=plan['event_id'], plan_version_id=plan['plan_version_id'], revision=saved['revision'])
    dispatch(dict(command='workspace_check', **args), store)
    published = dispatch(dict(command='workspace_publish', **args), store)
    assert published['base']['publication_status'] == 'PUBLISHED'
    assert participant_view(published['base'], pid)['assignment'] is None
    assert published['base']['operations'][pid]['attendance_status'] == 'ABSENT'
    next_state = copy.deepcopy(published['state'])
    other = next(p for p in next_state['items'] if p != pid)
    next_state['items'][other]['seat_ids'] = []
    held = save(ws, published['base'], next_state, published['revision'])
    with pytest.raises(DomainError, match='every present paid'):
        ws.action(plan['event_id'], 'staff', dict(command='workspace_check', plan_version_id=published['base']['plan_version_id'], revision=held['revision']))


def test_attendance_is_shared_across_versions_and_regeneration(tmp_path):
    store, ws, plan = saved_session(tmp_path)
    another = store.save(solve(tiny(4)), 'generator')
    pid = plan['assignments'][0]['participant_id']
    saved = save(ws, plan, absent(initial_state(plan), pid))
    opened = ws.open(plan['event_id'], 'staff', another['plan_version_id'])
    assert opened['state']['items'][pid]['attendance_status'] == 'ABSENT'
    assert opened['state']['items'][pid]['seat_ids'] == []
    result = dispatch(dict(command='solve', event_id=plan['event_id'], generation_mode='REGENERATE_DRAFT'), store)
    assert pid not in {a['participant_id'] for a in result['assignments']}
    assert result['operations'][pid]['attendance_status'] == 'ABSENT'
    assert result['source_request']['participants'] == plan['source_request']['participants']
    restored = copy.deepcopy(opened['state'])
    restored['items'][pid]['attendance_status'] = 'PRESENT'
    restored['items'][pid]['seat_ids'] = initial_state(another)['items'][pid]['seat_ids']
    save(ws, another, restored, opened['revision'])
    reopened = ws.open(plan['event_id'], 'staff', plan['plan_version_id'])
    assert reopened['state']['items'][pid]['attendance_status'] == 'PRESENT'
    assert reopened['state']['items'][pid]['seat_ids'] == []  # no invented old placement
    with store.connection() as db:
        assert db.execute('SELECT status FROM event_attendance WHERE event=? AND participant=?', (plan['event_id'], pid)).fetchone()['status'] == 'PRESENT'


def test_stale_repair_and_adoption_are_rejected(tmp_path):
    store, ws, plan = saved_session(tmp_path)
    saved = save(ws, plan, absent(initial_state(plan), plan['assignments'][0]['participant_id']))
    result = dispatch(command(saved), store)
    newer = save(ws, plan, saved['state'], saved['revision'])
    with pytest.raises(DomainError, match='Reload'):
        dispatch(command(saved), store)
    with pytest.raises(DomainError, match='saved map changed'):
        ws.open(plan['event_id'], 'staff', result['plan_version_id'])
    with pytest.raises(DomainError, match='candidate discarded'):
        store.save(result, 'staff', workspace_guard={'plan_version_id': plan['plan_version_id'], 'revision': saved['revision']})
    assert ws.load(plan['event_id'])['revision'] == newer['revision']


def test_temporary_dock_and_no_absence_cannot_trigger_repair(tmp_path):
    _, _, plan = saved_session(tmp_path)
    state = initial_state(plan)
    with pytest.raises(DomainError, match='absent registration'):
        repair(plan, state)
    state = absent(state, plan['assignments'][0]['participant_id'])
    state['items'][plan['assignments'][1]['participant_id']]['seat_ids'] = []
    with pytest.raises(DomainError, match='temporary dock'):
        repair(plan, state)


def test_all_absent_and_already_packed_absence_need_no_movement(tmp_path):
    _, _, plan = saved_session(tmp_path)
    state = initial_state(plan)
    for pid in list(state['items']):
        state = absent(state, pid)
    result = repair(plan, state)
    assert audit_result(result)['passed']
    assert result['assignments'] == []
    assert result['repair_summary']['moved_registrations'] == 0


def test_search_without_any_solution_does_not_change_workspace(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from seat_solver.production import absence_repair
    store, ws, plan = saved_session(tmp_path)
    cells = {s['seat_id']: s for s in plan['source_request']['layout']['seats']}
    state = initial_state(plan)
    front = min(state['items'], key=lambda pid: cells[state['items'][pid]['seat_ids'][0]]['priority_rank'])
    saved = save(ws, plan, absent(state, front))
    before = store.history(plan['event_id'])
    class UnknownSolver:
        parameters = SimpleNamespace()
        def Solve(self, model):
            return absence_repair.cp_model.UNKNOWN
    monkeypatch.setattr(absence_repair.cp_model, 'CpSolver', UnknownSolver)
    result = dispatch(command(saved), store)
    assert result['error']['code'] == 'REPAIR_NO_SOLUTION'
    assert store.history(plan['event_id']) == before
    assert ws.load(plan['event_id'])['state'] == saved['state']
    assert store.published(plan['event_id']) is None


def test_regeneration_preserves_saved_display_edits_and_absent_names(tmp_path):
    store, ws, plan = saved_session(tmp_path)
    state = initial_state(plan)
    pid = plan['assignments'][0]['participant_id']
    other = plan['assignments'][1]['participant_id']
    state['items'][pid]['display_names'] = ['Absent display']
    state['items'][other]['display_names'] = ['Present display']
    saved = save(ws, plan, absent(state, pid))
    result = dispatch(dict(command='solve', event_id=plan['event_id'], generation_mode='REGENERATE_DRAFT'), store)
    assert audit_result(result)['passed']
    assert result['operations'][pid]['display_names'] == ['Absent display']
    assignment = next(a for a in result['assignments'] if a['participant_id'] == other)
    assert assignment['seats'][0]['display_name'] == 'Present display'
    opened = ws.open(plan['event_id'], 'staff', result['plan_version_id'])
    assert opened['state']['items'][pid]['display_names'] == ['Absent display']


def test_legacy_plan_publication_cannot_ignore_new_event_attendance(tmp_path):
    store, ws, plan = saved_session(tmp_path)
    store.transition(plan['plan_version_id'], 'submit', 'staff', plan['validation_revision'])
    store.transition(plan['plan_version_id'], 'approve', 'staff', plan['validation_revision'])
    save(ws, plan, absent(initial_state(plan), plan['assignments'][0]['participant_id']))
    with pytest.raises(DomainError, match='Event attendance changed'):
        store.transition(plan['plan_version_id'], 'publish', 'staff', plan['validation_revision'])
    assert store.published(plan['event_id']) is None


@pytest.mark.parametrize('stop_stage', [1, 2, 3])
def test_feasible_repair_is_saved_without_requiring_optimality(tmp_path, monkeypatch, stop_stage):
    from seat_solver.production import absence_repair
    store, ws, plan = saved_session(tmp_path)
    cells = {s['seat_id']: s for s in plan['source_request']['layout']['seats']}
    state = initial_state(plan)
    front = min(state['items'], key=lambda pid: cells[state['items'][pid]['seat_ids'][0]]['priority_rank'])
    saved = save(ws, plan, absent(state, front))
    real_solver = absence_repair.cp_model.CpSolver
    calls = []

    class FeasibleSolver:
        def __init__(self):
            self.engine = real_solver()
            self.parameters = self.engine.parameters

        def Solve(self, model):
            calls.append(model)
            status = self.engine.Solve(model)
            assert status == absence_repair.cp_model.OPTIMAL
            return absence_repair.cp_model.FEASIBLE if len(calls) == stop_stage else status

        def __getattr__(self, name):
            return getattr(self.engine, name)

    monkeypatch.setattr(absence_repair.cp_model, 'CpSolver', FeasibleSolver)
    result = dispatch(command(saved), store)
    assert result['status'] == 'success', result
    assert result['solver']['status'] == 'FEASIBLE'
    assert result['solver_status_at_generation'] == 'FEASIBLE'
    assert result['repair_summary']['optimality_proven'] is False
    assert result['solver']['proof'][-1]['status'] == 'FEASIBLE'
    assert len(calls) == stop_stage  # Never optimize lower terms after an unproven stage.
    assert audit_result(result)['passed']
    assert ws.open(plan['event_id'], 'staff', result['plan_version_id'])['base']['plan_version_id'] == result['plan_version_id']
    assert store.published(plan['event_id']) is None


@pytest.mark.parametrize('stop_stage', [2, 3])
def test_later_stage_without_solution_retains_earlier_valid_incumbent(tmp_path, monkeypatch, stop_stage):
    from seat_solver.production import absence_repair
    store, ws, plan = saved_session(tmp_path)
    cells = {s['seat_id']: s for s in plan['source_request']['layout']['seats']}
    state = initial_state(plan)
    front = min(state['items'], key=lambda pid: cells[state['items'][pid]['seat_ids'][0]]['priority_rank'])
    saved = save(ws, plan, absent(state, front))
    real_solver = absence_repair.cp_model.CpSolver
    calls = []

    class InterruptedSolver:
        def __init__(self):
            self.engine = real_solver()
            self.parameters = self.engine.parameters

        def Solve(self, model):
            calls.append(model)
            if len(calls) == stop_stage:
                return absence_repair.cp_model.UNKNOWN
            return self.engine.Solve(model)

        def __getattr__(self, name):
            return getattr(self.engine, name)

    monkeypatch.setattr(absence_repair.cp_model, 'CpSolver', InterruptedSolver)
    result = dispatch(command(saved), store)
    assert result['status'] == 'success', result
    assert result['solver']['status'] == 'FEASIBLE'
    assert len(result['solver']['proof']) == stop_stage - 1
    assert result['repair_summary']['optimality_proven'] is False
    assert audit_result(result)['passed']
    assert result['repair_summary']['moved_registrations'] == 1
    assert store.published(plan['event_id']) is None


def test_deadline_after_first_solution_returns_the_valid_incumbent(tmp_path, monkeypatch):
    from seat_solver.production import absence_repair
    store, ws, plan = saved_session(tmp_path)
    cells = {s['seat_id']: s for s in plan['source_request']['layout']['seats']}
    state = initial_state(plan)
    front = min(state['items'], key=lambda pid: cells[state['items'][pid]['seat_ids'][0]]['priority_rank'])
    saved = save(ws, plan, absent(state, front))
    real_solver = absence_repair.cp_model.CpSolver
    real_clock = absence_repair.time.perf_counter
    expired = False
    calls = []

    class DeadlineSolver:
        def __init__(self):
            self.engine = real_solver()
            self.parameters = self.engine.parameters

        def Solve(self, model):
            nonlocal expired
            calls.append(model)
            status = self.engine.Solve(model)
            expired = True
            return status

        def __getattr__(self, name):
            return getattr(self.engine, name)

    monkeypatch.setattr(absence_repair.cp_model, 'CpSolver', DeadlineSolver)
    monkeypatch.setattr(absence_repair.time, 'perf_counter', lambda: real_clock() + (60 if expired else 0))
    result = dispatch(command(saved), store)
    assert result['status'] == 'success', result
    assert result['solver']['status'] == 'FEASIBLE'
    assert result['repair_summary']['stopped_stage'] == 'movement_distance_doubled'
    assert result['solver']['proof'][0]['status'] == 'OPTIMAL'
    assert len(calls) == 1
    assert audit_result(result)['passed']
    assert store.published(plan['event_id']) is None
