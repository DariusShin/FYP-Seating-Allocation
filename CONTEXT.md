# Seating allocation

Language for discussing PJKIT registration allocation and seating preferences.

## Language

**Registration unit**:
A registration receiving its complete seating entitlement. An Emperor registration is one unit entitled to two seats and counts as one affected unit when its seat bundle changes.
_Avoid_: Person, when counting registrations or affected registration units.

**Validated seating allocation**:
A complete allocation in which every eligible registration receives its full seating entitlement and all compulsory seating rules pass independent validation. It is acceptable for staff use without a proof that its seating-preference penalty is minimum; preference optimality is reported separately.
_Avoid_: Optimal allocation, when only completeness and compulsory-rule validity have been established.

**Physical seat demand**:
The number of seats required by all registration entitlements in an event: two per Emperor registration and one per Merit or Bodhi registration.
_Avoid_: Participant count, when referring to occupied physical seats.

**Occupancy family**:
A group of seating scenarios sharing tier counts and physical seat demand, with different declared profile or accessibility patterns. Occupancy is the share of available physical seats demanded, rather than the share of registrations in a contribution tier.
_Avoid_: Extra full, extremely full.

**High occupancy family**:
The benchmark family with 62 Emperor, 31 Merit and 24 Bodhi registrations: 117 registration units requiring 179 of 232 seats.

**Near capacity family**:
The benchmark family with 73 Emperor, 37 Merit and 29 Bodhi registrations: 139 registration units requiring 212 of 232 seats.

**Full capacity family**:
The benchmark family with 80 Emperor, 40 Merit and 32 Bodhi registrations: 152 registration units requiring all 232 seats.

**Emperor-heavy scenario**:
The distinct mixed-profile scenario with 99 Emperor, 19 Merit and 13 Bodhi registrations: 131 registration units requiring 230 seats. Its Emperor share describes registrations, not physical seat occupancy.

**Matched solver case**:
One event under one preference configuration, shared by all compared methods. Related patterns and accessibility derivatives are constructed scenarios rather than independent samples of real events.

**Seating preference priority**:
The relative importance of a seating preference in a compensatory trade-off: a higher-ranked preference has greater influence per comparable penalty unit, but improvements in other preferences may outweigh it.
_Avoid_: Absolute preference priority, guaranteed first-preference satisfaction.

**Enabled seating preference**:
A seating decision factor that staff have selected for consideration in the allocation. A disabled preference contributes no preference penalty to the allocation decision; disabling it does not remove related compulsory seating rules.
_Avoid_: Optional hard constraint.

**Seating preference ranking**:
The order of relative importance that staff assign to the enabled seating preferences. Staff may change this order before regenerating a seating map.
_Avoid_: Participant ranking, when referring to the ordering of preference factors.

**Preference-free regeneration**:
A regenerated seating allocation made without considering any optional seating preference because staff have disabled them all. Compulsory allocation rules still apply.
_Avoid_: Unconstrained allocation.

**Absence movement priority**:
The strict ordering of repair objectives: first minimize moved registration units, then movement distance, then seating-preference penalties. This differs from the compensatory priority among seating preferences.
_Avoid_: Treating movement and seating preferences as interchangeable trade-offs.
