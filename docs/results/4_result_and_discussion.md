# Chapter 4: Results and Discussion

*Dissertation chapter draft, 24 October 2026. This chapter consolidates the completed Study A attempt 3 controlled solver comparison and the completed Study B attempt 3 production initial-allocation benchmark. It reports saved records only; no experiment was rerun for this chapter. It supersedes the earlier stand-alone Study A chapter ([`solver-selection-v4-attempt3-results-and-discussion.md`][study-a-chapter]) as the dissertation source, and in particular replaces that chapter's forward-looking statements that Study B had not yet been executed. All numerical values have been recomputed from the run-record tables cited beneath each table or figure.*

## 4.1 Introduction

This chapter reports and interprets the empirical evaluation of the seating allocation engine developed for Objective 1: generating complete, rule-consistent and priority-aware seating plans for PJKIT assemblies by modelling allocation as a constraint optimization problem with compulsory rules and weighted, configurable preferences. The interim report selected Google OR-Tools CP-SAT as the implementation solver on the basis of literature and prototype evidence. The present evaluation tests that selection empirically rather than presuming it, and it was designed so that a result contrary to the original expectation would be reported as a finding instead of being treated as a reason to alter the cases or hypotheses after execution.

The evidence comes from two separately designed experiments. Study A is a controlled comparison of three implemented allocation methods, namely CP-SAT, the SCIP mixed-integer programming solver and a deterministic constraint-aware greedy constructor, on 21 known-feasible synthetic events under four preference settings and a common single-worker configuration. Study A established that the ranking of the two exact solvers depends on the search allowance, which left the production choice unresolved. Study B was therefore conducted as a production-path benchmark of CP-SAT and SCIP only, using the system's local initial-allocation service, eight parallel workers, a shared function allowance, independent validation of every returned candidate and repeated executions that included a semantics-preserving input permutation. The two studies answer different questions under different clocks and configurations; this chapter keeps their denominators separate and brings them together only in the discussion.

Section 4.2 states the research questions and describes the evaluation design that is common to both studies. Section 4.3 presents the Study A results and Section 4.4 presents the Study B results. Section 4.5 discusses the findings in relation to the research questions, the solver literature and Objective 1, and Section 4.6 examines threats to validity. Section 4.7 summarizes the chapter.

## 4.2 Evaluation design and evidence base

### 4.2.1 Research questions and hypotheses

The evaluation was organized around the hypotheses and questions confirmed before the main experiments were executed. They are listed in Table 4.1 together with the study that addresses each and the section in which it is answered. The Study B selection question was added after Study A, when that study showed that neither exact solver dominated across search allowances.

*Table 4.1. Research questions and hypotheses addressed in this chapter.*

| Label | Question or hypothesis | Evidence | Answered in |
| --- | --- | --- | --- |
| H1 | Under a common five-second search allowance, CP-SAT produces a lower modeled preference penalty than the greedy baseline on matched cases in which both return valid maps. | Study A, primary cohort | Sections 4.3.3 and 4.5.1 |
| RQ1 | How does CP-SAT compare with SCIP in valid-map coverage, preference penalty, runtime and optimality evidence? | Study A, all controlled cohorts | Sections 4.3.1–4.3.6 and 4.5.1 |
| H3 | Additional search time (5→30 s and 30→60 s) yields additional valid maps or lower penalties on at least some predeclared larger cases. | Study A, longer-budget cohort | Sections 4.3.2, 4.3.4 and 4.5.1 |
| VQ | What complete-result time and outcome does the prototype CP-SAT production path achieve under its 60-second configuration? | Study A, production-path checks | Section 4.3.7 |
| RQ2 | Under the production initial-allocation service and the agreed selection hierarchy, should CP-SAT or SCIP be the initial-generation solver? | Study B, primary 60-second cohort | Sections 4.4 and 4.5.2 |

These are bounded descriptive studies of related synthetic scenarios. They are not population-level significance tests, and no p-values or confidence intervals are claimed. Each hypothesis is evaluated separately for each preference setting where the protocol requires it, rather than through a pooled winner score.

### 4.2.2 Experimental units, events and allocation demand

A *registration unit* is an entitlement-bearing registration, not necessarily one physical seat. An Emperor registration requires an approved two-seat pair, whereas a Merit or Bodhi registration requires one seat. A *matched case* is one event under one preference setting, shared by all methods compared on it, and a *trial* (Study A) or *job* (Study B) is one method's execution of that case at one allowance. The venue layout has 232 usable seats in every scenario.

Study A used 21 known-feasible synthetic events, comprising five demand families with four patterns each (mixed, conflict, tied and an accessibility derivative) plus one distinct Emperor-heavy mixed event. Table 4.2 summarizes their demand. These are related constructed scenarios rather than 21 independent samples of real assemblies, and accessibility cases are derivatives of their base events. Registration count, physical seat demand and Emperor share must therefore be interpreted as distinct properties of each scenario.

*Table 4.2. Study A event families and allocation demand.*

| Event family | Registration units | Physical seat demand / 232 usable seats | Events |
| --- | ---: | ---: | ---: |
| Small | 24 | 32 / 232 | 4 |
| Typical | 96 | 152 / 232 | 4 |
| High occupancy | 117 | 179 / 232 | 4 |
| Near capacity | 139 | 212 / 232 | 4 |
| Full capacity | 152 | 232 / 232 | 4 |
| Emperor-heavy mixed | 131 | 230 / 232 | 1 |

Study B reused eight frozen Study A inputs, each paired with one preference setting and identified by the same input hash. The selection, shown in Table 4.3, covers the four larger mixed events from Study A's longer-budget subset, the typical mixed event, and one conflict, tied and accessibility scenario at full capacity, so that each preference setting is represented at least once. The tied scenario was assigned the disabled-preference setting, which makes it a feasibility, proof and timing control rather than evidence about preference quality.

*Table 4.3. Study B event–setting pairs. All inputs are byte-identical to the corresponding Study A inputs and passed witness validation in the Study B preflight.*

| Event | Preference setting | Registration units | Physical seats | Role in the comparison |
| --- | --- | ---: | ---: | --- |
| `typical-mixed` | Current | 96 | 152 | Moderate-demand reference |
| `high-mixed` | Current | 117 | 179 | High occupancy |
| `near-mixed` | Current | 139 | 212 | Near capacity |
| `full-mixed` | Current | 152 | 232 | Full capacity |
| `heavy-mixed` | Current | 131 | 230 | Emperor-heavy stress case |
| `full-conflict` | Reversed | 152 | 232 | Conflicting preference pattern |
| `full-tied` | Disabled | 152 | 232 | Feasibility, proof and timing control |
| `full-accessible` | Two preferences | 152 | 232 | Accessibility derivative |

### 4.2.3 Preference settings and objective scales

All methods in a matched case received the same effective input, compulsory rules and preference coefficients. The weighted objective combines normalized contribution, activity and category penalties, and a lower value indicates a better value of the declared objective. Table 4.4 lists the four settings. Study A used compact coefficients, whereas the production service maps the same priority orders to integer coefficients that are exactly ten times larger in every setting, as recorded in the Study B preflight. Because positive uniform scaling preserves the minimizer, the two scales describe the same optimization problem; production-scale penalties are not "ten times worse" seating.

*Table 4.4. Preference settings and coefficients in the two studies.*

| Setting | Priority order | Study A coefficients (contribution : activity : category) | Study B production coefficients |
| --- | --- | ---: | ---: |
| Current | Contribution > activity > category | 4 : 3 : 2 | 40 : 30 : 20 |
| Reversed | Category > activity > contribution | 2 : 3 : 4 | 20 : 30 : 40 |
| Two preferences | Contribution > category; activity disabled | 4 : 0 : 3 | 40 : 0 : 30 |
| Disabled | All ordinary preferences disabled | 0 : 0 : 0 | 0 : 0 : 0 |

The coefficients define compensatory trade-offs rather than lexicographic commands. A higher-ranked preference has greater influence per comparable normalized penalty unit, but improvements in other components can offset a worsening in that component, and a preference priority is never an additional compulsory rule. The penalty is neither a monetary cost nor a measurement of attendee satisfaction. Disabling preferences retains every compulsory rule, so the disabled setting is a feasibility and runtime control whose zero objective cannot demonstrate superior preference quality. Penalty magnitudes are therefore compared only within a fixed event and setting, and values under different coefficient vectors or scales are never pooled into one average quality score.

### 4.2.4 Experimental cohorts

