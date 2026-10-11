# Seating allocation

Language for discussing PJKIT registration allocation and seating preferences.

## Language

**Registration unit**:
A registration receiving its complete seating entitlement. An Emperor registration is one unit entitled to two seats and counts as one affected unit when its seat bundle changes.
_Avoid_: Person, when counting registrations or affected registration units.

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
