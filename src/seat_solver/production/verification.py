"""Explainable safeguards over physical placements; no solver or browser trust."""
from collections import Counter
from urllib.parse import quote

from seat_solver.production.policy import DomainError, ELIGIBLE, TIERS
from seat_solver.production.production_scoring import options, packing_pairs


def finding_id(rule, pair, gaps):
    return ':'.join(quote(part, safe='') for part in [rule, *sorted(pair), *gaps])


def detect(request, state):
    """Rule detection shared by review and history, including incomplete dock states."""
    seats = {s['seat_id']: s for s in request['layout']['seats']}
    people = {p['participant_id']: p for p in state['participants']
              if p['registration_status'] in ELIGIBLE and state['items'][p['participant_id']]['seat_ids']}
    placed = {pid: state['items'][pid]['seat_ids'] for pid in people}
    rows = {pid: seats[ids[0]]['row_number'] for pid, ids in placed.items()}
    def order(sid):
        s = seats[sid]
        return (s['row_number'], s['priority_rank'])
    def violations(a, b, placements):
        p, q = people[a], people[b]
        pi, qi = TIERS.index(p['contribution_tier']), TIERS.index(q['contribution_tier'])
        if pi != qi:
            high, low = (a, b) if pi < qi else (b, a)
            return 'C12' if max(map(order, placements[high])) >= min(map(order, placements[low])) else None
        rp, rq = seats[placements[a][0]]['row_number'], seats[placements[b][0]]['row_number']
        return 'C13' if (p['contribution_amount_rm'] - q['contribution_amount_rm']) * (rp - rq) > 0 else None
    raw = []
    ids = sorted(people)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            rule = violations(a, b, placed)
            if rule:
                raw.append((rule, [a, b], []))
    occupied = {sid for ss in placed.values() for sid in ss}
    owners = {sid: pid for pid, ss in placed.items() for sid in ss}
    last = max(rows.values(), default=0)
    for sid, seat in seats.items():
        if not seat['is_blocked'] and sid not in occupied and seat['row_number'] < last:
            candidates = [p for p in ids if rows[p] > seat['row_number']]
            actor = min(candidates, key=lambda p: (rows[p], p))
            raw.append(('C15', [actor], [sid]))
    for inner, outer in packing_pairs(request['layout']):
        if outer in occupied and inner not in occupied:
            raw.append(('C16', [owners[outer]], [inner]))
    return raw, violations


def check(plan, state, previous=None):
    from seat_solver.production.workspace import validate_state

    request = validate_state(plan, state)
    previous = previous or {}
    seats = {s['seat_id']: s for s in request['layout']['seats']}
    people = {p['participant_id']: p for p in state['participants'] if p['registration_status'] in ELIGIBLE}
    placed = {pid: state['items'][pid]['seat_ids'] for pid in people}
    if any(not ids for ids in placed.values()):
        raise DomainError('INVALID_INPUT', 'Assign every paid registration before review or publication; attendance does not remove paid seats.')
    rows = {pid: seats[ids[0]]['row_number'] for pid, ids in placed.items()}
    raw, violations = detect(request, state)
    occupied = {sid for ss in placed.values() for sid in ss}
    ids = sorted(people)
    counts = Counter(pid for _, pair, _ in raw for pid in pair)
    valid = {pid: {tuple(sorted(s['seat_id'] for s in option)) for option in options(request, p)} for pid, p in people.items()}
    def detail(pid):
        p = people[pid]
        return {k: p[k] for k in ('participant_id', 'contribution_tier', 'contribution_amount_rm')} | {
            'display_name': state['items'][pid]['display_names'][0], 'seat_ids': placed[pid], 'row_number': rows[pid]}
    hints = {}
    findings = []
    acks = previous.get('acknowledgements', {})
    seen = previous.get('seen', {})
    for rule, pair, gaps in raw:
        # Stable pair IDs; gap findings also identify their physical gap so an
        # acknowledgement never silently suppresses a newly created gap.
        fid = finding_id(rule, pair, gaps)
        if rule == 'C12':
            actor = min(pair, key=lambda p: TIERS.index(people[p]['contribution_tier']))
        elif rule == 'C13':
            actor = max(pair, key=lambda p: people[p]['contribution_amount_rm'])
        else:
            actor = pair[0]
        target = min([rows[p] for p in pair] + [seats[s]['row_number'] for s in gaps])
        key = (actor, target, rule)
        if key not in hints:
            candidates = sorted((p for p in ids if p != actor
                and people[p]['contribution_tier'] == people[actor]['contribution_tier']
                and people[p]['contribution_amount_rm'] <= people[actor]['contribution_amount_rm']
                and rows[p] < rows[actor]), key=lambda p: (rows[actor] - rows[p], counts[p], p))
            clean = []
            for candidate in candidates:
                if tuple(sorted(placed[candidate])) not in valid[actor] or tuple(sorted(placed[actor])) not in valid[candidate]:
                    continue
                trial = placed | {actor: placed[candidate], candidate: placed[actor]}
                # Reject candidates with any remaining ordering conflict involving
                # either moved registration. Unrelated existing issues may remain.
                if any(violations(a, b, trial) for a in (actor, candidate) for b in ids if a != b):
                    continue
                clean.append(detail(candidate))
                if len(clean) == 5:
                    break
            free = [option for option in valid[actor] if not occupied.intersection(option)
                    and seats[option[0]]['row_number'] <= target]
            action = 'SWAP_WITH' if clean else 'MOVE_FORWARD' if free else 'FREE_SEAT'
            name = detail(actor)['display_name']
            message = f'Move {name} forward to row {target}'
            if clean:
                message += f", or swap with {clean[0]['display_name']} (row {clean[0]['row_number']})."
            elif free:
                message += '.'
            else:
                message += ' (requires freeing a suitable seat).'
            hints[key] = {'actor_participant_id': actor, 'action': action, 'target_rows': [target],
                          'swap_candidates': clean, 'message': message, 'locked_conflict': False}
        findings.append({'finding_id': fid, 'rule_id': rule, 'severity': 'RED' if rule in ('C12', 'C13') else 'YELLOW',
            'participants': [detail(p) for p in pair], 'involved_seat_ids': sorted({s for p in pair for s in placed[p]} | set(gaps)),
            'resolution_hint': hints[key], 'status': 'ACKED' if acks.get(fid, {}).get('status') == 'ACKED' else 'OPEN',
            'is_new': bool(seen) and fid not in seen})
    findings.sort(key=lambda f: (f['severity'] != 'RED', min(p['row_number'] for p in f['participants']), f['finding_id']))
    current = {f['finding_id'] for f in findings}
    summary = {'open_blocking': sum(f['severity'] == 'RED' and f['status'] == 'OPEN' for f in findings),
               'open_advisory': sum(f['severity'] == 'YELLOW' and f['status'] == 'OPEN' for f in findings),
               'acked': sum(f['status'] == 'ACKED' for f in findings), 'resolved': len(set(seen) - current)}
    return {'review_status': 'IN_PROGRESS', 'findings': findings, 'summary': summary,
            'acknowledgements': acks, 'seen': seen | {f['finding_id']: f for f in findings}}