Table 4.5 summarizes the cohorts. Study A's controlled cohorts used one worker, no solution hints and no canonical tie-break, with one execution per case, method and allowance. Its four production-path checks used a different configuration and are analysed separately. Study B ran every case twice in its original input order and once under a semantics-preserving permutation, for both backends, at three separate fresh allowances.

*Table 4.5. Experimental cohorts and their denominators. Cohorts are never pooled into a single success rate.*

| Study | Cohort | Design | Jobs | Configuration |
| --- | --- | --- | ---: | --- |
| A | Primary controlled comparison | 21 events × 4 settings × 3 methods at 5 s | 252 | One worker; 84 matched cases, 63 with active preferences |
| A | Longer-budget comparison | 4 large mixed events × 3 active settings × 3 methods × 30/60 s | 72 | One worker; 12 matched cases per allowance; 5-s endpoints reuse primary records |
| A | Production-path checks | 4 mixed events, current setting, CP-SAT at 60 s | 4 | Eight workers; canonicalization requested; diagnostic only |
| B | Primary comparison | 8 pairs × 3 executions × 2 backends at 60 s | 48 | Eight CP-SAT workers / eight native SCIP concurrent solvers; canonicalization off |
| B | Diagnostic endpoints | 8 pairs × 3 executions × 2 backends at 5 s and at 30 s | 96 | Same as Study B primary |
| | **Total** | | **472** | Study A 328; Study B 144 |

### 4.2.5 Execution environment and integrity gates

Both manifests record the same operating-system build, processor identifier and Python build, which indicates that the two studies were executed on the same Windows 11 workstation. Table 4.6 lists the recorded environment. Version and hardware values are those stored in the study manifests and are not claims about other installations.

*Table 4.6. Recorded execution environments.*

| Property | Study A attempt 3 | Study B attempt 3 |
| --- | --- | --- |
| Operating system | Windows 11 (10.0.26200), AMD64 | Windows 11 (10.0.26200), AMD64 |
| Processor | AMD Family 25 Model 80; 12 logical cores | AMD Family 25 Model 80; 6 physical / 12 logical cores; 31.4 GiB memory |
| Python | 3.14.7 | 3.14.7 |
| Solvers | OR-Tools 9.15.6755; SCIP 10.0.0 with SoPlex 8.0.0 | OR-Tools 9.15.6755; SCIP 10.0.0 with SoPlex 8.0.0 |
| Runner elapsed / ceiling | 4,045.05 s / 8,100 s | 2,683.23 s / 7,200 s |
| Operating conditions | Plugged in and awake, stable power, no competing heavy workloads | Plugged in and awake, stable power, no competing heavy workloads |

In Study A, all 328 scheduled jobs were attempted and completed, input-inventory and correctness gates passed, the report audit counted all 328 records, and no invalid returned allocation or incomplete execution was recorded. In Study B, the preflight verified 72 small oracle executions for both backends, including deliberately capacity-infeasible and accessibility-infeasible cases that both backends correctly reported as infeasible; it confirmed through native logs that SCIP launched eight distinct concurrent solver instances; and it confirmed that the service bridge adopted valid unproved candidates and rejected an invalid candidate. The Study B main run then completed 144/144 scheduled jobs, independently rescored 99 returned candidates, recorded zero invalid adopted maps and no model defects, and verified all record checksums.

Study B attempt 3 is a fresh execution. Its predecessor, attempt 2, stopped after 125 of 144 jobs when a Windows `PermissionError [WinError 5]` occurred while a checkpoint file was being replaced during evidence persistence; that weighted stage had itself returned a valid `OPTIMAL` result. Attempt 3 kept the attempt 2 solver contract, inputs, settings, seeds, schedules and decision hierarchy, changed only checkpoint persistence (separate pending and validated candidate files, atomic replacement and a bounded retry for Windows sharing errors, all inside the measured service clock), and used a fresh worker and data store for every job. No attempt 1 or attempt 2 record is pooled with the results below, and the same rule applies to the stopped Study A attempts and all development pilots.

### 4.2.6 Outcome definitions and timing clocks

A complete, independently validated allocation is required before any preference penalty is evaluated. `FEASIBLE` denotes such a map without proof that its penalty is minimal, and `OPTIMAL` adds the solver's reported proof of the declared objective minimum, subject to its numerical tolerances. Independent map validation establishes compliance with the compulsory rules and is a separate check from the solver's objective bound. In Study A, `UNKNOWN` denotes a run that did not establish a complete map and `CONSTRUCTION_FAILED` denotes a greedy dead end. In Study B, `no_map` denotes a job whose weighted stage produced no candidate, and `late_candidate` denotes a complete candidate whose weighted stage returned after the shared allowance and which the service contract therefore refused to adopt. None of these outcomes proves that an event is infeasible, because every measured input has a certified feasible witness.

The two studies use different clocks, and this difference is central to interpreting them together. Study A's allowances are *solver search* settings applied after preprocessing and model construction, and its reported allocation total additionally includes preprocessing, model building, extraction and validation. Study B's allowances are *shared function* allowances that begin at the service boundary and must cover normalization, model building and weighted search; a candidate whose weighted stage finishes after the allowance is not adopted. Study B then separately records the *complete local service return*, which adds independent validation, response formatting, SQLite persistence and JSON encoding. Neither clock includes interpreter start-up, browser rendering or network latency, so neither is a measurement of staff-facing web latency. No staff response-time requirement has been established, and the 5-, 30- and 60-second values are engineering settings rather than business deadlines.

## 4.3 Study A: controlled solver comparison

### 4.3.1 Five-second outcomes across all events

Figure 4.1 shows the complete primary cohort as an event-by-method outcome matrix, so that cases for which no penalty exists remain visible rather than disappearing from a cost average.

![Figure 4.1. Five-second outcomes across all 21 events, four settings and three methods.](solver-selection-v4-attempt3-figures-2026-10-23/figures/a1-five-second-outcomes.svg)

*Figure 4.1. Study A primary cohort at the five-second search allowance with one worker and no canonicalization. Dark green (O) denotes a validated optimal map, light green (F) a validated feasible map, amber (U) no validated map, red (C) a construction failure, purple (I) an invalid output and grey (E) an incomplete execution; the last two did not occur. Each setting contains 21 events per method. Sources: [run records][a-runs] and [execution coverage][a-execution-coverage].*

*Table 4.7. Complete independently validated maps at the five-second search allowance (denominator 21 events per method and setting).*

| Setting | CP-SAT | SCIP | Greedy |
| --- | ---: | ---: | ---: |
| Current | 15 (71.4%) | 9 (42.9%) | 6 (28.6%) |
| Reversed | 16 (76.2%) | 7 (33.3%) | 3 (14.3%) |
| Two preferences | 19 (90.5%) | 10 (47.6%) | 4 (19.0%) |
| All disabled | 20 (95.2%) | 17 (81.0%) | 0 (0.0%) |

Across the three active settings, CP-SAT returned 50 of 63 validated maps (79.4%), SCIP 26 of 63 (41.3%) and the greedy constructor 13 of 63 (20.6%). Including the disabled control gives 70/84 (83.3%), 43/84 (51.2%) and 13/84 (15.5%) respectively, although the active-setting denominator is the relevant preference-aware summary. Among active-setting trials, CP-SAT produced 14 `OPTIMAL`, 36 `FEASIBLE` and 13 no-map outcomes, SCIP produced 21 `OPTIMAL`, 5 `FEASIBLE` and 37 no-map outcomes, and greedy produced 13 `FEASIBLE` outcomes and 50 construction failures. CP-SAT's five-second advantage therefore concerned availability, whereas SCIP produced more proven optima and a larger proof fraction among its returned maps (21 of 26, against CP-SAT's 14 of 50). These fractions are conditional on a map being returned and are not overall success rates.

The greedy constructor returned no map in any disabled-setting case, which shows that removing preference optimization did not resolve its difficulty with the compulsory joint assignment problem. It nevertheless returned maps for `near-conflict/current` and `near-mixed/reversed` when neither exact solver did at five seconds, so neither exact implementation dominated case by case.

### 4.3.2 Matched outcomes at 5, 30 and 60 seconds

Figure 4.2 places the short- and longer-allowance outcomes side by side for the predefined subset of four large mixed events under the three active settings.

![Figure 4.2. Matched 5/30/60-second outcomes on the predefined large-event subset.](solver-selection-v4-attempt3-figures-2026-10-23/figures/a2-matched-budget-outcomes.svg)

*Figure 4.2. Fresh-run budget endpoints for `high-mixed`, `near-mixed`, `full-mixed` and `heavy-mixed` under the current, reversed and two-preference settings. Status codes follow Figure 4.1. Five-second cells reuse primary executions, and 30- and 60-second cells are additional runs. Other events and the disabled setting were not tested at longer allowances. Source: [matched-budget outcome table][a-matched-outcomes].*

