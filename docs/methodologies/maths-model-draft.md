# Draft Planning for the Mathematical Model Documentation to be presented in the Final Year Project Dissertation

---

# 1. First: is the mathematical documentation synchronized with the Python implementation?

The short answer is:

**The core production-v4 solver mathematics is mostly synchronized. The historical model is intentionally obsolete. The new safeguard documentation is currently behind the implementation.**

| Source | Status against current `main` | What you should do |
|---|---|---|
| `docs/mathematical_model.md` | **Mostly synchronized with production solver** | Use as the main mathematical reference |
| `docs/mathematical_model.json` | **Very closely synchronized** | Useful as a traceability specification |
| `src/seat_solver/production/production.py` | **Current implementation source of truth** | Main code reference |
| `production_scoring.py` | **Current soft-objective source of truth** | Main cost-function reference |
| `policy.py` + `production_policy.json` | **Current policy/parameter source of truth** | Main input/policy reference |
| `production_validator.py` | **Current independent solver-output audit** | Explain separately from optimization |
| `verification.py` + `workspace.py` | **Newer than the documentation** | Documentation requires updating |
| `docs/solver_mathematical_model.md` | **Historical prototype only** | Do not use as current dissertation model |
| `src/seat_solver/prototype/*` | **Historical v1 reproduction** | Mention only as development history |
| `README.md` safeguard description | **Currently stale** | Do not rely on its “safeguard removed” statement |
| `docs/solver-mathematical-background.md` | **Mixed** | Production sections useful; prototype/movement sections historical |

There are three particularly important inconsistencies you should know.

First, the historical solver documentation still contains the **movement/reallocation penalty**. Production v4 has no such objective and no previous allocation input. Therefore equations such as

\[
c^{mov}_{p,o}
\]

must **not** appear in your final production mathematical model.

Second, the old prototype uses a large main-objective scale plus tie-breaking term. Production v4 **does not use that formulation anymore**. Production solves the weighted business objective first, proves/fixes it, and then performs sequential canonicalization.

Third, your current `verification.py` and `workspace.py` now implement considerably more of Objective 2 than `docs/mathematical_model.md`, `README.md`, and `code_overview.md` currently claim. The current code performs safeguard checking, produces C12/C13/C15/C16 findings, supports acknowledgement, rechecks before publication, and blocks publication when unresolved blocking findings remain.

There is therefore a documentation update you should make before relying on the repository as dissertation evidence.

---

# 2. One terminology correction before learning the mathematics

There are three separate things in your project that are easy to mix together:

| Layer | Question it answers |
|---|---|
| **Mathematical model** | “What constitutes a valid and good seating plan?” |
| **CP-SAT solver** | “How can we computationally search the enormous set of possible plans?” |
| **Independent validator / safeguard** | “After we get or manually modify a plan, is it still valid according to the rules?” |

The Python solver is therefore **not itself the mathematical model**.

The mathematical model is the collection of:

\[
\text{sets} + \text{parameters} + \text{variables} + \text{constraints} + \text{objective}.
\]

Python simply translates those mathematical definitions into OR-Tools instructions.

This distinction is important for your dissertation.

---

# 3. What type of mathematical problem are you solving?

Your seating allocation problem is a **Constraint Optimization Problem**, or COP.

A basic Constraint Satisfaction Problem asks:

> Can I find *any* seating arrangement satisfying every compulsory rule?

A Constraint Optimization Problem asks:

> Among every seating arrangement satisfying the compulsory rules, which one produces the smallest preference penalty?

Mathematically:

\[
\boxed{
\min Z
}
\]

subject to

\[
\boxed{
\text{all hard constraints}
}
\]

where \(Z\) is the total soft-preference penalty.

Your system therefore works conceptually as:

\[
\text{PJKIT business rules}
\rightarrow
\text{mathematical constraints}
\rightarrow
\text{CP-SAT model}
\rightarrow
\text{optimal/feasible assignment}.
\]

Google's official documentation confirms that CP-SAT operates on integer models and returns statuses including `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, `MODEL_INVALID`, and `UNKNOWN`. [Google for Developers](https://developers.google.com/optimization/cp/cp_solver/?utm_source=chatgpt.com)

CP-SAT itself combines constraint programming and SAT-based techniques using Lazy Clause Generation, together with linear-relaxation techniques and multiple search workers. [DROPS](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.CP.2023.3?utm_source=chatgpt.com)

---

# 4. Mathematical notation you need before reading the equations

You should be comfortable with the following notation.

| Symbol | Read as | Meaning |
|---|---|---|
| \(P\) | “set P” | All eligible registrations |
| \(p\in P\) | “p belongs to P” | One particular registration |
| \(S\) | “set S” | All physical seats |
| \(s\in S\) | — | One particular seat |
| \(O_p\) | “option set of p” | Legal seat/pair choices for participant \(p\) |
| \(\forall\) | “for all” | Rule applies to every member |
| \(\exists\) | “there exists” | At least one exists |
| \(\sum\) | “sum” | Add multiple terms together |
| \(\leq\) | — | Less than or equal |
| \(\in\{0,1\}\) | — | Boolean/binary variable |
| \(\min\) | minimum | Smallest value |
| \(\max\) | maximum | Largest value |
| \(|A|\) | cardinality | Number of elements in set \(A\) |
| \(f(x)\) | function | Output produced from input \(x\) |

For example,

\[
p\in P
\]

does **not** mean \(p=P\).

It means:

> \(p\) is one element inside the set \(P\).

If

\[
P=\{P001,P002,P003\}
\]

then \(P002\in P\).

---

# 5. The fundamental sets in production v4

The active model simplifies the old prototype considerably.

Define:

\[
P=\text{set of eligible confirmed registrations}
\]

and

\[
S=\text{set of physical venue seats}.
\]

For the current PJKIT layout:

\[
16\times16=256
\]

physical positions exist.

Twenty-four are structurally blocked:

\[
256-24=232
\]

assignable physical seats.

The important point is that \(P\) contains **confirmed paid registrations**, not physically present attendees.

That is exactly how your new paid-seat requirement appears mathematically.

Attendance does not change:

\[
p\in P.
\]

In Python this starts from:

```python
ELIGIBLE = ("CONFIRMED",)
```

and:

```python
def eligible(request):
    return sorted(
        (
            p for p in request["participants"]
            if p["registration_status"] in ELIGIBLE
        ),
        key=lambda p: p["participant_id"],
    )
```

Therefore:

\[
P=
\{p\mid status(p)=CONFIRMED\}.
\]

Notice something important:

**there is no attendance variable in this expression.**

That is how the new PJKIT requirement is embedded into the actual solver.

---

# 6. Seats have different mathematical attributes

A seat is not merely something like `"R01-S09"`.

For each seat \(s\), production v4 uses several attributes:

\[
row(s)
\]

is the row number,

\[
pos(s)
\]

is its physical position,

\[
\rho(s)
\]

is its priority/desirability rank,

\[
zone(s)
\]

is its zone,

\[
blocked(s)
\]

indicates whether it is unavailable.

This distinction between

\[
pos(s)
\]

and

\[
\rho(s)
\]

is extremely important.

Physical position answers:

> Where physically is the chair?

Priority rank answers:

> How desirable is the chair?

They are **not the same number**.

Your current 16-seat row is ranked:

\[
16,\;15,\;14,\;13,\;12,\;11,\;10,\;9
\quad|\quad
1,\;2,\;3,\;4,\;5,\;6,\;7,\;8
\]

for physical positions

\[
1,2,\dots,16.
\]

The `|` represents the centre aisle.

Therefore physical seat 9 is:

\[
pos(s)=9
\]

but:

\[
\rho(s)=1.
\]

It is the most desirable seat.

---

# 7. Why does production use a row-major seat order?

The solver needs to compare seats not only inside one row, but across different rows and tiers.

Production defines:

\[
order(s)
=
(row(s)-1)\times C+\rho(s)
\]

where:

\[
C=16
\]

is seats per row.

For Row 1 Position 9:

\[
order(s)
=
(1-1)\times16+1
=
1.
\]

For Row 1 Position 10:

\[
order(s)=2.
\]

For Row 2 Position 9:

\[
order(s)
=
(2-1)\times16+1
=
17.
\]

Therefore smaller values mean earlier/more desirable physical placement.

This function solves an important requirement:

> Emperor seats must precede Merit seats even when the tiers share the same physical row.

The comparison can happen at **seat level**, not merely row level.

---

# 8. What is an “option” \(O_p\)?

This is one of the most useful abstractions in production v4.

Instead of creating one mathematical variable for singles and a completely different formulation for Emperor pairs, production treats both as an **allocation option**.