def attribute_history(plan, state, findings, context):
    """Untrusted, optional display context. Never changes authoritative findings."""
    import copy
    from seat_solver.production.workspace import validate_state, validate_items

    fallback = {'groups': [], 'message': 'Local edit history is unavailable; showing all safeguard findings.'}
    if context is None:
        return fallback
    try:
        if not isinstance(context, dict) or context.get('schema_version') != 1:
            raise ValueError('Unsupported history format')
        edits = context['edits']
        if not isinstance(edits, list):
            raise ValueError('Invalid edit list')
        if len(edits) > 500:
            return {**fallback, 'message': 'This branch exceeds the 500-edit analysis limit. All edits remain in local history; showing ordinary safeguard findings.'}
        current = copy.deepcopy(context['baseline'])
        request = validate_state(plan, current)
        valid_options = {p['participant_id']: {tuple(sorted(s['seat_id'] for s in option))
                         for option in options(request, p)} for p in request['participants']}
        def detected(value):
            return {finding_id(*raw) for raw in detect(request, value)[0]}
        previous = detected(current)
        introduced = {}
        operations = {}
        for edit in edits:
            oid = edit['operation_id']
            if not isinstance(oid, str) or not oid or len(oid) > 100 or oid in operations:
                raise ValueError('Invalid or repeated operation ID')
            changes = edit['changes']
            if not isinstance(changes, list) or not changes or len(changes) > len(current['items']):
                raise ValueError('Invalid operation changes')
            changed = set()
            for change in changes:
                pid = change['participant_id']
                if pid in changed or current['items'][pid] != change['before']:
                    raise ValueError('History is not continuous')
                changed.add(pid)
                current['items'][pid] = copy.deepcopy(change['after'])
            validate_items(request, current["items"], valid_options)
            following = detected(current)
            introduced = {fid: op for fid, op in introduced.items() if fid in following}
            introduced.update({fid: oid for fid in following - previous})
            operations[oid] = edit
            previous = following
        if current != state:
            raise ValueError('History does not match this draft')
        groups = {}
        for finding in findings:
            fid = finding['finding_id']
            oid = introduced.get(fid)
            if not oid:
                continue
            if oid not in groups:
                changes = operations[oid]['changes']
                pids = [c['participant_id'] for c in changes]
                groups[oid] = {'operation_id': oid, 'participant_ids': pids,
                    'finding_ids': [], 'changes': changes,
                    'focus_seat_ids': sorted({sid for pid in pids for sid in state['items'][pid]['seat_ids']})}
            groups[oid]['finding_ids'].append(fid)
        return {'groups': list(groups.values()), 'message': None}
    except (ValueError, KeyError, TypeError, IndexError, DomainError):
        return {**fallback, 'message': 'Local edit history is incomplete or incompatible; showing all safeguard findings.'}