*Table 4.8. Validated-map counts on the 12 matched cases at each search allowance (four events per active setting).*

| Setting | CP-SAT at 5 / 30 / 60 s | SCIP at 5 / 30 / 60 s | Greedy at 5 / 30 / 60 s |
| --- | ---: | ---: | ---: |
| Current | 2 / 4 / 4 | 1 / 4 / 4 | 1 / 1 / 1 |
| Reversed | 2 / 4 / 4 | 0 / 4 / 4 | 1 / 1 / 1 |
| Two preferences | 4 / 4 / 4 | 1 / 4 / 4 | 0 / 0 / 0 |
| All 12 cases | 8 / 12 / 12 | 2 / 12 / 12 | 2 / 2 / 2 |

Between five and 30 seconds, CP-SAT gained four validated maps and SCIP gained ten, and neither lost a previously available map. Both exact solvers reached 12/12 at 30 and at 60 seconds, but their proof outcomes differed sharply: all 12 CP-SAT maps at each longer allowance remained `FEASIBLE`, whereas all 12 SCIP maps were `OPTIMAL`. Every longer-budget greedy execution reproduced its five-second outcome, leaving its availability at 2/12, because the constructor terminates on success or on an irreversible dead end rather than continuing to revise its commitments. On this predefined subset, therefore, SCIP attained the same complete-map coverage as CP-SAT and proved every objective minimum at both longer allowances. This result does not extend to the conflict, tied or accessibility scenarios, which were not tested at 30 or 60 seconds in Study A.

### 4.3.3 Paired preference penalties at five seconds

Figure 4.3 compares preference penalties only where both methods returned validated maps for the same event and setting, normalized by the number of registration units.

![Figure 4.3. Both-valid paired preference-penalty differences per registration.](solver-selection-v4-attempt3-figures-2026-10-23/figures/a3-paired-preference-costs.svg)

*Figure 4.3. `(CP-SAT penalty − comparator penalty) / registration units`, conditional on both methods returning validated maps. Negative values favour CP-SAT, positive values favour the comparator, and zero denotes equality. Settings are plotted separately because their coefficient vectors differ; blank rows have no both-valid pair. Sources: [original paired table][a-original-pairs] and [cross-checked presentation table][a-paired-table].*

*Table 4.9. Both-valid five-second comparisons. Lower/equal/higher refers to CP-SAT's penalty relative to the named comparator.*

| Setting | Comparator | Both-valid pairs / 21 | CP-SAT lower / equal / higher | Median difference per registration |
| --- | --- | ---: | ---: | ---: |
| Current | Greedy | 5 | 5 / 0 / 0 | −22.21 |
| Current | SCIP | 9 | 0 / 4 / 5 | +0.40 |
| Reversed | Greedy | 2 | 2 / 0 / 0 | −13.10 |
| Reversed | SCIP | 7 | 0 / 5 / 2 | 0.00 |
| Two preferences | Greedy | 4 | 4 / 0 / 0 | −16.94 |
| Two preferences | SCIP | 10 | 0 / 4 / 6 | +4.47 |

CP-SAT had the lower penalty in all 11 both-valid comparisons against greedy, and the median difference was negative in each of the three active settings. This supports the H1 prediction for every setting in which it was estimable. The comparison does not assign penalties to greedy's 50 failures, and greedy returned faster than CP-SAT in all 11 of these pairs, so a speed–quality trade-off was observed even among successful executions. Against SCIP, CP-SAT had a lower penalty in none of the 26 both-valid pairs, tied in 13 and had a higher penalty in 13. This conditional comparison does not support a claim that CP-SAT delivered the best preference quality, although it cannot be offset against CP-SAT's broader availability because penalties were never observed for SCIP's missing maps.

### 4.3.4 Budget response in availability, penalty and elapsed time

Figure 4.4 shows how availability, paired penalty change and observed allocation time responded to the larger allowances on the same 12 matched cases.

![Figure 4.4. Availability, paired penalty change and allocation time at fresh-run endpoints.](solver-selection-v4-attempt3-figures-2026-10-23/figures/a4-budget-response.svg)

*Figure 4.4. The upper row counts validated maps; the middle row shows `(later penalty − earlier penalty) / registration units` for both-valid endpoints only; and the lower row shows observed allocation total for every execution, with × marking no validated map. Columns are independent fresh executions and must not be read as one continuous solve. Sources: [budget contrasts][a-budget-contrasts] and [run records][a-runs].*

Among both-valid CP-SAT endpoints, the penalty decreased in seven of eight 5→30-second comparisons with one tie (median change −4.73 units per registration), and it decreased in all 12 30→60-second comparisons (median −1.97). SCIP improved both of its available 5→30-second pairs (median −3.95) and showed 12 ties from 30 to 60 seconds after it had already established optimality. These observations support H3 for both exact solvers on this subset: the larger allowance yielded additional valid maps, and for CP-SAT it also yielded lower penalties at both contrasts. The greedy constructor showed no benefit from additional time.

At 30 seconds, CP-SAT's penalty exceeded SCIP's in all 12 matched cases. At 60 seconds it exceeded SCIP's in 11 and tied in `high-mixed/reversed`, where CP-SAT still reported `FEASIBLE`. Because the shared model has the same feasible set and objective in both encodings, SCIP's proof establishes that the equal-valued CP-SAT incumbent was also optimal for that case, even though CP-SAT had not proved it within its own run.

*Table 4.10. Median observed allocation total (seconds) on the same 12 matched cases, including no-map executions.*

| Configured search allowance | CP-SAT | SCIP | Greedy |
| --- | ---: | ---: | ---: |
| 5 s | 10.52 | 5.42 | 0.88 |
| 30 s | 35.62 | 10.80 | 0.90 |
| 60 s | 65.64 | 10.76 | 0.86 |

CP-SAT's allocation totals rose with the allowance because its single-worker search generally consumed the whole limit without completing a proof. SCIP's 30- and 60-second totals were similar because those runs terminated once optimality was proved. At 30 seconds, CP-SAT totals ranged from 33.76 to 37.10 seconds against SCIP's 8.37 to 14.70, and at 60 seconds from 63.74 to 66.74 against 8.39 to 14.71, so SCIP was faster in every matched longer-allowance comparison in this configuration. Greedy's short times frequently measured failed attempts and must be read alongside its 2/12 coverage.

### 4.3.5 Recorded timing phases at the 60-second allowance

Figure 4.5 decomposes each 60-second execution into its recorded phases.

![Figure 4.5. Recorded allocation phases for all 36 controlled 60-second executions.](solver-selection-v4-attempt3-figures-2026-10-23/figures/a5-phase-timing-60s.svg)

*Figure 4.5. Disjoint recorded phases (preprocessing, model or construction, search call, extraction, validation and scoring, and residual overhead) for four events × three active settings × three methods at the 60-second search allowance. Each bar is one execution. Source: [phase-timing table][a-phase-table].*

Across the 12 CP-SAT 60-second cases, model building took 3.11–5.83 seconds and the search call 60.01–60.05 seconds. The corresponding SCIP ranges were 0.21–0.34 seconds and 7.23–13.79 seconds. Native SCIP presolve is included within its search call and is not isolated as a separate phase. Table 4.11 illustrates the distinction between configured allowance and observed time on the Emperor-heavy case.

*Table 4.11. SCIP timing on `heavy-mixed/current` in Study A (seconds; each allowance is a separate fresh run).*

| Search allowance | Result | Model build | Search call | Allocation total |
| --- | --- | ---: | ---: | ---: |
| 5 s | `UNKNOWN`, no map | 0.334 | 4.634 | 5.483 |
| 30 s | `OPTIMAL` | 0.295 | 7.211 | 8.370 |
| 60 s | `OPTIMAL` | 0.290 | 7.229 | 8.390 |

A validated optimum was returned in about 8.4 seconds by runs that were permitted up to 30 or 60 seconds of search. The records do not identify when the first feasible or optimal incumbent appeared, and the controlled records provide no comparable first-incumbent timestamps for both backends, so allocation total, search duration and time-to-proof must not be treated as interchangeable.

### 4.3.6 The 230-seat Emperor-heavy case at a common 60-second endpoint

Figure 4.6 illustrates the three methods' physical outcomes on the most constrained individual case, in which 99 Emperor registrations requiring 198 seats, 19 Merit and 13 Bodhi registrations (131 registration units) occupy 230 of 232 usable seats.