For a Merit participant:

\[
o=\{s\}.
\]

For an Emperor registration:

\[
o=\{s_a,s_b\}.
\]

Then:

\[
O_p
\]

means:

> all legal seating options available to registration \(p\).

For Merit/Bodhi this contains one-seat options.

For Emperor it contains approved two-seat pair options.

This allows production to use one unified assignment variable.

---

# 9. The most important decision variable

Production defines:

\[
\boxed{
z_{p,o}\in\{0,1\}
}
\]

Interpretation:

\[
z_{p,o}
=
\begin{cases}
1 & \text{if participant } p \text{ receives option }o\\
0 & \text{otherwise}
\end{cases}
\]

In the code this is:

```python
v = model.NewBoolVar(f"assign[{pid},{j}]")
```

Suppose P001 has three possible seats:

\[
O_{P001}=
\{S01,S02,S03\}.
\]

Then the solver creates something conceptually equivalent to:

\[
z_{P001,S01}
\]

\[
z_{P001,S02}
\]

\[
z_{P001,S03}.
\]

A final solution might be:

\[
0,\;1,\;0.
\]

That means P001 receives S02.

---

# 10. Hard Constraint C1 — exactly one option per registration

Every confirmed paid registration must receive exactly one allocation option.

Mathematically:

\[
\boxed{
\sum_{o\in O_p}z_{p,o}=1
\qquad
\forall p\in P
}
\]

Read this as:

> For every eligible registration \(p\), add all its option variables. Exactly one must equal 1.

Suppose:

\[
O_p=\{A,B,C\}.
\]

Valid:

\[
0+1+0=1.
\]

Invalid:

\[
0+0+0=0.
\]

Also invalid:

\[
1+1+0=2.
\]

The implementation is literally:

```python
model.AddExactlyOne(vs)
```

This is one of the clearest examples of a direct mapping from mathematics to Python.

---

# 11. How Emperor registrations fit into the same equation

An Emperor registration requires two seats.

The solver does **not** independently choose seat A and then seat B.

Instead, legal pairs are constructed first.

For example:

\[
O_p=
\{
(1,2),
(3,4),
(5,6),
(7,8),
(9,10),
(11,12),
(13,14),
(15,16)
\}
\]

per applicable row, after blocked-seat/accessibility filtering.

Then:

\[
z_{p,(9,10)}=1
\]

means the complete pair is chosen.

Therefore C10 and C11 are largely represented by controlling which options exist.

This is sometimes called **domain restriction** or **modelling by omission**.

---

# 12. Modelling by omission is a major idea in your implementation

Some requirements are not expressed as equations such as:

\[
x\le y.
\]

Instead, illegal choices simply never become variables.

For example, blocked seats are removed in:

```python
available = [
    s for s in layout["seats"]
    if not s["is_blocked"]
]
```

For accessible participants:

```python
if not participant["requires_accessible_seat"]
or s["is_accessible"]
```

And Emperor pairs are generated only from:

```python
layout["approved_pairs"]
```

Therefore an illegal assignment has no \(z_{p,o}\) variable at all.

Mathematically:

\[
o\notin O_p.
\]

This is often much more efficient than creating illegal options and then adding many constraints saying they must equal zero.

---

# 13. Hard Constraint C2 — a physical seat cannot be reused

Define seat occupancy:

\[
occ(s)
=
\sum_{\substack{p\in P\\o\in O_p:s\in o}}
z_{p,o}.
\]

This means:

> Add every assignment variable whose chosen option includes seat \(s\).

Then:

\[
\boxed{
occ(s)\le1
\qquad
\forall s\in S
}
\]

For an Emperor pair, the same assignment variable contributes to **both seats**.

The code does exactly that:

```python
for s in o:
    occupants[s["seat_id"]].append(v)
```

followed by:

```python
model.AddAtMostOne(vs)
```

Therefore two registrations cannot occupy the same physical chair.

---

# 14. The tier-order rule is stronger than just “Emperor rows before Merit rows”

Production v4's C12 is important.

The order is:

\[
EMPEROR
\prec
MERIT
\prec
BODHI.
\]

But rows may be shared.

Therefore merely saying

\[
row(Emperor)\le row(Merit)
\]

is not sufficient.

Imagine both are in Row 5.

The Emperor could accidentally be placed at a worse seat than the Merit participant.

Production therefore compares **seat order**.

For an allocation option \(o\), define:

\[
best(o)=\min_{s\in o} order(s)
\]

and

\[
worst(o)=\max_{s\in o} order(s).
\]

Because only one option is selected:

\[
best(p)
=
\sum_{o\in O_p}
best(o)z_{p,o}
\]

and:

\[
worst(p)
=
\sum_{o\in O_p}
worst(o)z_{p,o}.
\]

For every higher-tier registration \(p\) and lower-tier registration \(q\):

\[
\boxed{
worst(p)<best(q)
}
\]

Conceptually this means:

> even the worst seat belonging to the higher-tier registration must still precede the best seat belonging to the lower-tier registration.

That is stronger and more correct.

---

# 15. Why boundary variables are used for tier ordering

Comparing every Emperor directly against every Merit and every Merit directly against every Bodhi would create many pairwise constraints.

Production instead introduces an integer boundary:

\[
B_t.
\]

For two consecutive non-empty tiers:

\[
H=\text{higher tier}
\]

and

\[
L=\text{lower tier},
\]

the model requires:

\[
worst(p)\le B_t
\qquad
\forall p\in H
\]

and:

\[
best(q)>B_t
\qquad
\forall q\in L.
\]

Therefore automatically:

\[
worst(p)<best(q).
\]

In Python:

```python
boundary = model.NewIntVar(...)
```

then:

```python
model.Add(worstexpr[pid] <= boundary)
```

and:

```python
model.Add(bestexpr[pid] > boundary)
```

This is an auxiliary variable.

It helps encode a global ordering relationship compactly.

---

# 16. Hard Constraint C13 — contribution ordering inside the same tier

Suppose three Merit registrations contributed:

\[
RM5000,\quad RM4000,\quad RM3000.
\]

The higher contributor must not be behind the lower contributor.

If:

\[
c_p>c_q
\]

then:

\[
\boxed{
row(p)\le row(q)
}
\]

Notice the use of:

\[
\le
\]

rather than:

\[
<.
\]

Therefore RM5000 and RM4000 participants may share the same row.

They just cannot have the RM5000 contributor sitting in a later row.

---

# 17. How does the solver know a participant's row?

For option \(o\), define:

\[
row(o).
\]

Because every valid Emperor pair is in one row, this works for both single and pair options.

Then:

\[
\boxed{
row(p)
=
\sum_{o\in O_p}row(o)z_{p,o}
}
\]

Why does that work?

Because exactly one \(z_{p,o}\) equals 1.

Suppose options are in Rows 1, 2 and 3:

\[
z=(0,1,0).
\]

Then:

\[
row(p)
=
1(0)+2(1)+3(0)
=
2.
\]

This is a useful general mathematical technique.

A binary selection variable transforms a property of the selected option into a linear expression.

---

# 18. Contribution ordering also uses boundary variables

Suppose contribution groups within a tier are:

\[
g_1>g_2>g_3.
\]

Production introduces a row boundary between consecutive groups.

For \(g_1\) and \(g_2\):

\[
row(p)\le b_1
\qquad
p\in g_1
\]

\[
row(q)\ge b_1
\qquad
q\in g_2.
\]

Then similarly:

\[
row(q)\le b_2
\]

for \(g_2\), and:

\[
row(r)\ge b_2
\]

for \(g_3\).

By transitivity the full ordering follows.

Equal-contribution participants belong to the same group, so there is no ordering constraint between them.

---

# 19. What `initial_rows()` is doing before the solver really starts searching

This is a particularly important part of your Python code that is easy to misunderstand.

`initial_rows()` is **domain pruning**.

It does not allocate the final seat.

Instead, it determines which rows are mathematically possible for each contribution group.

Registrations are grouped according to:

\[
(tier,\;-contribution).
\]

The negative sign means contributions sort from high to low.

For each group \(G\), required physical seats are:

\[
d(G)=
\begin{cases}
2|G| & EMPEROR\\
|G| & MERIT/BODHI
\end{cases}
\]

The code then takes the corresponding contiguous portion of the globally front-packed seat slots and extracts the rows touched by that interval.

Those become the only rows allowed for that contribution group.

This shrinks the search space dramatically.

Importantly:

**it does not decide exact seats.**

CP-SAT still decides the final options.

---

# 20. Hard Constraint C15 — front-to-back packing

