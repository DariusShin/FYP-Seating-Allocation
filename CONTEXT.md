# PJKIT Seat Allocation

The domain of seating allocation for PJ Kwan Inn Teng (PJKIT) assembly events: matching registered participants to seats in a fixed hall layout under community tier rules, solved as a constraint optimization problem.

## Language

**Tier**:
A participant's contribution class — Emperor, Bodhi, or Merit — seated in that precedence order from the front of the hall. Distinct from *category*, which is a separate participant attribute used for zone-suitability preferences.
_Avoid_: level, class, rank

**Tier band**:
The contiguous block of rows a tier occupies, ordered Emperor → Bodhi → Merit from row 1 backward. Boundaries are not fixed venue zones; they are determined by each event's tier demand. A row belongs to at most one tier: a partially filled last row of a band stays otherwise empty rather than being shared with the next tier.
_Avoid_: tier zone, reserved zone, fixed zone

**Emperor pair**:
The two consecutive side-by-side seats occupied by one Emperor registration. Pair seating is exclusive to the Emperor tier; a pair must be one of the venue's valid within-row position pairs and must never straddle the centre aisle.
_Avoid_: group, double seat, twin seats

**Adjacent guest**:
The companion occupying the second seat of an Emperor pair. Not a primary participant record; when no guest name is given, both seats display the primary participant's name.
_Avoid_: companion, plus-one

**Allocation unit**:
What one registration occupies: one seat for a Bodhi or Merit participant, one Emperor pair for an Emperor participant.

**Physical position**:
A seat's location within its row (column 1–12), used for adjacency and aisle rules.
_Avoid_: conflating with priority rank

**Priority rank**:
A seat's desirability ranking, used for preference alignment. Never used for adjacency.
_Avoid_: conflating with physical position

## Rejected concepts

**Group / group registration**:
Does not exist in this domain. PJKIT confirmed (July 2026) that participants never register as groups and carry no group identifier; there is no group-adjacency rule. The only multi-seat structure is the Emperor pair, which is a hard pairing rule, not a grouping preference.