![Figure 4.6. CP-SAT, SCIP and greedy on the same 230-seat case at the 60-second search allowance.](solver-selection-v4-attempt3-figures-2026-10-23/figures/a6-230-seat-60s.svg)

*Figure 4.6. `heavy-mixed/current` in Study A with one worker and no canonicalization. CP-SAT returned a validated `FEASIBLE` map, SCIP a validated `OPTIMAL` map and greedy no map. Yellow indicates Emperor seats, blue Merit, green Bodhi, grey blocked positions and white unused usable seats; outlines identify Emperor pairs. Sources: [endpoint table][a-heavy-table], the saved placements and their independent audits.*

*Table 4.12. The 230-seat current-setting case across Study A allowances. Penalties use the Study A scale; elapsed values are observed allocation totals.*

| Method | Allowance | Outcome | Penalty | Allocation total (s) |
| --- | ---: | --- | ---: | ---: |
| CP-SAT | 5 s | `FEASIBLE` | 22,722 | 11.566 |
| CP-SAT | 30 s | `FEASIBLE` | 21,935 | 37.035 |
| CP-SAT | 60 s | `FEASIBLE` | 21,679 | 66.729 |
| SCIP | 5 s | `UNKNOWN`, no map | — | 5.483 |
| SCIP | 30 s | `OPTIMAL` | 20,515 | 8.370 |
| SCIP | 60 s | `OPTIMAL` | 20,515 | 8.390 |
| Greedy | 5 / 30 / 60 s | `CONSTRUCTION_FAILED` | — | 0.820 / 0.793 / 0.797 |

CP-SAT established a complete map at five seconds when SCIP did not, but SCIP established the common minimum of 20,515 at both longer allowances and returned sooner than CP-SAT's corresponding runs. Relative to that minimum, CP-SAT's single-worker penalty was 2,207 units (10.76%) higher at five seconds and 1,164 units (5.67%) higher at 60 seconds. Greedy's failure at every allowance is consistent with the risk of irreversible local commitments in a highly occupied joint assignment problem, but the records do not isolate a particular rule as the cause. The missing panel denotes no validated allocation, not a zero penalty and not infeasibility.

### 4.3.7 Production-path verification checks

The four production-path checks ran the prototype CP-SAT service on the four large mixed events under the current setting, with eight workers, a requested canonical tie-break stage and a 60-second configuration. Their settings and clocks differ from the controlled trials, so they are excluded from Figures 4.1 to 4.6.

*Table 4.13. Study A production-path CP-SAT checks. Penalties are rescored on the Study A scale. All four maps passed independent validation and proved the weighted objective, while canonicalization did not complete.*

| Event | Penalty | Weighted-objective proof | Canonicalization complete | Service return (s) | Including external audit and persistence (s) |
| --- | ---: | --- | --- | ---: | ---: |
| `high-mixed` | 19,093 | `OPTIMAL` | No | 62.552 | 62.919 |
| `near-mixed` | 23,194 | `OPTIMAL` | No | 62.510 | 62.941 |
| `full-mixed` | 24,959 | `OPTIMAL` | No | 62.600 | 63.070 |
| `heavy-mixed` | 20,515 | `OPTIMAL` | No | 62.487 | 62.897 |

Sources are the raw prototype records for [`high-mixed`][a-prototype-high], [`near-mixed`][a-prototype-near], [`full-mixed`][a-prototype-full] and [`heavy-mixed`][a-prototype-heavy]. Every penalty equals the corresponding controlled SCIP optimum, so eight-worker CP-SAT reached and proved the same minima that single-worker CP-SAT did not prove within 60 seconds. The service returns of approximately 62.5 seconds reflect a configuration in which the canonical tie-break stage was allowed to use the remaining allowance after the weighted proof; the records do not contain a comparable weighted-proof timestamp, so these totals are not times to the first optimum. Canonicalization selects one physical map among equally penalized alternatives using a fixed ordered tie-break, and an `OPTIMAL` weighted status alone does not show that this selection finished. Four completed jobs with incomplete canonicalization are therefore not counted as invalid allocations or incomplete executions.

### 4.3.8 Summary of Study A

Study A identified a trade-off that depends on the search allowance. CP-SAT returned the most validated maps at five seconds; SCIP never had a higher penalty in the 26 both-valid five-second pairs and, on the predefined longer-budget subset, reached complete coverage with proven optima and shorter allocation times in the single-worker configuration. The greedy constructor's low coverage and consistently higher both-valid penalties excluded it as a sole initial allocator. The production-path checks, however, showed that the single-worker comparison could not settle how CP-SAT would perform in the configuration actually used by the system. This unresolved question motivated Study B.

## 4.4 Study B: production initial-allocation benchmark

Study B compared CP-SAT and SCIP through the local production initial-allocation service. Both backends used eight workers (native concurrent solvers for SCIP), the canonical tie-break stage was off under the agreed contract, and every returned candidate was independently rescored before adoption. The agreed selection hierarchy, fixed before execution, compares valid-map coverage at 60 seconds first, then penalty on matched valid cases, then proof coverage and finally complete local service-return time, with zero invalid adopted maps required throughout. Identical-request repeatability of the physical map is assigned to the application's result cache and is not a selection criterion; that cache was not exercised in this study. The underlying evidence is the [Study B attempt 3 bundle][b-evidence], including its [manifest][b-manifest], [audit][b-checks], [run records][b-runs], [coverage table][b-coverage], [matched objectives][b-paired] and [phase timing][b-phase].

### 4.4.1 Coverage and proof by allowance

Figure 4.7 shows valid-map and proof coverage at the three fresh allowances, and Table 4.14 gives the full outcome breakdown.

![Figure 4.7. Study B valid-map and weighted-proof coverage at the three fresh allowances.](study-b-windows-2026-10-23-attempt3/figures/attempt3-coverage-by-allowance.svg)

*Figure 4.7. Share of the 24 scheduled jobs per backend that produced an adopted validated map (left) and an adopted map with a proven weighted optimum (right) at shared function allowances of 5, 30 and 60 seconds. The two panels coincide because every adopted map was proven. Lines join independent endpoint summaries and do not represent progress within a single solve. Source: [coverage table][b-coverage]. Vector versions: [PDF][b-fig-coverage-pdf] and [SVG][b-fig-coverage-svg].*

*Table 4.14. Study B outcomes by allowance and backend (24 scheduled jobs each; all 144 jobs completed).*

| Allowance | Backend | Adopted valid maps | Proven (`OPTIMAL`) | `FEASIBLE` | `late_candidate` | `no_map` | Invalid / execution error |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 s | CP-SAT | 0 | 0 | 0 | 3 | 21 | 0 / 0 |
| 5 s | SCIP | 0 | 0 | 0 | 0 | 24 | 0 / 0 |
| 30 s | CP-SAT | 24 | 24 | 0 | 0 | 0 | 0 / 0 |
| 30 s | SCIP | 17 | 17 | 0 | 7 | 0 | 0 / 0 |
| **60 s (primary)** | **CP-SAT** | **24** | **24** | 0 | 0 | 0 | 0 / 0 |
| **60 s (primary)** | **SCIP** | **24** | **24** | 0 | 0 | 0 | 0 / 0 |

At the primary 60-second allowance both backends adopted 24 of 24 validated maps and proved the weighted optimum in all 24, with zero invalid adopted maps. The first decision criterion and the proof criterion therefore tie. The diagnostic endpoints differ: at 30 seconds CP-SAT adopted and proved all 24 maps, whereas SCIP adopted 17, and at five seconds neither backend adopted any map. These diagnostic outcomes are examined in Section 4.4.5.

### 4.4.2 Preference penalty at 60 seconds

Figure 4.8 plots the CP-SAT-minus-SCIP penalty difference for every matched active-preference execution at 60 seconds, and Table 4.15 lists the proven optimum of each event–setting pair.

![Figure 4.8. Matched active-preference penalty differences at 60 seconds.](study-b-windows-2026-10-23-attempt3/figures/attempt3-matched-penalties.svg)

*Figure 4.8. CP-SAT penalty minus SCIP penalty for the 21 matched active-preference executions at the 60-second allowance (seven event–setting pairs × three executions; the third execution of each pair uses the permuted input). The disabled-preference control is excluded. Every difference is exactly zero. Source: [matched objectives][b-paired]. Vector versions: [PDF][b-fig-penalty-pdf] and [SVG][b-fig-penalty-svg].*

*Table 4.15. Proven production-scale optima at 60 seconds and their relationship to Study A. Study B values are identical for both backends and all three executions. The common-scale value divides the production penalty by ten, which is exact because the production coefficients are ten times the Study A coefficients in every setting.*