Let total physical seat demand be:

\[
D
=
\sum_{p\in P}\sigma_p
\]

where:

\[
\sigma_p=
\begin{cases}
2 & p\text{ is Emperor}\\
1 & \text{otherwise}.
\end{cases}
\]

For every row \(r\), let:

\[
A_r
=
\text{number of assignable seats in row }r.
\]

The first row gets:

\[
q_1=\min(D,A_1).
\]

Remaining demand:

\[
D_2=D-q_1.
\]

Then:

\[
q_2=\min(D_2,A_2).
\]

Continue until demand becomes zero.

Production then enforces:

\[
\boxed{
\sum_{s\in row(r)}occ(s)=q_r
}
\]

for every row.

This guarantees there cannot be an empty Row 1 followed by occupied Row 2 seats.

The code is:

```python
target = min(demand, len(seats))
demand -= target
model.Add(
    sum(occ[s["seat_id"]] for s in seats)
    == target
)
```

This is the mathematical meaning of **front fill**.

---

# 21. C16 — filling East/Right before West/Left

Production has an even stricter row-packing sequence.

Available seats are ordered:

\[
R9,R10,\dots,R16,
L8,L7,\dots,L1
\]

conceptually, skipping blocked seats.

Call that sequence:

\[
s_1,s_2,\dots,s_m.
\]

Then the prefix rule is:

\[
\boxed{
occ(s_{j+1})\le occ(s_j)
}
\]

for consecutive seats.

Your implementation actually generates all earlier/later comparisons, which is redundant but equivalent for enforcing the prefix.

That means this pattern is impossible:

\[
1,\;1,\;0,\;1.
\]

Because the fourth seat cannot be occupied while the third is empty.

Allowed patterns are:

\[
1,1,1,1,0,0,0,\dots
\]

only.

This is the mathematical reason your generated plan packs continuously from the preferred side.

---

# 22. Accessibility is a hard domain rule

For a participant requiring accessibility:

\[
requiresAccessible(p)=1.
\]

Then:

\[
O_p
\]

contains only accessible options.

For singles:

\[
accessible(s)=1.
\]

For Emperor pairs, the current implementation requires:

\[
accessible(s_a)=accessible(s_b)=1.
\]

Therefore an accessible Emperor must receive an approved pair composed entirely of accessible seats.

Again, the rule is primarily enforced by **candidate construction**, rather than an explicit solver equation.

---

# 23. At this point we have defined the feasible region

Everything so far tells the solver:

> These are the legal seating plans.

Mathematically the set of all valid plans can be represented as:

\[
\mathcal F.
\]

Without soft preferences, the problem would simply be:

\[
\text{find any }A\in\mathcal F.
\]

But you want a better plan among all valid plans.

Now we introduce the objective function.

---

# 24. Soft preferences are penalties, not rules

A hard constraint says:

> This may never happen.

A soft constraint says:

> This may happen, but it has a cost.

CP-SAT minimizes those costs.

So:

\[
\text{better plan}
=
\text{lower total penalty}.
\]

Production v4 currently has three preference components:

| Component | Meaning |
|---|---|
| Contribution-seat | Higher contributors should receive more desirable seating |
| Activeness | More active participants should receive more desirable seating |
| Category-zone | Participant category should align with preferred zones |

Movement is **not included**.

---

# 25. First calculate seat disadvantage

Let:

\[
\rho(s)
\]

be priority rank.

Remember:

\[
\rho=1
\]

is best.

Production defines:

\[
\boxed{
d(o)
=
\frac{2}{|o|}
\sum_{s\in o}
(\rho(s)-1)
}
\]

This is called doubled mean disadvantage.

For a single seat ranked 1:

\[
d=2(1-1)=0.
\]

For single seat rank 8:

\[
d=2(8-1)=14.
\]

For Emperor pair with ranks 1 and 2:

\[
d
=
\frac{2}{2}
[(1-1)+(2-1)]
=
1.
\]

For pair ranks 7 and 8:

\[
d
=
(7-1)+(8-1)
=
13.
\]

Therefore lower disadvantage means better seating.

---

# 26. Why multiply the mean by 2?

Because CP-SAT prefers integer coefficients.

The average of two numbers can contain \(0.5\).

Example:

\[
\frac{1+2}{2}=1.5.
\]

Multiplying by two avoids floating-point values.