| Event / setting | Study B optimum (production scale) | Common-scale value (÷10) | Best Study A result on the same case | Relationship |
| --- | ---: | ---: | --- | --- |
| `typical-mixed/current` | 154,960 | 15,496 | SCIP `OPTIMAL` 15,496 (5 s) | Identical optimum |
| `high-mixed/current` | 190,930 | 19,093 | SCIP `OPTIMAL` 19,093 (30/60 s) | Identical optimum |
| `near-mixed/current` | 231,940 | 23,194 | SCIP `OPTIMAL` 23,194 (30/60 s) | Identical optimum |
| `full-mixed/current` | 249,590 | 24,959 | SCIP `OPTIMAL` 24,959 (30/60 s) | Identical optimum |
| `heavy-mixed/current` | 205,150 | 20,515 | SCIP `OPTIMAL` 20,515 (30/60 s) | Identical optimum |
| `full-conflict/reversed` | 299,120 | 29,912 | CP-SAT `FEASIBLE` 34,870 (5 s) | Study A incumbent 16.58% above the later proven optimum |
| `full-accessible/two` | 178,870 | 17,887 | CP-SAT `FEASIBLE` 20,815 (5 s) | Study A incumbent 16.37% above the later proven optimum |
| `full-tied/disabled` | 0 | 0 | CP-SAT `OPTIMAL` 0 (5 s) | Control; no quality information |

All 21 active-preference differences were exactly zero, so neither backend has a measured preference-quality advantage on this cohort, and the second decision criterion also ties. Equal proven penalties do not imply identical seat-by-seat allocations, because several physical maps can attain the same minimum where the compulsory rules permit equivalent assignments. The permuted-input execution of each pair returned the same proven optimum as the two original-order executions for both backends, which indicates that the optimal value was insensitive to the tested input ordering, although it says nothing about the physical map selected.

Table 4.15 also provides a cross-harness consistency check. For the five current-setting events, the Study B optimum divided by ten equals the optimum that SCIP proved independently in Study A, with no discrepancy in any case. This agreement between two separately implemented harnesses, two solver backends and two coefficient scales supports the claim that the production service and the Study A benchmark encode the same mathematical allocation problem on these inputs. For the conflict and accessibility scenarios, which Study A tested only at five seconds and for which it obtained only unproved CP-SAT incumbents, Study B supplies the first proven optima; the Study A incumbents were about 16.4–16.6% above them on the common scale.

### 4.4.3 Complete local service-return time at 60 seconds

Because the first three criteria tie, the selection rests on the fourth: complete local service-return time. Figure 4.9 plots every primary call.

![Figure 4.9. Paired complete local service-return times at 60 seconds.](study-b-windows-2026-10-23-attempt3/figures/attempt3-complete-service-time.svg)

*Figure 4.9. Complete local service-return time for every primary job, grouped by event and execution (executions 1 and 2 use the original input order; execution 3 uses the permuted input). Circles denote CP-SAT and squares SCIP. The dashed line marks the 60-second function allowance; all calls returned before it. Source: [run records][b-runs]. Vector versions: [PDF][b-fig-time-pdf] and [SVG][b-fig-time-svg].*

*Table 4.16. Primary 60-second decision measures (24 matched jobs per backend).*

| Decision measure (in priority order) | CP-SAT, eight workers | SCIP, eight concurrent solvers | Result |
| --- | ---: | ---: | --- |
| Invalid adopted maps (gate) | 0 | 0 | Both pass |
| 1. Adopted valid maps | 24 / 24 | 24 / 24 | Tie |
| 2. Matched active-preference penalty | Equal in 21 / 21 pairs | Equal in 21 / 21 pairs | Tie |
| 3. Proven weighted optima | 24 / 24 | 24 / 24 | Tie |
| 4. Complete service return, mean (s) | 9.990 | 28.645 | CP-SAT shorter |
| 4. Complete service return, median (s) | 10.515 | 28.616 | CP-SAT shorter |
| 4. Complete service return, range (s) | 5.907–14.274 | 13.061–45.694 | CP-SAT shorter in 24 / 24 pairs |
| Weighted-stage return, mean (s) | 8.449 | 26.511 | Supporting measure |

CP-SAT returned sooner than SCIP in all 24 matched pairs. The paired SCIP-minus-CP-SAT difference had a mean of 18.655 seconds, a median of 17.443 seconds and a range of 6.484 to 39.787 seconds, and the SCIP-to-CP-SAT time ratio had a median of 2.65 (range 1.69–7.73). Excluding the disabled control, the 21 active-preference differences had a median of 17.234 seconds (range 6.484–27.911). The weighted-stage return, which ends when the solver hands back its proven candidate, averaged 8.449 seconds for CP-SAT and 26.511 seconds for SCIP; it is neither a first-feasible time nor the moment an optimal incumbent was first found.

*Table 4.17. Complete local service return by event–setting pair at 60 seconds (seconds; three executions per backend).*

| Event / setting | CP-SAT mean (min–max) | SCIP mean (min–max) | Mean paired difference | Mean ratio SCIP / CP-SAT |
| --- | ---: | ---: | ---: | ---: |
| `typical-mixed/current` | 6.220 (6.039–6.577) | 13.464 (13.061–13.865) | 7.245 | 2.17 |
| `high-mixed/current` | 13.401 (12.153–14.274) | 23.969 (23.281–24.423) | 10.568 | 1.80 |
| `near-mixed/current` | 12.454 (12.148–12.652) | 34.161 (29.241–40.473) | 21.707 | 2.74 |
| `full-mixed/current` | 12.668 (11.148–13.629) | 32.273 (29.488–36.168) | 19.605 | 2.55 |
| `heavy-mixed/current` | 10.375 (10.097–10.701) | 28.566 (27.331–29.466) | 18.191 | 2.75 |
| `full-conflict/reversed` | 10.643 (10.163–10.896) | 27.884 (26.419–28.891) | 17.241 | 2.63 |
| `full-accessible/two` | 7.958 (7.843–8.099) | 24.330 (23.614–25.512) | 16.372 | 3.06 |
| `full-tied/disabled` | 6.198 (5.907–6.439) | 44.509 (42.971–45.694) | 38.311 | 7.20 |

The separation held in every pair, every execution and every preference setting, so it is not caused by a single outlier. The ranges of the two backends did not overlap within any event–setting pair. The largest gap occurred in the disabled-preference control, where CP-SAT returned in about 6.2 seconds and SCIP in about 44.5 seconds even though the objective is zero by construction; this suggests that SCIP's time in that case was spent in establishing a feasible assignment and its trivial optimality under the compulsory rules rather than in trading off preferences, though the records do not isolate the solver's internal activity. SCIP also showed more variation between executions, most visibly in `near-mixed/current` (29.2–40.5 seconds), whereas CP-SAT's executions of the same pair spanned 12.1–12.7 seconds. The permuted executions did not change the direction of the result: the CP-SAT mean was 10.156 seconds over original-order executions and 9.656 seconds over permuted ones, against 28.415 and 29.103 seconds for SCIP. Three executions per case describe observed variation and do not estimate tail latency.

### 4.4.4 Where the time is spent

Table 4.18 decomposes the mean primary service time into the recorded phases, which sum to the complete service return.

*Table 4.18. Mean recorded phase durations for the 24 primary jobs per backend (seconds). Source: [phase timing][b-phase].*

| Phase | CP-SAT | SCIP | Difference (SCIP − CP-SAT) |
| --- | ---: | ---: | ---: |
| Normalization | 0.085 | 0.089 | 0.004 |
| Model build | 5.366 | 5.364 | −0.002 |
| Model updates | 0.023 | 0.005 | −0.018 |
| Weighted search | 2.975 | 21.053 | 18.078 |
| Extraction | 0.015 | 0.021 | 0.006 |
| Validation and scoring | 0.439 | 0.387 | −0.052 |
| Response formatting | 0.288 | 0.252 | −0.036 |
| Other function work | 0.026 | 0.749 | 0.723 |
| Service overhead (persistence and encoding) | 0.772 | 0.725 | −0.047 |
| **Complete service return** | **9.990** | **28.645** | **18.655** |