The official OR-Tools documentation states that CP-SAT is fundamentally an integer solver and model terms should use integers. [Google for Developers](https://developers.google.com/optimization/cp/cp_solver/?utm_source=chatgpt.com)

Your code deliberately stays in integer arithmetic.

That is one reason you see unusual expressions such as `half_up()`.

---

# 27. Contribution importance

Suppose participant \(p\) belongs to tier \(t\).

Let:

\[
m_p
\]

be their contribution amount.

Let:

\[
m_t^{min}
\]

and

\[
m_t^{max}
\]

be the smallest and largest contributions observed inside that tier for the current event.

Production calculates:

\[
\boxed{
I^C_p
=
1+
round_{half-up}
\left(
\frac{
99(m_p-m_t^{min})
}{
\max(1,m_t^{max}-m_t^{min})
}
\right)
}
\]

Therefore:

\[
I^C_p\in[1,100].
\]

The lowest contributor receives approximately:

\[
1.
\]

The highest:

\[
100.
\]

---

# 28. What is `half_up()`?

The implementation is:

```python
def half_up(n, d):
    return (2 * n + d) // (2 * d)
```

where:

```python
//
```

means integer floor division.

This implements conventional round-half-up without floating-point values.

If:

\[
\frac nd=2.4
\]

the result is 2.

If:

\[
\frac nd=2.5
\]

the result is 3.

The important reason is reproducibility and integer-only CP-SAT modelling.

---

# 29. Contribution-seat penalty

Once contribution importance is known:

\[
\boxed{
R^C_{p,o}
=
I^C_p\,d(o)
}
\]

Suppose a highest contributor has:

\[
I^C_p=100.
\]

If given the best single seat:

\[
d=0
\]

therefore:

\[
R^C=0.
\]

If given the worst rank-16 single seat:

\[
d=30.
\]

Then:

\[
R^C=100(30)=3000.
\]

Now consider the lowest contributor:

\[
I^C=1.
\]

The same worst seat produces only:

\[
R^C=30.
\]

That is the mathematical mechanism that gives high contributors stronger pressure toward desirable seats.

---

# 30. Activeness importance

The same principle is applied to previous participation.

Let:

\[
e_p
\]

be events joined during the preceding two years.

Define:

\[
e_t^{min},e_t^{max}
\]

within the same contribution tier.

Then:

\[
\boxed{
I^A_p
=
round_{half-up}
\left(
\frac{
100(e_p-e_t^{min})
}{
\max(1,e_t^{max}-e_t^{min})
}
\right)
}
\]

so:

\[
I^A_p\in[0,100].
\]

Unlike contribution importance, this begins at zero.

Then:

\[
\boxed{
R^A_{p,o}
=
I^A_p\,d(o)
}
\]

A participant with the lowest observed activeness has no differential activeness pressure:

\[
I^A_p=0.
\]

---

# 31. Category-zone cost

The policy file contains a cost matrix.

For example the current MONASTIC values are effectively:

| Zone | Cost |
|---|---:|
| Right Center | 0 |
| Left Center | 2 |
| Right Outer | 4 |
| Left Outer | 8 |

These are not learned by machine learning.

They are **configured domain-policy numbers**.

For option \(o\):

\[
\boxed{
R^Z_{p,o}
=
\frac{2}{|o|}
\sum_{s\in o}
Z_{cat(p),zone(s)}
}
\]

Again, a pair uses the **average influence**, so Emperor registrations do not automatically receive twice the optimization importance merely because they occupy two seats.

That design decision is mathematically significant.

---

# 32. Why normalize the three costs?

The three raw costs have different scales.

Contribution and activeness can reach:

\[
3000.
\]

Zone cost may reach only:

\[
16.
\]

Without normalization, contribution would dominate simply because its numbers are larger.

Production therefore maps each component onto approximately:

\[
0\dots100.
\]

For raw cost \(R\) and theoretical maximum \(M\):

\[
\boxed{
N(R,M)
=
\left\lfloor
\frac{200R+M}{2M}
\right\rfloor
}
\]

which is equivalent to half-up rounding of:

\[
100\frac RM.
\]

Therefore all preference components operate on a comparable scale.

---

# 33. The ranked preference weights

The user does not directly enter arbitrary numbers such as:

\[
73,17,10.
\]

Instead, staff rank the enabled preferences.

The backend maps them to:

\[
40,\;30,\;20.
\]

Suppose the UI ordering is:

\[
Contribution,\ Category,\ Activeness.
\]

Then:

\[
w_C=40,\quad
w_Z=30,\quad
w_A=20.
\]

If Activeness is disabled:

\[
w_C=40,\quad
w_Z=30,\quad
w_A=0.
\]

The coefficients are **relative weights**.

They are not percentages.

They also do not represent lexicographic priorities.

For example multiple improvements under a weight-30 preference could mathematically outweigh one deterioration under weight 40.

---

# 34. Cost of assigning participant \(p\) to option \(o\)

The complete candidate cost is:

\[
\boxed{
Cost(p,o)
=
w_C N^C_{p,o}
+
w_A N^A_{p,o}
+
w_Z N^Z_{p,o}
}
\]

Every possible legal participant-option assignment has one precomputed integer cost.

This happens in:

```python
candidate_cost(...)
```

before CP-SAT needs to reason about preference mathematics itself.

---

# 35. The production objective function

Now we reach the central optimization equation.

Because:

\[
z_{p,o}=1
\]

only for the selected option, the total objective is:

\[
\boxed{
\min Z
=
\sum_{p\in P}
\sum_{o\in O_p}
Cost(p,o)z_{p,o}
}
\]

This is exactly what:

```python
costexpr.append(
    v * candidate_cost(...)[
        "weighted"
    ]["total"]
)
```

creates.

Then:

```python
model.Minimize(sum(costexpr))
```

asks CP-SAT to find the valid assignment with minimum total weighted penalty.

That equation is arguably **the most important mathematical statement in your entire solver**.

---

# 36. What production does NOT use anymore

Your current production model does not use:

\[
MovementPenalty
\]

does not use:

\[
PreviousAllocation
\]

and does not use:

\[
M\times MainPenalty+TieBreak
\]

as one combined objective.

Those belong to the historical prototype.

This needs to be explicitly removed from the final dissertation mathematical formulation.

---

# 37. Canonicalization — why two optimal runs might otherwise look different

There may be many seating plans with exactly the same value:

\[
Z^*.
\]

Suppose P001 and P002 are completely equivalent.

Swapping them might produce exactly the same cost.

Both are mathematically optimal.

But for reproducibility you would prefer the same plan every time.

Production therefore performs a **second optimization phase** after the real business objective is proven.

---

# 38. Production canonicalization is lexicographic

First solve:

\[
\min Z.
\]

Suppose:

\[
Z^*=4200.
\]

Production then fixes:

\[
Z=4200.
\]

No later operation may worsen the business objective.

Options are sorted deterministically.

For each participant, define:

\[
j_p
=
\sum_{o\in O_p}
index(o)z_{p,o}.
\]

Because exactly one option is selected, \(j_p\) is simply that selected option's deterministic index.

Participants are sorted by ID:

\[
p_1,p_2,\dots,p_n.
\]

Then production sequentially solves:

\[
\min j_{p_1}
\]

and fixes its optimum.

Next:

\[
\min j_{p_2}.
\]

And so forth.

Therefore the final output is conceptually:

\[
\boxed{
\min_{\text{lex}}
(j_{p_1},j_{p_2},\dots,j_{p_n})
}
\]

subject to:

\[
Z=Z^*.
\]

This produces a deterministic canonical assignment without affecting the true business objective.

---

# 39. This is different from the old prototype tie-break

The prototype used something conceptually like:

\[
\min
MZ+\tau.
\]

Production no longer does this.

Therefore your dissertation should describe:

> **two-stage optimization with post-optimal canonicalization**

rather than:

> **large-\(M\) tie-breaking objective**

for the final system.

---

# 40. What CP-SAT does after receiving this model

Your Python code does not itself manually loop through every seating combination.

Instead it hands the mathematical model to:

```python
cp_model.CpSolver()
```

and calls:

```python
engine.Solve(model)
```

Conceptually CP-SAT searches the feasible region while repeatedly doing things such as domain propagation, Boolean/SAT reasoning, conflict learning, bounding and parallel search.

The CP-SAT-LP paper describes the solver as a purely integral CP solver built on SAT using Lazy Clause Generation, augmented with linear-programming relaxation and multiple portfolio workers. [DROPS](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.CP.2023.3?utm_source=chatgpt.com)

Therefore CP-SAT is not simply:

> try arrangement 1, try arrangement 2, try arrangement 3...

It aggressively eliminates large families of impossible or inferior assignments.

---

# 41. FEASIBLE versus OPTIMAL

This distinction is essential for your VIVA.

If CP-SAT returns:

\[
OPTIMAL
\]

it means:

> A feasible solution has been found and the solver has mathematically established that no better objective value exists.

If it returns:

\[
FEASIBLE
\]

it means:

> A valid solution has been found, but the solver has not proved that no better one exists.

Google's documentation makes exactly this distinction. [Google for Developers](https://developers.google.com/optimization/cp/cp_solver?utm_source=chatgpt.com)

Production v4 can accept independently validated FEASIBLE results when:

```python
require_optimal = false
```

but correctly labels them:

\[
FEASIBLE.
\]

It does not claim:

\[
OPTIMAL.
\]

For your benchmark experiments, you can enable stricter optimality requirements where appropriate.

---

# 42. Best objective bound and optimality gap

Suppose the best plan found has:

\[
Z=5000.
\]

Suppose CP-SAT has established that:

\[
Z\ge4800
\]

for every possible plan.

Then:

\[
BestBound=4800.
\]

The absolute optimality gap is:

\[
5000-4800=200.
\]

Your code reports:

\[
gap=
Z-Z_{bound}.
\]

When:

\[
gap=0
\]

and the search proof completes appropriately, optimality is established.

---

# 43. Why independent validation exists after CP-SAT

Your system does not blindly trust:

> “The solver said it succeeded.”

`production_validator.py` reconstructs the physical result from the JSON assignment.

It does **not** inspect the internal CP-SAT Boolean variables.

This is very good engineering practice.

It separately checks the assigned participant set, duplicate seats, blocked seats, valid pairs, accessibility, C12 tier precedence, C13 contribution ordering, C15 front packing, C16 row packing, quality metrics, and serialized output consistency.

Mathematically you can describe this as:

\[
V(A)=
\bigwedge_i check_i(A).
\]

For generated solver output:

\[
V(A)=true
\]

must hold before the result is accepted.

One subtle point:

The independent validator verifies the **solution**.

It does not independently reproduce CP-SAT's proof that:

\[
Z=Z^*.
\]

That optimality proof still belongs to CP-SAT.

---

# 44. Your current Objective 2 now has its own mathematical logic

This is where the latest repository differs from the older documentation.

`verification.py` now checks manually edited seating plans.

For edited plan \(A\), define:

\[
F(A)
\]

as the set of detected safeguard findings.

Current explicit finding rules are:

\[
C12,\ C13,\ C15,\ C16.
\]

C12 and C13 are marked:

\[
RED.
\]

C15 and C16 are:

\[
YELLOW.
\]

A RED finding is blocking while its status is `OPEN`.

Define:

\[
OpenBlocking(A)
=
\sum_{f\in F(A)}
\mathbf1[
severity(f)=RED
\land
status(f)=OPEN
].
\]

Here:

\[
\mathbf1[\cdot]
\]

is an indicator function:

\[
\mathbf1[condition]
=
\begin{cases}
1 & condition\ true\\
0 & condition\ false
\end{cases}.
\]

Publication requires:

\[
\boxed{
OpenBlocking(A)=0.
}
\]

But there is an important governance feature.

A RED finding may be explicitly acknowledged:

\[
status(f)=ACKED.
\]

Then it is not counted as `open_blocking`.

Therefore your current safeguard is **not mathematically equivalent** to the old documented formula:

\[
accept(A)=\bigwedge_h check_h(A).
\]

That old formula implies no violation can ever be accepted.

Your implementation actually supports **human-authorized override**.

---

# 45. The more accurate publication model

A more faithful mathematical description of current implementation is:

\[
\boxed{
Publishable(A)
=
Integrity(A)
\land Reviewed(A)
\land
OpenBlocking(A)=0
\land
BaselineCurrent(A)
}
\]

where:

\[
Integrity(A)
\]

covers non-overridable structural validity such as known seats, no duplicate occupancy, complete paid-seat count at publication, valid Emperor pair cardinality, blocked-seat exclusion and accessibility.

\[
Reviewed(A)
\]

means a safeguard review has been performed.

\[
OpenBlocking(A)=0
\]

means every RED finding has either been resolved or explicitly acknowledged.

\[
BaselineCurrent(A)
\]

means the plan/revision/publication pointer has not gone stale due to another staff update.

That formulation matches the current code much better than the existing documentation.

---

# 46. An important distinction for your dissertation: “hard solver rule” does not always mean “non-overridable staff publication rule”

Inside automatic CP-SAT generation:

\[
C12,C13,C15,C16
\]

are compulsory.

CP-SAT cannot violate them.

However, after staff manually edit a generated seating map, the safeguard currently treats:

\[
C12,C13
\]

as RED findings that may be explicitly acknowledged.

And:

\[
C15,C16
\]

as YELLOW advisory findings.

Therefore you actually have two policy layers:

| Layer | Meaning |
|---|---|
| Solver constraint policy | What automatic generation is permitted to produce |
| Human publication governance | What manually edited plans staff are permitted to publish after review/acknowledgement |

This is a sophisticated and useful distinction to discuss in your dissertation.

It preserves:

> intelligent automated generation

while also preserving:

> administrator authority.

---

# 47. One correction to the methodology terminology in your Interim Report

Your Interim Report says mathematical formulation may use:

> linearization, reification and channeling. [Signed]DariusLeeShin_22003269\_…

The current production code certainly uses Boolean integer modelling and linear expressions.

But I do **not** see meaningful explicit reification in the current production model, such as `OnlyEnforceIf()` or equivalent implication constraints.

So I would not write:

> “The production solver relies extensively on reification.”

Instead write something more accurate such as:

> “The production model uses binary assignment variables, integer auxiliary boundary variables, linear expressions, domain restriction, and linear equality/inequality constraints. Invalid participant-seat combinations are excluded during candidate generation before model construction.”

That statement reflects the actual implementation.

---

# 48. Your complete production mathematical model in compact form

Now that every component has been explained, the core model can be summarized as:

\[
\boxed{
\begin{aligned}
\min_{z,b,B}\quad
&
\sum_{p\in P}
\sum_{o\in O_p}
Cost(p,o)z_{p,o}
\\[4pt]
\text{s.t.}\quad
&
\sum_{o\in O_p}z_{p,o}=1
&&\forall p\in P
\\
&
\sum_{\substack{p,o\\s\in o}}z_{p,o}\le1
&&\forall s\in S
\\
&
worst(p)\le B_t < best(q)
&&p\in T_h,\ q\in T_l
\\
&
row(p)\le b_g\le row(q)
&&c_p>c_q,\ t(p)=t(q)
\\
&
\sum_{s\in S_r}occ(s)=q_r
&&\forall r
\\
&
occ(s_j)\ge occ(s_{j+1})
&&\forall\text{ ordered row positions}
\\
&
z_{p,o}\in\{0,1\}.
\end{aligned}
}
\]

with \(O_p\) already excluding blocked, inaccessible and invalid pair options.

That is the mathematical heart of your FYP.

---

# 49. The entire Python execution pipeline mapped back to mathematics

You can now read the production Python code as this sequence:

| Python stage | Mathematical meaning |
|---|---|
| `validate_request()` | Validate parameters and model assumptions |
| `eligible()` | Construct \(P\) |
| `options()` | Construct \(O_p\) |
| `initial_rows()` | Domain reduction |
| `NewBoolVar()` | Construct \(z_{p,o}\) |
| `AddExactlyOne()` | C1 |
| `AddAtMostOne()` | C2 |
| `rowexpr` | Compute \(row(p)\) |
| `bestexpr/worstexpr` | Compute tier seat-order expressions |
| tier boundaries | C12 |
| contribution boundaries | C13 |
| `packing_pairs()` | C16 |
| row occupancy equality | C15 |
| `candidate_cost()` | Soft cost \(Cost(p,o)\) |
| `Minimize()` | Minimize \(Z\) |
| `CpSolver.Solve()` | Mathematical search |
| sequential `canon` solves | Canonical optimum selection |
| `validate_placements()` | Independent validity audit |
| `format_result()` | Convert mathematical solution into application data |

Once you see the code through this table, `production.py` becomes much easier to understand.

It is not random Python logic.

It is basically a translation layer between mathematical notation and OR-Tools APIs.

---

# 50. What should go into your dissertation methodology now?

I recommend that the final Methodology chapter include a dedicated section such as:

**3.X Mathematical Formulation of the Seating Allocation Constraint Optimization Problem**

Within that section, use this sequence:

| Subsection | Content |
|---|---|
| 3.X.1 Problem Definition | Explain COP and allocation units |
| 3.X.2 Sets, Indices and Parameters | \(P,S,O_p,\rho,pos,row,\dots\) |
| 3.X.3 Decision Variables | \(z_{p,o}\), boundary variables |
| 3.X.4 Feasibility and Domain Construction | paid eligibility, legal pairs, blocked/accessibility |
| 3.X.5 Hard Constraints | C1/C2/C12/C13/C15/C16 etc. |
| 3.X.6 Soft Preference Cost Model | contribution, activeness, zone |
| 3.X.7 Normalization and Weighted Objective | normalized \(0\!-\!100\), 40/30/20 |
| 3.X.8 CP-SAT Optimization and Solver Status | FEASIBLE vs OPTIMAL |
| 3.X.9 Canonicalization | deterministic output |
| 3.X.10 Independent Solution Validation | solver-independent verification |
| 3.X.11 Manual-Edit Safeguard Model | revised Objective 2 |

This is considerably better than copying `docs/mathematical_model.md` verbatim, because it explains the **research methodology** rather than just documenting software internals.

---

# 51. What should explicitly NOT appear as current mathematics

For the production dissertation model, retire these historical concepts:

\[
movement\ penalty
\]

\[
previous\ allocation\ baseline
\]

\[
incremental\ repair
\]

\[
affected/unaffected\ participant\ optimization
\]

and the prototype combined objective:

\[
M\times MainPenalty+TieBreak.
\]

If you mention them at all, label them:

> “Earlier prototype formulation superseded following September 2026 requirements re-elicitation.”

That allows you to demonstrate requirements evolution without making the final model internally inconsistent.

---

# 52. Documentation changes I recommend making in the repository

The current mathematical core itself is in reasonably good shape, but the documentation surrounding Objective 2 is now stale.

`docs/mathematical_model.md` currently says the full safeguard gate remains planned. That no longer reflects `verification.py` and `workspace.py`.

`README.md` says the safeguard implementation has been removed and that there is no automated contribution-order/packing review. That is also no longer true on current `main`.

`docs/code_overview.md` similarly describes the safeguard as planned.

The old equation:

\[
accept(A)=AND_h\,check_h(A)
\]

should also be revised because it fails to represent acknowledgement/override behavior.

A more accurate model is the `Publishable(A)` equation I gave above.

---

# 53. Academic and technical references you can use

For the theoretical justification of CP-SAT, Perron, Didier and Gay describe CP-SAT-LP as a purely integral constraint-programming solver built on a SAT solver using Lazy Clause Generation, together with simplex/linear-relaxation and portfolio-search mechanisms. [DROPS](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.CP.2023.3?utm_source=chatgpt.com)

A suitable APA-style reference is:

**Perron, L., Didier, F., & Gay, S. (2023). The CP-SAT-LP solver. In *29th International Conference on Principles and Practice of Constraint Programming (CP 2023)*, LIPIcs, 280, 3:1–3:2. https://doi.org/10.4230/LIPIcs.CP.2023.3**

For implementation behaviour, use Google's official CP-SAT documentation, particularly its integer-model requirement and solver-status definitions. [Google for Developers](https://developers.google.com/optimization/cp/cp_solver/?utm_source=chatgpt.com)

[Google OR-Tools CP-SAT documentation](https://developers.google.com/optimization/cp/cp_solver?utm_source=chatgpt.com)

The latest stable OR-Tools release currently shown by the official repository is **v9.15**. Your project currently declares `ortools>=9.10`, so for the final dissertation experiment I strongly recommend recording and preferably pinning the **exact OR-Tools version actually used during evaluation** rather than merely reporting `>=9.10`. [GitHub](https://github.com/google/or-tools/releases?utm_source=chatgpt.com)

---

The main conceptual takeaway to keep in your mind is this:

\[
\boxed{
\text{PJKIT rules}
\rightarrow
\text{legal domains }O_p
\rightarrow
\text{binary variables }z_{p,o}
\rightarrow
\text{hard constraints}
\rightarrow
\text{integer preference penalties}
\rightarrow
\min Z
\rightarrow
\text{CP-SAT}
\rightarrow
\text{independent validation}
}
\]

That is your seating-allocation algorithm at the mathematical level.

The Python code is simply implementing each arrow in that pipeline.

---
## Further Explanation

Yes. The compact formulation in Section 48 is essentially the **compressed mathematical summary of everything the Python solver does**. The easiest way to understand where it comes from is not to start with the final equations. Start with the real PJKIT question:

> “For every confirmed paid registration, which legal seat or seat-pair should be selected, such that all compulsory seating rules are satisfied and the overall preference penalty is as small as possible?”

Once that sentence is translated systematically, the compact mathematical model almost derives itself.

---

# 1. Start with the mathematical structure of the problem

Any mathematical optimization model usually contains five things:

\[
\boxed{
\text{Sets}
+
\text{Parameters}
+
\text{Decision Variables}
+
\text{Constraints}
+
\text{Objective}
}
\]

For your FYP:

\[
\boxed{
\text{Participants and seats}
+
\text{PJKIT data}
+
\text{seat-selection variables}
+
\text{business rules}
+
\text{preference minimization}
}
\]

So the compact model:

\[
\begin{aligned}
\min_{z,b,B}\quad
&
\sum_{p\in P}
\sum_{o\in O_p}
Cost(p,o)z_{p,o}
\\
\text{s.t.}\quad
&\cdots
\end{aligned}
\]

is really saying:

> “Choose values for the assignment variables \(z\) and auxiliary boundary variables \(b,B\), while satisfying all PJKIT rules, so that total seating penalty is minimized.”

That is the whole idea.

---

# 2. First derive the sets

We begin with the objects that exist in the real problem.

Let

\[
P
\]

be the set of eligible confirmed paid registrations.

For example:

\[
P=\{P_1,P_2,P_3,P_4\}.
\]

Let

\[
S
\]

be the set of physical seats:

\[
S=\{S_1,S_2,\dots,S_{256}\}.
\]

Not every physical seat is usable, however, because some seats are blocked.

Now for every participant \(p\), define:

\[
O_p
\]

as that participant's set of **legal seating options**.

This is a very important design choice in your production model.

For a Merit participant:

\[
O_p=
\{
\{S_1\},
\{S_2\},
\{S_3\},
\dots
\}.
\]

For an Emperor participant:

\[
O_p=
\{
\{S_1,S_2\},
\{S_3,S_4\},
\dots
\}.
\]

So instead of saying:

> “Assign individual seats.”

the production model says:

> “Select exactly one legal allocation option.”

That lets one mathematical structure handle both one-seat registrations and two-seat Emperor registrations.

---

# 3. Why some constraints do not appear explicitly in the final equations

This is an important point for your dissertation.

Suppose seat `R06-S05` is blocked.

Instead of creating:

\[
z_{p,R06S05}
\]

and adding:

\[
z_{p,R06S05}=0,
\]

your Python code simply does **not create that option**.

Therefore:

\[
R06S05\notin O_p.
\]

Likewise, if an Emperor pair crosses the aisle, that pair is not included in:

\[
O_p.
\]

If a participant requires an accessible seat, non-accessible options do not belong to:

\[
O_p.
\]

Therefore several hard rules are encoded in the definition of the domain itself.

This means the compact model should be read as:

\[
O_p=
\{\text{all legal options for }p\}.
\]

That definition already contains rules equivalent to blocked-seat exclusion, accessibility restrictions, Emperor pair cardinality and approved pair geometry.

This is why C3, C10, C11 and C17 do not necessarily need their own explicit equation in the compact block.

---

# 4. Derive the main decision variable

Now ask:

> What does the solver actually need to decide?

For every participant \(p\) and legal option \(o\in O_p\), define:

\[
\boxed{
z_{p,o}\in\{0,1\}
}
\]

with:

\[
z_{p,o}
=
\begin{cases}
1,&\text{if participant }p\text{ is assigned option }o\\
0,&\text{otherwise.}
\end{cases}
\]

This is the core decision variable.

Everything else in the model either constrains these \(z\)'s or calculates something from them.

For example, imagine:

\[
O_{P_1}
=
\{S_1,S_2,S_3\}.
\]

The solver could choose:

\[
z_{P_1,S_1}=0
\]

\[
z_{P_1,S_2}=1
\]

\[
z_{P_1,S_3}=0.
\]

That simply means:

\[
P_1\rightarrow S_2.
\]

---

# 5. Now derive C1: every paid registration needs exactly one allocation

The business rule says:

> Every confirmed paid registration must receive exactly its required allocation.

For one participant:

\[
z_{p,o_1}
+
z_{p,o_2}
+
\dots
+
z_{p,o_n}
=
1.
\]

Using summation notation:

\[
\boxed{
\sum_{o\in O_p}z_{p,o}=1
\qquad\forall p\in P
}
\]

Break the notation apart.

\[
\sum
\]

means add.

\[
o\in O_p
\]

means over every legal option available to participant \(p\).

Therefore:

\[
\sum_{o\in O_p}z_{p,o}
\]

means:

> add all option-selection variables belonging to participant \(p\).

Then:

\[
=1
\]

forces exactly one option to be chosen.

Finally:

\[
\forall p\in P
\]

means:

> apply this rule to every eligible participant.

So the equation literally says:

> For every confirmed registration, exactly one legal seating option must be selected.

That maps directly to:

```python
model.AddExactlyOne(vs)
```

---

# 6. Derive seat occupancy

Now we need to prevent two registrations from receiving the same physical seat.

For each seat \(s\), define:

\[
occ(s)
\]

as the number of selected options containing that seat.

Mathematically:

\[
\boxed{
occ(s)
=
\sum_{\substack{p\in P\\o\in O_p:s\in o}}
z_{p,o}
}
\]

The condition:

\[
s\in o
\]

means:

> only include options that contain physical seat \(s\).

Suppose:

\[
P_1
\]

could select seat 10 individually, while Emperor participant \(P_2\) could select pair:

\[
(9,10).
\]

Then:

\[
occ(10)
=
z_{P_1,\{10\}}
+
z_{P_2,\{9,10\}}.
\]

Both cannot equal 1 simultaneously.

Therefore:

\[
\boxed{
occ(s)\le1
\qquad\forall s\in S
}
\]

or expanded:

\[
\boxed{
\sum_{\substack{p,o\\s\in o}}z_{p,o}\le1
\qquad\forall s\in S
}
\]

This gives the second line of your compact model.

---

# 7. Why Emperor pairs automatically occupy two seats

Suppose Emperor participant \(E_1\) selects:

\[
o=(S_9,S_{10}).
\]

Then:

\[
z_{E_1,o}=1.
\]

The same variable contributes to both:

\[
occ(S_9)
\]

and:

\[
occ(S_{10}).
\]

So there is no need to independently say:

> “also occupy the second seat.”

Choosing the pair means both physical seats become occupied.

This is one of the cleanest parts of your mathematical design.

---

# 8. Derive the participant's assigned row

The next business rule concerns contribution ordering.

But before saying:

\[
row(p)\le row(q),
\]

we must mathematically define:

\[
row(p).
\]

Every option \(o\) has a row:

\[
row(o).
\]

Because exactly one option is selected:

\[
\boxed{
row(p)
=
\sum_{o\in O_p}
row(o)z_{p,o}
}
\]

Suppose P1 can choose options in rows:

\[
1,2,3.
\]

If:

\[
z=(0,1,0),
\]

then:

\[
row(P_1)
=
1(0)+2(1)+3(0)
=
2.
\]

The binary decision variable effectively acts like a mathematical switch.

This is exactly what the production code creates with `rowexpr`.

---

# 9. Derive within-tier contribution ordering

Now translate the business requirement:

> Within the same contribution tier, a participant with a higher contribution must not be seated in a later row than a lower contributor.

Suppose:

\[
c_p>c_q
\]

where:

\[
c_p
\]

means participant \(p\)'s contribution amount.

If they are in the same tier:

\[
t(p)=t(q),
\]

then:

\[
\boxed{
row(p)\le row(q)
}
\]

This is the pure mathematical specification.

For example:

\[
RM5000>RM4000.
\]

If the RM5000 participant is in Row 3 while RM4000 participant is Row 2:

\[
3\le2
\]

is false.

So the assignment is invalid.

If both are in Row 2:

\[
2\le2
\]

is true.

Therefore same-row placement is permitted.

---

# 10. But the code does not literally create every pairwise inequality

This is where we distinguish:

### Mathematical rule

from

### CP-SAT encoding.

The mathematical rule is:

\[
c_p>c_q
\Rightarrow
row(p)\le row(q).
\]

But if you have many participants, creating every possible pair could produce lots of constraints.

Instead, your implementation groups participants by contribution level.

Suppose one tier has:

\[
RM5000,\ RM4000,\ RM3000.
\]

Call these groups:

\[
G_1,G_2,G_3.
\]

The solver creates an auxiliary integer boundary:

\[
b_1
\]

between \(G_1\) and \(G_2\), and:

\[
b_2
\]

between \(G_2\) and \(G_3\).

Then:

\[
row(p)\le b_1
\qquad\forall p\in G_1
\]

and:

\[
b_1\le row(q)
\qquad\forall q\in G_2.
\]

Therefore automatically:

\[
row(p)\le row(q).
\]

That is why the compact model contains:

\[
\boxed{
row(p)\le b_g\le row(q)
}
\]

for consecutive contribution levels.

Here:

\[
b_g
\]

is not a real physical object.

It is an **auxiliary mathematical variable** introduced solely to encode ordering efficiently.

---

# 11. Why the boundary approach works transitively

Suppose:

\[
RM5000>RM4000>RM3000.
\]

The first boundary gives:

\[
row(5000)\le b_1\le row(4000).
\]

The second gives:

\[
row(4000)\le b_2\le row(3000).
\]

Therefore:

\[
row(5000)
\le
row(4000)
\le
row(3000).
\]

So even though we never explicitly wrote:

\[
row(5000)\le row(3000),
\]

it follows mathematically.

This is called **transitivity**.

---

# 12. Now derive cross-tier precedence

The rule between tiers is stronger.

The tier priority is:

\[
EMPEROR
\prec
MERIT
\prec
BODHI.
\]

Here \(\prec\) means “must precede.”

If we only wrote:

\[
row(Emperor)\le row(Merit),
\]

there would be a problem.

They can share a row.

Inside that shared row, a Merit seat could potentially be more desirable than an Emperor seat.

Therefore production v4 needs a finer ordering.

---

# 13. Derive the global seat order

Define:

\[
\rho(s)
\]

as priority rank inside a row.

Define:

\[
C
\]

as seats per row.

Then:

\[
\boxed{
order(s)
=
(row(s)-1)C+\rho(s)
}
\]

This converts a two-dimensional position:

\[
(row,\ priorityRank)
\]

into one globally ordered number.

For a 16-seat row:

Row 1 best seat:

\[
order=1.
\]

Row 1 worst seat:

\[
order=16.
\]

Row 2 best seat:

\[
order=17.
\]

So:

\[
1<2<\cdots<16<17<18<\cdots
\]

naturally represents the front-to-back seat preference order.

---

# 14. Derive the best and worst physical seat of a registration

For Merit/Bodhi, an option has one seat, so best and worst are the same.

For an Emperor option:

\[
o=(s_1,s_2),
\]

define:

\[
best(o)
=
\min_{s\in o}order(s)
\]

and:

\[
worst(o)
=
\max_{s\in o}order(s).
\]

Then for the selected option:

\[
best(p)
=
\sum_{o\in O_p}
best(o)z_{p,o}
\]

and:

\[
worst(p)
=
\sum_{o\in O_p}
worst(o)z_{p,o}.
\]

Why consider both Emperor seats?

Because saying only:

\[
best(Emperor)<best(Merit)
\]

could still allow the second Emperor seat to be worse than the Merit seat.

The business rule requires the whole Emperor allocation to precede the next tier.

Therefore:

\[
\boxed{
worst(p)<best(q)
}
\]

for higher-tier \(p\), lower-tier \(q\).

---

# 15. Again, production uses a boundary encoding

Instead of directly adding:

\[
worst(p)<best(q)
\]

for every higher/lower participant pair, production creates:

\[
B_t.
\]

For higher tier:

\[
worst(p)\le B_t.
\]

For lower tier:

\[
best(q)>B_t.
\]

Therefore:

\[
worst(p)\le B_t<best(q),
\]

which implies:

\[
worst(p)<best(q).
\]

That's where this compact line came from:

\[
\boxed{
worst(p)\le B_t < best(q)
}
\]

The capital \(B\) is simply being used to distinguish a **tier boundary** from the lowercase \(b\) used for a **contribution-row boundary**.

You could choose different notation in your dissertation if you want clearer symbols.

For example:

\[
\beta_t
\]

for tier boundaries and:

\[
\gamma_{t,g}
\]

for contribution boundaries may actually be clearer academically.

---

# 16. Derive front-fill C15

Now consider this PJKIT operational rule:

> Use available seats from the front rows before moving to later rows.

Let:

\[
D
\]

be total physical seat demand.

For each row \(r\), let:

\[
A_r
\]

be the number of assignable non-blocked seats.

Define remaining demand before row \(r\):

\[
D_r.
\]

Then the required occupancy for that row is:

\[
\boxed{
q_r
=
\min(D_r,A_r)
}
\]

and:

\[
D_{r+1}=D_r-q_r.
\]

Now since:

\[
occ(s)
\]

tells us whether physical seat \(s\) is occupied, the total occupancy of row \(r\) is:

\[
\sum_{s\in S_r}occ(s).
\]

Therefore:

\[
\boxed{
\sum_{s\in S_r}occ(s)=q_r
\qquad\forall r
}
\]

This is C15.

If Row 1 has capacity 16 and there are 20 required seats:

\[
q_1=16.
\]

Then remaining:

\[
20-16=4.
\]

So:

\[
q_2=4.
\]

The model then forces:

\[
occupancy(Row1)=16
\]

and:

\[
occupancy(Row2)=4.
\]

No solver solution can place 15 people in Row 1 and 5 in Row 2.

---

# 17. Why front fill alone is not enough

Suppose Row 2 must contain four occupied seats.

This satisfies:

\[
\sum occ(s)=4.
\]

But they could theoretically be scattered:

\[
[X][\ ][X][\ ][X][\ ][X].
\]

PJKIT does not want that.

So we need another constraint describing **which four seats** inside the row get filled first.

That is C16.

---

# 18. Derive the packing order inside a row

The current production policy orders seats:

> right/east side outward from the aisle first, then left/west side outward.

Let the available seats in this required order be:

\[
s_1,s_2,s_3,\dots,s_m.
\]

Then require:

\[
occ(s_2)\le occ(s_1)
\]

\[
occ(s_3)\le occ(s_2)
\]

and so on.

Compactly:

\[
\boxed{
occ(s_{j+1})\le occ(s_j)
}
\]

Why?

If:

\[
occ(s_3)=1,
\]

then:

\[
1\le occ(s_2)
\]

forces:

\[
occ(s_2)=1.
\]

Then:

\[
1\le occ(s_1)
\]

forces:

\[
occ(s_1)=1.
\]

Therefore you cannot occupy a later-priority seat without filling all earlier ones.

The only valid occupancy shapes are prefixes:

\[
[1,0,0,0]
\]

\[
[1,1,0,0]
\]

\[
[1,1,1,0]
\]

\[
[1,1,1,1].
\]

Not:

\[
[1,0,1,0].
\]

That is the mathematical meaning of your packing rule.

---

# 19. Now we have described all valid plans

Up to this point, we haven't said which valid plan is “best.”

We have only constructed what optimization theory calls the **feasible region**:

\[
\mathcal F.
\]

Conceptually:

\[
\mathcal F
=
\{
z:
z\text{ satisfies all hard constraints}
\}.
\]

CP-SAT is not allowed to choose anything outside:

\[
\mathcal F.
\]

Hard constraints therefore define:

\[
\text{possible vs impossible}.
\]

Now the objective decides:

\[
\text{better vs worse}.
\]

---

# 20. Derive the cost function

For every legal combination:

\[
(p,o),
\]

the Python scorer calculates:

\[
Cost(p,o).
\]

In current production v4:

\[
Cost(p,o)
=
w_C N^C_{p,o}
+
w_A N^A_{p,o}
+
w_Z N^Z_{p,o}.
\]

Where:

\[
N^C
\]

is normalized contribution-seat cost,

\[
N^A
\]

is normalized activeness-seat cost,

and:

\[
N^Z
\]

is normalized category-zone cost.

The weights:

\[
w_C,w_A,w_Z
\]

come from the ordered preferences selected by staff.

Typical mappings are:

\[
40,30,20.
\]

---

# 21. Why multiply cost by \(z_{p,o}\)?

Suppose P1 has three options:

\[
o_1,o_2,o_3
\]

with costs:

\[
10,50,30.
\]

Suppose:

\[
z=(0,1,0).
\]

Then:

\[
10(0)+50(1)+30(0)=50.
\]

Only the selected option contributes to the objective.

Therefore the cost incurred by participant \(p\) is:

\[
\sum_{o\in O_p}
Cost(p,o)z_{p,o}.
\]

Then summing over every participant gives:

\[
\boxed{
Z
=
\sum_{p\in P}
\sum_{o\in O_p}
Cost(p,o)z_{p,o}.
}
\]

That is the complete plan's penalty.

---

# 22. Finally derive the objective

The system wants the lowest total penalty.

Therefore:

\[
\boxed{
\min Z
}
\]

or fully expanded:

\[
\boxed{
\min
\sum_{p\in P}
\sum_{o\in O_p}
Cost(p,o)z_{p,o}.
}
\]

This is exactly what your solver's:

```python
model.Minimize(expr)
```

means mathematically.

The complete question being sent to CP-SAT is now:

> Among all values of \(z\), \(b\), and \(B\) satisfying every compulsory constraint, find the values producing the smallest possible \(Z\).

---

# 23. Now the compact model should make much more sense

We can rewrite it with annotations:

\[
\boxed{
\begin{aligned}
\min_{z,b,B}\quad
&
\underbrace{
\sum_{p\in P}
\sum_{o\in O_p}
Cost(p,o)z_{p,o}
}_{\text{minimize total soft-preference penalty}}
\\[6pt]
\text{s.t.}\quad
&
\underbrace{
\sum_{o\in O_p}z_{p,o}=1
}_{\text{exactly one allocation option}}
&&
\forall p\in P
\\[6pt]
&
\underbrace{
\sum_{\substack{p,o\\s\in o}}
z_{p,o}\le1
}_{\text{no physical seat duplicated}}
&&
\forall s\in S
\\[6pt]
&
\underbrace{
worst(p)\le B_t<best(q)
}_{\text{higher tier entirely before lower tier}}
&&
p\in T_h,\ q\in T_l
\\[6pt]
&
\underbrace{
row(p)\le b_{t,g}\le row(q)
}_{\text{higher contribution not behind lower contribution}}
&&
c_p>c_q,\ t(p)=t(q)
\\[6pt]
&
\underbrace{
\sum_{s\in S_r}occ(s)=q_r
}_{\text{front rows filled first}}
&&
\forall r
\\[6pt]
&
\underbrace{
occ(s_{j+1})\le occ(s_j)
}_{\text{required centre/right-to-left packing}}
&&
\forall\text{ ordered seat pairs}
\\[6pt]
&
\underbrace{
z_{p,o}\in\{0,1\}
}_{\text{binary assignment decisions}.}
\end{aligned}
}
\]

And importantly:

\[
\boxed{
o\in O_p
}
\]

already implies:

> non-blocked, legal cardinality, valid Emperor pair, non-aisle-crossing, and required accessibility.

That sentence should accompany the compact mathematical model in your dissertation.

---

# 24. A small numerical example makes the model easier to defend

Imagine a simplified hall with two rows and four seats per row.

Suppose:

\[
P=\{E_1,M_1,M_2\}.
\]

Where:

\[
E_1=\text{Emperor}
\]

and:

\[
M_1,M_2=\text{Merit}.
\]

Assume Emperor requires two seats.

Therefore total physical demand is:

\[
D=2+1+1=4.
\]

If Row 1 has four valid seats, C15 forces:

\[
q_1=4
\]

and:

\[
q_2=0.
\]

So all registrations must fit Row 1.

Suppose valid Emperor pairs are:

\[
O_{E_1}
=
\{(S_1,S_2),(S_3,S_4)\}.
\]

Merit options:

\[
O_{M_1}=O_{M_2}
=
\{S_1,S_2,S_3,S_4\}.
\]

C1 requires:

\[
z_{E_1,(S_1,S_2)}
+
z_{E_1,(S_3,S_4)}
=1.
\]

Likewise:

\[
\sum_{s}z_{M_1,s}=1
\]

and:

\[
\sum_s z_{M_2,s}=1.
\]

Seat occupancy prevents overlap.

Tier precedence then requires the Emperor's worst seat to precede both Merit seats.

If Emperor takes:

\[
(S_1,S_2),
\]

then Merit must use:

\[
S_3,S_4.
\]

Now suppose:

\[
c_{M_1}>c_{M_2}.
\]

Since they are in the same row:

\[
row(M_1)=row(M_2)=1,
\]

so contribution ordering:

\[
1\le1
\]

is satisfied.

The objective then decides whether:

\[
M_1\to S_3,\quad M_2\to S_4
\]

or vice versa, based on their contribution importance, activeness and category-zone penalties.

This example shows that:

**hard constraints first determine what is legal; the objective chooses the most desirable option among the legal alternatives.**

---

# 25. How to explain the entire model in your VIVA without drowning in symbols

A good spoken explanation would be:

> “I formulated the seating problem as a binary constraint optimization model. For each confirmed paid registration, I first generate a domain of legal seating options. A Merit or Bodhi option contains one physical seat, while an Emperor option contains an approved adjacent pair. I then define a Boolean decision variable indicating whether a participant receives a particular option. Hard constraints ensure exactly one option is selected per registration, no physical seat is reused, higher tiers precede lower tiers, higher contributors within the same tier are not placed in later rows, and the venue is filled according to the required front-to-back and row-packing rules. Illegal blocked, inaccessible or invalid pair options are removed before model construction. Among all arrangements satisfying those hard rules, CP-SAT minimizes the sum of normalized and weighted contribution, activeness and category-zone penalties.”

That explanation communicates almost the entire model without needing to display every equation.

Then if the examiner asks:

> “How did you mathematically model assigning a participant to a seat?”

show:

\[
z_{p,o}\in\{0,1\}.
\]

If they ask:

> “How do you ensure everybody gets one seat?”

show:

\[
\sum_{o\in O_p}z_{p,o}=1.
\]

If they ask:

> “How do you prevent duplicates?”

show:

\[
\sum_{p,o:s\in o}z_{p,o}\le1.
\]

If they ask:

> “Where is the intelligence?”

show:

\[
\min
\sum_{p,o}
Cost(p,o)z_{p,o}.
\]

---

# 26. One improvement I recommend for the dissertation notation

The previous compact model used:

\[
b
\]

and:

\[
B.
\]

They look too similar.

For readability, I recommend changing them to:

\[
\gamma_{t,g}
\]

for the within-tier contribution boundary, and:

\[
\beta_t
\]

for cross-tier seat-order boundaries.

Then C13 becomes:

\[
row(p)\le\gamma_{t,g}\le row(q).
\]

And C12 becomes:

\[
worst(p)\le\beta_t<best(q).
\]

This reduces confusion substantially.

---

# 27. I would also distinguish “mathematical specification” from “implementation encoding”

This is valuable academically.

For C13, the **business-level mathematical rule** is simply:

\[
\boxed{
c_p>c_q
\land
t(p)=t(q)
\Rightarrow
row(p)\le row(q)
}
\]

The boundary-variable formulation:

\[
row(p)\le\gamma_{t,g}\le row(q)
\]

is the **CP-SAT encoding**.

Similarly, the clean business specification for C12 is:

\[
\boxed{
t(p)\prec t(q)
\Rightarrow
worst(p)<best(q)
}
\]

while:

\[
worst(p)\le\beta_t<best(q)
\]

is the more efficient implementation encoding.

In the dissertation, showing **both levels** will make your methodology much clearer:

\[
\text{Business rule}
\rightarrow
\text{formal requirement}
\rightarrow
\text{CP-SAT encoding}.
\]

That directly demonstrates how your elicited PJKIT rules were transformed into executable constraint logic.

---

# 28. The model can therefore be explained in three layers

Think of it this way:

**Layer 1 — Feasibility**

\[
z\in\mathcal F
\]

asks:

> Is this seating plan allowed?

This is controlled by paid eligibility, legal options, unique occupancy, tier precedence, contribution ordering, accessibility and packing.

**Layer 2 — Quality**

\[
Z(z)
\]

asks:

> How good is this valid seating plan according to configurable preferences?

This is contribution, activeness and category-zone cost.

**Layer 3 — Optimization**

\[
\boxed{
z^*
=
\arg\min_{z\in\mathcal F}
Z(z)
}
\]

This is perhaps the most elegant way to summarize your entire algorithm mathematically.

The symbol:

\[
\arg\min
\]

means:

> return the actual assignment \(z\) that produces the smallest value.

So:

\[
\boxed{
z^*
=
\arg\min_{z\in\mathcal F}
\sum_{p\in P}
\sum_{o\in O_p}
Cost(p,o)z_{p,o}
}
\]

can be read in plain English as:

> **Find the valid seating assignment that minimizes the total weighted seating-preference penalty.**

That one sentence is probably the clearest mathematical description of what your FYP solver actually does.