The weighted search phase accounts for 18.078 of the 18.655-second mean difference (96.9%), and model building took almost exactly the same time for both backends (means of 5.366 and 5.364 seconds). The production comparison is therefore a comparison of search and proof time on a common model-building pipeline rather than a comparison of model construction. Weighted search ranged from 1.318 to 6.688 seconds for CP-SAT and from 8.180 to 41.794 seconds for SCIP. A further observation is that model building constituted 53.7% of CP-SAT's mean service time, against 29.8% for weighted search. Once CP-SAT is retained, model construction rather than search is the largest component of its response time on these cases. The work performed after the weighted stage (validation, formatting, persistence and encoding, measured as complete return minus weighted-stage return) averaged 1.541 seconds for CP-SAT (0.527–2.252) and 2.134 seconds for SCIP (1.443–2.766). These phase labels belong to the production harness and should not be compared directly with the Study A phase values in Section 4.3.5, which were recorded by a different pipeline with different model-construction code paths.

### 4.4.5 Diagnostic endpoints at 5 and 30 seconds

The diagnostic endpoints show how the shared function clock interacts with each backend. Table 4.19 lists every late candidate.

*Table 4.19. Late candidates in the Study B diagnostic endpoints. Each was complete and passed independent rescoring but was not adopted because its weighted stage returned after the allowance.*

| Allowance | Backend | Event / setting | Execution | Weighted-stage return (s) | Candidate status | Production-scale penalty |
| ---: | --- | --- | ---: | ---: | --- | ---: |
| 5 s | CP-SAT | `typical-mixed/current` | 1 | 5.067 | `FEASIBLE` | 192,760 |
| 5 s | CP-SAT | `typical-mixed/current` | 2 | 5.076 | `FEASIBLE` | 193,330 |
| 5 s | CP-SAT | `typical-mixed/current` | 3 | 5.037 | `OPTIMAL` | 154,960 |
| 30 s | SCIP | `near-mixed/current` | 1 | 31.395 | `OPTIMAL` | 231,940 |
| 30 s | SCIP | `near-mixed/current` | 3 | 30.066 | `OPTIMAL` | 231,940 |
| 30 s | SCIP | `full-mixed/current` | 3 | 31.652 | `OPTIMAL` | 249,590 |
| 30 s | SCIP | `heavy-mixed/current` | 2 | 32.672 | `OPTIMAL` | 205,150 |
| 30 s | SCIP | `full-tied/disabled` | 1 | 37.536 | `OPTIMAL` | 0 |
| 30 s | SCIP | `full-tied/disabled` | 2 | 38.529 | `OPTIMAL` | 0 |
| 30 s | SCIP | `full-tied/disabled` | 3 | 36.999 | `OPTIMAL` | 0 |

At five seconds, normalization plus model building alone consumed at least five seconds in 14 of 24 CP-SAT jobs and 15 of 24 SCIP jobs (medians of 5.623 and 5.803 seconds), so the shared allowance frequently left no time for weighted search at all. The only complete candidates were three CP-SAT candidates for the moderate-demand `typical-mixed/current` case that returned between 37 and 76 milliseconds after the boundary; one of them was already the proven optimum. The five-second result is therefore a consequence of the service clock and of model-construction time, not evidence that either solver cannot find a map within five seconds of search. It also cannot be compared directly with Study A's five-second *search* allowance, under which CP-SAT returned 50 of 63 active-setting maps.

At 30 seconds, CP-SAT adopted and proved all 24 maps, with adopted weighted stages returning between 5.072 and 12.417 seconds. SCIP adopted 17, and its seven non-adopted candidates were all valid and proven but returned between 30.066 and 38.529 seconds. The correct SCIP coverage at 30 seconds is 17/24 rather than 24/24, because the contract forbids adopting a late candidate; this is a service-boundary outcome and not evidence that those instances lacked an optimal solution. The 30-second endpoint nevertheless indicates that CP-SAT retained a substantial margin below the 60-second setting in this configuration, whereas SCIP did not, since all 24 CP-SAT complete returns at 30 seconds were at most 14.494 seconds.

### 4.4.6 Computational resource use

Table 4.20 reports process-level resource measurements for the primary jobs. They are descriptive observations from fresh worker processes, including native solver threads, and are not decision criteria under the agreed hierarchy.

*Table 4.20. Resource use of the 24 primary jobs per backend.*

| Measure | CP-SAT | SCIP |
| --- | ---: | ---: |
| Service process CPU time, mean (median; range) | 19.695 s (16.562; 10.141–42.828) | 119.747 s (114.977; 53.219–180.562) |
| Peak working set, mean (range) | 187.9 MiB (158.1–216.3) | 995.8 MiB (650.4–1,790.6) |
| Mean CPU time ÷ mean complete service return | ≈ 1.97 | ≈ 4.18 |

SCIP consumed about six times as much CPU time and about five times as much peak memory as CP-SAT on average. The ratio of CPU time to wall time indicates that SCIP's concurrent mode kept more cores busy for longer, whereas CP-SAT completed its search with less aggregate computation. The peak working set is a Windows process-lifetime measurement and not a per-stage memory profile, and the native SCIP logs establish that eight concurrent solvers were launched rather than measuring their sustained utilization. These measurements are relevant to deployment sizing, because a function environment with constrained memory or concurrent requests would penalize the larger SCIP footprint, but they do not constitute a controlled capacity test.

### 4.4.7 Application of the selection hierarchy

Under the agreed hierarchy and the tested eight-worker, 60-second initial-generation configuration, CP-SAT and SCIP tie on valid-map coverage, matched active-preference penalty and proof coverage, and both pass the zero-invalid gate. CP-SAT then returns the complete local service response sooner in all 24 matched executions, by a median of 17.4 seconds. The Study B result therefore supports retaining CP-SAT as the initial-generation solver for this configuration. The secondary diagnostic and resource observations point in the same direction, since CP-SAT achieved full coverage at the 30-second endpoint and used less CPU time and memory, but the selection does not depend on them.

## 4.5 Discussion

### 4.5.1 Answers to the research questions

The H1 prediction is supported in each of the three active preference settings in which it could be estimated: CP-SAT had a lower penalty than the greedy constructor in all 11 both-valid five-second pairs, with negative medians of −22.21, −13.10 and −16.94 units per registration under the current, reversed and two-preference settings respectively. The support is conditional on both methods returning a map, which happened in only 11 of the 63 active cases, and the greedy constructor's speed advantage remained visible within those pairs. Its 20.6% active-setting coverage, its inability to benefit from additional time and its failure on every disabled-setting case indicate that a single-pass constructor is not a suitable sole allocator for this tightly packed joint assignment problem. This conclusion applies to the implemented constructor and not to every conceivable heuristic.

The answer to RQ1 depends on the configuration. In Study A's single-worker setting, CP-SAT had the greater five-second availability, while SCIP had equal or lower penalties in every both-valid comparison, proved every longer-budget optimum and returned sooner at 30 and 60 seconds. In Study B's eight-worker production setting, both solvers proved every optimum at 60 seconds and CP-SAT returned sooner in every matched execution. Neither solver is therefore universally superior across the tested configurations, and the single-worker comparison alone would have led to the wrong production conclusion for the configuration the system actually uses.

H3 is supported for both exact solvers on the predefined Study A subset. Moving from five to 30 seconds yielded four additional CP-SAT maps and ten additional SCIP maps, and CP-SAT's penalties continued to fall from 30 to 60 seconds without reaching proof. For SCIP, the 30-to-60-second contrast produced only ties, so 30 seconds matched the 60-second outcome on those cases. In Study B, the comparable observation is that the 30-second endpoint already gave CP-SAT complete proven coverage, whereas SCIP required the 60-second allowance for seven of its 24 jobs. Neither study establishes a minimum necessary allowance.

For the verification question, the Study A production-path checks showed that the prototype CP-SAT path returned validated, proven-optimal maps on all four large mixed events under its 60-second configuration, but with service returns of approximately 62.5 seconds and incomplete canonicalization. Study B, with canonicalization turned off, obtained the same proven optima on the same four events in mean complete service returns of 10.4–13.4 seconds. The comparison is consistent with the interpretation that the earlier totals were dominated by the canonical tie-break stage consuming the remaining allowance rather than by the weighted solve, although the Study A records lack the timestamps needed to confirm this.

RQ2 is answered by Section 4.4.7: under the agreed selection contract and the tested configuration, CP-SAT is retained as the initial-generation solver.

### 4.5.2 Why the solver ranking changed between the studies

Table 4.21 juxtaposes the two studies on the measures they share. The apparently opposite timing rankings are not contradictory, because they describe different configurations and different measured quantities.

*Table 4.21. Corresponding observations in Study A and Study B.*

| Evidence | Study A (controlled, one worker) | Study B (production service, eight workers) |
| --- | --- | --- |
| Short endpoint | 5-s **search** allowance: active-setting valid maps CP-SAT 50/63, SCIP 26/63, greedy 13/63 | 5-s **function** allowance: 0/24 adopted maps for each backend; model building often consumed the allowance |
| Longer-endpoint coverage | 12/12 for both exact solvers at 30 and 60 s on four large mixed events | 24/24 for both at 60 s; at 30 s CP-SAT 24/24 and SCIP 17/24 (seven valid proven candidates were late) |
| Proof at 60 s | SCIP 12/12; CP-SAT 0/12 | Both 24/24 |
| Penalty at 60 s | CP-SAT higher in 11 of 12 cases, equal in one | Equal in all 21 active pairs |
| Observed time at 60 s | SCIP shorter in 12/12; medians 10.76 s versus 65.64 s (allocation total) | CP-SAT shorter in 24/24; means 9.990 s versus 28.645 s (complete service return) |
| `heavy-mixed/current` | CP-SAT `FEASIBLE` 21,679 in 66.729 s; SCIP `OPTIMAL` 20,515 in 8.390 s | Both `OPTIMAL` 205,150 (= 20,515 × 10); means 10.375 s versus 28.566 s |

The most plausible contributor to the reversal is parallelism. CP-SAT is designed as a portfolio solver that runs diverse search strategies, including lazy clause generation with conflict-driven learning, linear-relaxation bounding and large-neighbourhood search, in parallel workers that share bounds and solutions (Perron & Didier, 2023; Stuckey, 2010). With a single worker, this portfolio is reduced to one strategy, which is consistent with Study A's observation that CP-SAT improved its incumbents steadily but did not complete proofs within 60 seconds. With eight workers, both the Study A production-path checks and Study B show CP-SAT proving the same optima that single-worker CP-SAT could not. SCIP, a branch-and-bound solver built on linear-programming relaxations (Williams, 2013), proved optima quickly with one thread in Study A, but its concurrent mode in Study B was slower and far more resource-intensive. A plausible reading is that the gain from adding concurrent SCIP instances on six physical cores did not offset their overhead on these models, but this was not isolated.

Other factors also differ between the two studies and cannot be separated from parallelism in the present data: the model-construction code paths and their phase boundaries, the clock definitions, the selection of eight event–setting pairs, the repeated executions, and the service's independent validation and persistence. The exact correspondence of the optima in Table 4.15 does rule out one candidate explanation: the change in objective scale did not alter the optimization problem being solved. The optional 96-job worker/thread sensitivity sweep, which would compare 1, 2, 4 and 8 workers or native threads on four predefined pairs, is the appropriate experiment for testing the effect of parallelism directly, and it has not been executed.

### 4.5.3 Feasibility, preference quality and proof as distinct claims

Across both studies, the results support keeping three claims separate. A validated map establishes that the implemented compulsory rules were satisfied by the returned allocation. Its penalty describes performance under the chosen preference coefficients. A proof establishes that no lower penalty exists within the declared model, subject to solver correctness and tolerance. Study A contained many valid but unproved CP-SAT maps whose penalties were later shown to be above the optimum, and one, in `high-mixed/reversed`, that was optimal without being proved so by CP-SAT itself. Study B contained valid, proven SCIP maps that could not be adopted because they arrived late. A lower penalty never implied fewer compulsory-rule violations, since every map admitted to a quality comparison had already passed the hard-rule audit. This separation follows the valued-constraint view in which compulsory rules define the feasible space and preferences are optimized within it (Schiex et al., 1995; Rossi et al., 2006), and it justifies the system's practice of reporting solver status alongside the validated map rather than presenting every returned map as optimal.

The same separation bounds the theoretical interpretation. CP-SAT and SCIP are solution technologies applied to encodings of one allocation problem; using a different solver does not change the problem's rules or objective. The empirical differences concern how quickly each technology finds, improves and proves solutions on these encodings and configurations, not which mathematical allocation is correct.

### 4.5.4 Implications for Objective 1 and the system design

The results support the claim that the implemented approach can express PJKIT's compulsory rules and configurable preferences and generate complete, independently validated and proven-optimal seating allocations for the evaluated synthetic events within the system's 60-second engineering setting. On the eight Study B pairs, which span 96 to 152 registration units and up to every one of the 232 usable seats, the production CP-SAT service returned 24 of 24 proven-optimal maps with complete service returns of at most 14.274 seconds. This is supportive rather than conclusive evidence for the Objective 1 success criterion stated in the interim report, because that criterion specifies a default 122-participant scenario, which neither study used directly, and a comparison against random and first-come-first-served baselines in addition to greedy, which were not executed. The criterion that the engine's penalty should be strictly lower than every automated baseline is supported against the implemented greedy constructor in all 11 estimable pairs but remains untested against the other planned baselines.

Several design consequences follow. First, the CP-SAT default should be retained for initial generation rather than refactored to SCIP on the strength of Study A's single-worker results; Study A remains valid evidence about its own configuration and explains why the production benchmark was necessary. Second, a five-second shared allowance is not viable in the current pipeline, because model construction alone takes about five seconds on the larger events. If shorter staff-facing response times become a requirement, the evidence points to model construction, which accounted for more than half of CP-SAT's mean service time, as the principal target for optimization. Third, the canonical tie-break stage should not be allowed to consume the whole remaining allowance by default, since the Study A production-path checks suggest that it can extend a roughly ten-second proven result to more than 60 seconds without improving the penalty; repeatable physical maps for identical requests are better provided by the application's result cache, which remains to be tested. Fourth, the substantially smaller CPU and memory footprint of CP-SAT is favourable for the planned serverless deployment, in which memory allocation affects cost and concurrency, although this was not measured in the deployment environment.

These results also relate to the wider seating-allocation literature. Ipsen et al. (2026) used exact integer programming for seating sub-problems in large organizations, and the present results confirm that exact methods are computationally viable for single-hall problems of PJKIT's scale, provided that the solver configuration is chosen with care. The finding that a constraint-aware greedy constructor frequently reached dead ends in highly occupied layouts is consistent with the motivation for formal constraint modelling in the interim literature review, where bespoke rule-based construction was expected to struggle with tightly coupled pairing, ordering and packing rules.

## 4.6 Threats to validity

**Construct validity.** The penalty measures alignment with the encoded preference model under assumed coefficients, not attendee experience or staff satisfaction, and it has not been validated with participants. An optimal result is optimal for the declared objective only, and the disabled setting produces no meaningful quality ranking. The clocks are engineering measurements: Study A's allocation total and Study B's complete local service return both exclude interpreter start-up, browser rendering and network latency, and no staff response-time requirement has been established against which to judge them. Neither study recorded comparable first-feasible or first-optimal timestamps, so neither supports claims about time-to-first-solution.

**Internal validity.** The comparisons are controlled within each study: matched cases share identical inputs, compulsory rules and coefficients, and every candidate was independently validated. Between the studies, however, parallelism, model-construction paths, clocks, case selection and repetition all differ simultaneously, so the reversal of the timing ranking cannot be attributed to any single factor. Study B was run from a working tree in which the benchmark harness files had uncommitted modifications relative to the recorded Git revision; the manifest's source hashes and preserved source snapshot identify the exact code executed and confirm it did not change during the run, but reproduction requires that snapshot rather than the revision alone. The checkpoint repair between attempts 2 and 3 changed persistence only and its retry delays fall inside the measured clock; no records from the failed attempt are pooled.

**External validity.** All inputs are known-feasible synthetic scenarios on one 232-seat layout and one Windows workstation with six physical cores. The events are related constructed variants rather than independent samples of real PJKIT assemblies, and Study B covered eight of Study A's 84 event–setting combinations. The results do not characterize infeasible requests, other layouts, other hardware, the planned AWS Lambda deployment environment or concurrent request load. The tested CP-SAT and SCIP configurations are those recorded; other parameter settings or solver versions may behave differently.

**Statistical conclusion validity.** Study A has one execution per case, method and allowance, and Study B has three executions per case and backend, one of them under a permuted input. These designs describe observed behaviour and its variation on the tested cases; they do not estimate population reliability, runtime variance or tail latency, and no inferential statistics are claimed. Conditional both-valid penalty comparisons necessarily omit unsuccessful pairs, which is why coverage counts are always reported beside them. Repeated equality of an optimal value across executions is not a test of physical-map determinism.

**Scope of the evidence.** Neither study evaluated the result cache, regeneration after a change of preference settings, or absence-driven repair under Objective 2. Those behaviours require their own evaluation, using the movement-first metrics defined in the evaluation methodology, and cannot be inferred from initial-allocation optima.

## 4.7 Chapter summary

This chapter evaluated the seating allocation engine through two complementary experiments. The controlled Study A showed that the implemented greedy constructor was fast but returned too few complete maps to serve as the sole allocator, that CP-SAT had the greatest availability under a five-second single-worker search allowance, and that SCIP proved every optimum and returned sooner on the larger single-worker allowances. The production Study B, which tested the configuration the system actually uses, showed that with eight workers and a 60-second shared function allowance both solvers returned complete, independently validated and proven-optimal maps on all 24 primary jobs with identical penalties, and that CP-SAT returned the complete service response sooner in all 24 matched executions, at a median of 10.5 seconds against SCIP's 28.6 seconds and with substantially lower CPU and memory use. The production optima also matched Study A's independently proved optima exactly after accounting for the tenfold coefficient scale, which supports the consistency of the two encodings.

Under the selection hierarchy agreed before execution, CP-SAT is retained as the initial-generation solver for the tested configuration. This is a conditional engineering choice for the evaluated service path and synthetic cases, not a claim that CP-SAT is universally faster or that every future event will be proved optimal within 60 seconds. The remaining evidence needs are a worker/thread sensitivity sweep to isolate the effect of parallelism, evaluation of the planned additional baselines and the default 122-participant scenario, measurement in the deployment environment, and the separate evaluation of preference-update regeneration and absence-driven repair, which the next chapter's conclusions and future work must take into account.

## References cited in this chapter

Ipsen, A., Cashmore, M., Fielding, K., Marchesotti, N., Zehtabi, P., Magazzeni, D., & Veloso, M. (2026). *Beyond manual planning: Seating allocation for large organizations*. arXiv:2602.05875. https://arxiv.org/abs/2602.05875

Perron, L., & Didier, F. (2023). The CP-SAT-LP solver (invited talk). In *Proceedings of the 29th International Conference on Principles and Practice of Constraint Programming (CP 2023)* (Article 3). Schloss Dagstuhl – Leibniz-Zentrum für Informatik. https://doi.org/10.4230/LIPIcs.CP.2023.3

Rossi, F., van Beek, P., & Walsh, T. (Eds.). (2006). *Handbook of constraint programming*. Elsevier.

Schiex, T., Fargier, H., & Verfaillie, G. (1995). Valued constraint satisfaction problems: Hard and easy problems. In *Proceedings of the 14th International Joint Conference on Artificial Intelligence (IJCAI-95)* (pp. 631–639). Morgan Kaufmann.

Stuckey, P. J. (2010). Lazy clause generation: Combining the power of SAT and CP (and MIP?) solving. In A. Lodi, M. Milano, & P. Toth (Eds.), *Integration of AI and OR techniques in constraint programming for combinatorial optimization problems* (CPAIOR 2010, LNCS 6140, pp. 5–9). Springer. https://doi.org/10.1007/978-3-642-13520-0_3

Williams, H. P. (2013). *Model building in mathematical programming* (5th ed.). Wiley.

> *Note: These entries are carried over from the interim report's APA 7 reference list and should be merged into the dissertation's consolidated list. The characterization of CP-SAT's portfolio components and SCIP's LP-based branch-and-bound in Section 4.5.2 should be checked against the cited sources before submission.*

## Evidence index

The Study A observations are taken from the [attempt 3 bundle][a-evidence] ([manifest][a-manifest], [run records][a-runs], [input inventory][a-inventory], [correctness audit][a-correctness], [report audit][a-report-audit]) and the [expanded figure package][a-figures], which re-presents those same observations with derived tables and source hashes. The Study B observations are taken from the [attempt 3 bundle][b-evidence] ([manifest][b-manifest], [audit][b-checks], [preflight][b-preflight], [run records][b-runs], [coverage][b-coverage], [matched objectives][b-paired], [phase timing][b-phase]) and its generated [interpretation][b-interpretation]. The [Study A–B synthesis][synthesis] and the [Study B attempt 3 protocol][b-protocol] record the cross-study reasoning and the selection contract. Figures 4.1–4.6 have PDF, SVG and PNG exports in the Study A figure package, including a [combined vector PDF][a-combined-pdf], and Figures 4.7–4.9 have PDF, SVG and PNG exports in the Study B `figures/` folder. For a shorter technical paper, Figures 4.1, 4.2, 4.7 and 4.9 carry the essential availability, proof and timing evidence, and Figure 4.5 is suitable for an appendix.

[study-a-chapter]: solver-selection-v4-attempt3-results-and-discussion.md
[synthesis]: solver-selection-study-a-study-b-attempt3-synthesis.md
[a-evidence]: solver-selection-v4-21-events-135m-windows-main-2026-10-20-attempt3/
[a-manifest]: solver-selection-v4-21-events-135m-windows-main-2026-10-20-attempt3/manifest.json
[a-runs]: solver-selection-v4-21-events-135m-windows-main-2026-10-20-attempt3/tables/run-records.csv
[a-inventory]: solver-selection-v4-21-events-135m-windows-main-2026-10-20-attempt3/inventory.json
[a-correctness]: solver-selection-v4-21-events-135m-windows-main-2026-10-20-attempt3/correctness.json
[a-report-audit]: solver-selection-v4-21-events-135m-windows-main-2026-10-20-attempt3/report-status.json
[a-figures]: solver-selection-v4-attempt3-figures-2026-10-23/README.md
[a-execution-coverage]: solver-selection-v4-attempt3-figures-2026-10-23/tables/execution-coverage.csv
[a-matched-outcomes]: solver-selection-v4-attempt3-figures-2026-10-23/tables/matched-budget-outcomes.csv
[a-original-pairs]: solver-selection-v4-21-events-135m-windows-main-2026-10-20-attempt3/tables/paired-costs.csv
[a-paired-table]: solver-selection-v4-attempt3-figures-2026-10-23/tables/paired-costs.csv
[a-budget-contrasts]: solver-selection-v4-attempt3-figures-2026-10-23/tables/budget-contrasts.csv
[a-phase-table]: solver-selection-v4-attempt3-figures-2026-10-23/tables/phase-timing-60s.csv
[a-heavy-table]: solver-selection-v4-attempt3-figures-2026-10-23/tables/230-seat-endpoints.csv
[a-prototype-high]: solver-selection-v4-21-events-135m-windows-main-2026-10-20-attempt3/runs/prototype__high-mixed__current__cp_sat__60s.json
[a-prototype-near]: solver-selection-v4-21-events-135m-windows-main-2026-10-20-attempt3/runs/prototype__near-mixed__current__cp_sat__60s.json
[a-prototype-full]: solver-selection-v4-21-events-135m-windows-main-2026-10-20-attempt3/runs/prototype__full-mixed__current__cp_sat__60s.json
[a-prototype-heavy]: solver-selection-v4-21-events-135m-windows-main-2026-10-20-attempt3/runs/prototype__heavy-mixed__current__cp_sat__60s.json
[a-combined-pdf]: solver-selection-v4-attempt3-figures-2026-10-23/attempt3-figure-package.pdf
[b-evidence]: study-b-windows-2026-10-23-attempt3/
[b-manifest]: study-b-windows-2026-10-23-attempt3/manifest.json
[b-checks]: study-b-windows-2026-10-23-attempt3/checks.json
[b-preflight]: study-b-windows-2026-10-23-attempt3/preflight.json
[b-runs]: study-b-windows-2026-10-23-attempt3/tables/run-records.csv
[b-coverage]: study-b-windows-2026-10-23-attempt3/tables/coverage.csv
[b-paired]: study-b-windows-2026-10-23-attempt3/tables/paired-objectives.csv
[b-phase]: study-b-windows-2026-10-23-attempt3/tables/phase-timing.csv
[b-interpretation]: study-b-windows-2026-10-23-attempt3/interpretation.md
[b-protocol]: ../planning/solver-selection-production-attempt3.md
[b-fig-coverage-pdf]: study-b-windows-2026-10-23-attempt3/figures/attempt3-coverage-by-allowance.pdf
[b-fig-coverage-svg]: study-b-windows-2026-10-23-attempt3/figures/attempt3-coverage-by-allowance.svg
[b-fig-penalty-pdf]: study-b-windows-2026-10-23-attempt3/figures/attempt3-matched-penalties.pdf
[b-fig-penalty-svg]: study-b-windows-2026-10-23-attempt3/figures/attempt3-matched-penalties.svg
[b-fig-time-pdf]: study-b-windows-2026-10-23-attempt3/figures/attempt3-complete-service-time.pdf
[b-fig-time-svg]: study-b-windows-2026-10-23-attempt3/figures/attempt3-complete-service-time.svg
