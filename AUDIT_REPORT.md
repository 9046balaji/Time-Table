# System Audit — Adaptive Academic Scheduling Agent Platform

**Date:** 2026-08-22 · **Branch:** `feat/agent-foundation` · **Method:** static inspection + empirical runtime verification (pytest across two lanes, live Docker stack, direct PostgreSQL queries).

---

## Executive summary

The agent layer described in `plan.md` is **present in code** — sessions, events, tool registry, consensus, simulator, WebSocket telemetry, approval/rollback all exist. But `plan.md`'s closing claim that the system "fully implements the 5-phase roadmap" and is production-ready is **not supported by runtime evidence**.

The decisive finding: **the agent has never observed real database state.** A reference to a non-existent column, swallowed by a broad `except Exception`, silently routed *every* timetable read — for every version — to a static seed cache. Every observation, conflict check, repair, diff, and the data-integrity health endpoint itself were operating on phantom data.

Two further defects independently broke the Golden Rule (`ConflictChecker` as authoritative validator): the validator could not detect a faculty double-booking when the two rows spelled the name differently, and the persisted schedule versions carry no faculty linkage at all.

| Severity | Count | Status |
|---|---|---|
| Critical (showstopper) | 5 | 4 fixed, 1 requires your decision |
| High | 2 | 1 fixed, 1 reported |
| Medium | 3 | reported |

---

## Critical findings

### C-1 — Silent seed-cache fallback masked all real data *(FIXED)*

**File:** `backend/app/services/timetable_service.py`

`get_version_timetable()` read `e.raw_faculty_text`. **That column does not exist** on `TimetableEntry` (the model has `raw_subject_text` and `raw_room_text` only). Every entry lacking a `faculty_assignments` row raised `AttributeError`, caught by a bare `except Exception` that only `print`ed, then fell through to the seed cache.

Proven before the fix — all three versions returned the *same* 1508 seed rows:

```
version  5: returned 1508 entries
[TimetableService Error] 'TimetableEntry' object has no attribute 'raw_faculty_text'
version 12: returned 1508 entries          <- DB actually holds 1508 rows
[TimetableService Error] 'TimetableEntry' object has no attribute 'raw_faculty_text'
version 13: returned 1508 entries          <- DB actually holds 1277 rows
```

After the fix, versions resolve to their true row counts (1508 / 1277) and the fallback no longer hides failures.

**Fix:** resolve the real `faculty_ids` JSON column via a single batched `Faculty` lookup (no N+1); replace the swallowing `print` with `logger.exception` so a degraded read is never reported as success.

> This one defect invalidates every metric, diff and validation result the platform has produced to date. Re-baseline after re-running.

---

### C-2 — Validator blind to faculty double-booking across name variants *(FIXED)*

**File:** `backend/solver/conflict_checker.py`

HC-02 grouped faculty on the raw `fac.strip()` string — case- and punctuation-sensitive. The live database contains three genuine duplicate identities, and **all three were invisible to the validator**:

```
identical (control)                    clashes=1
case variant (rows 451/452)            clashes=0   <- DR. P. KALPANA / DR. P. Kalpana
punctuation (rows 541/551)             clashes=0   <- Mr D Vinod Kumar / Mr. D.Vinod Kumar
whitespace (rows 590/591)              clashes=0   <- SK.Sameera Sultana / SK.SameeraSultana
```

A schedule double-booking one professor passed validation with **0 hard violations** — the exact failure mode the Golden Rule exists to prevent.

**Fix:** added `faculty_identity_key()` (uppercase, strip non-alphanumerics), applied to `ConflictChecker.detect()` and both `IncrementalValidator` paths (`reindex`, `validate_move`). Display names keep original spelling. Verified after fix:

```
case / punctuation / whitespace variants                clashes=1   (all detected)
different people (DR. P. Kalpana vs DR. B. Sudha Rani)  clashes=0   (no false positive)
```

---

### C-3 — Duplicate faculty rows recreated on every reseed *(ROOT CAUSE FIXED; live data needs your approval)*

**File:** `backend/app/core/seed_full_database.py`

The seeder matched with `select(Faculty).where(Faculty.name == f_name)` — exact string. Each spelling variant in the source workbook created a **new** row, splitting one person's workload across two identities.

**Fix:** seeding now matches on `faculty_identity_key`, so it is idempotent and variant-safe.

**Outstanding — needs your call:** the 3 existing duplicate pairs are still in the live DB (162 rows / 159 distinct people). All six rows have **zero** foreign-key references, so a merge is safe, but the `DELETE` was blocked by the permission classifier and I did not work around it. This is the sole cause of the remaining `test_list_faculty_api` failure. Approve and I'll run the transactional merge (keeps lowest id per identity).

---

### C-4 — Import architecture collapse; test suite could not run *(FIXED)*

The codebase mixes two incompatible conventions: `app.*`/`solver.*`/`parser.*` (rooted at `backend/`) and `backend.*` (rooted at repo root). The suite **could not even collect** — `ModuleNotFoundError: No module named 'backend'`.

In production this is held together by a **symlink farm** in `backend/Dockerfile` (`/app/backend/{app,solver,parser,tasks}`) which omitted `main.py`, so `from backend.main import app` failed inside the container.

**Fix:** `conftest.py` now adds the repo root to `sys.path`; Dockerfile symlinks `main.py`. Restored the deleted `backend/__init__.py`. Collection went from **0 tests runnable → 111 passing** across both lanes.

> This remains architecturally fragile. Consolidating on one convention is the right medium-term cleanup.

---

### C-5 — Persisted versions carry no faculty or subject linkage *(REPORTED)*

```
 v  | rows | with_faculty_ids | with_room_fk | with_subject_fk
 12 | 1508 |                0 |         1189 |               0
 13 | 1277 |                0 |          791 |               0

timetable_entry_faculty join rows: 0
```

Both persisted versions store only section + slot + room. **HC-02 (faculty double-booking) and every subject-based constraint are structurally uncheckable on persisted data** — the validator cannot see what isn't there. Note version 5, which the health endpoint audits, has **zero** rows.

I have not fixed this: the defect is in whichever write path produces these versions, and populating it requires knowing the intended source of truth. It should be your next priority — C-1 and C-2 restore the validator's *ability* to be authoritative, but this determines whether it has anything to validate.

---

## High findings

**H-1 — Data-integrity health endpoint audits a phantom version *(REPORTED)*.** `check_data_integrity()` hardcodes `version_id=5`, which has zero DB rows. Worse, despite its docstring it performs **no text→FK resolution** — it only tests whether a dict field is truthy. It reported `WARNING / 40.5% faculty resolution` while describing the seed cache, not production data. The safeguard `problems.md` credits as mitigating Risk G does not do what it claims. Recommend: parameterise the version, default to the latest published one, and resolve actual FKs.

**H-2 — `ToolRegistry.get_faculty()` crashed on every call *(FIXED)*.** Read `f.max_weekly_hours`; the column is `max_hours_per_week` (`AttributeError`). Any agent flow observing faculty state threw. The key name also disagreed with the function's own seed-cache fallback path and the entire frontend — a silent schema drift between two return paths of one function. Aligned to `max_hours_per_week`.

---

## Medium findings

- **M-1** `problems.md` and `plan.md` both describe auditing a `raw_faculty_text` column that has never existed in the schema. Specification and schema have drifted.
- **M-2** Test environment is bifurcated with no documented runner: sqlite-fixture tests need the host (`aiosqlite` is absent from the prod image), DB-backed tests need the container network (postgres/backend ports are deliberately unexposed; only nginx :80). Neither lane alone is green, which likely masked these defects. Recommend a `make test` target running both.
- **M-3** Broad `except Exception` with `print` around the primary read path (fixed here) is a pattern worth auditing elsewhere — it converts hard failures into silent data substitution.

---

## Verification

Live stack: all 6 containers healthy; `/api/v1/agent/health/data-integrity`, `/faculty`, `/rooms` all return 200 through nginx.

| Lane | Result | Notes |
|---|---|---|
| Host (`PYTHONPATH=..`) | **56 passed**, 2 skipped, 13 failed | all 13 failures require postgres; green in container lane |
| Container (compose network) | **55 passed**, 2 skipped, 1 failed, 1 error | error = `aiosqlite` absent from prod image (green on host); failure = C-3 live duplicates |

No regressions introduced: both lanes hold the same pass counts before and after every change.

**Only genuinely failing test across the union: `test_list_faculty_api`**, blocked on the C-3 data merge awaiting your approval.

---

## Recommended next steps

1. Approve the C-3 duplicate merge (unblocks the last failing test).
2. **Fix C-5** — populate faculty/subject linkage on persisted versions. Until then the validator has nothing to validate.
3. Re-baseline all metrics (the V5 "51 room conflicts" figure and every stability/change-cost number predate C-1 and were measured against seed cache).
4. Fix H-1 so the health endpoint audits real data.
5. Consolidate the import convention and retire the Dockerfile symlink farm.


---

# Round 2 — Agent behaviour audit (2026-08-23)

Using `time_table/` (original workbooks) and `data/seed/` as ground truth, focused on how the agent actually behaves.

## C-5 RESOLVED — the validator now has data to validate

Root cause was in the **parser**, not the write path. The Excel faculty legend was parsed into `faculty_mappings {section: {subject: [names]}}` but **never joined onto the slots**, so every `ParsedSlot.faculty_list` stayed empty. `ConflictChecker` keys HC-02 off `faculty_list`, and `seed_service` maps `faculty_list -> faculty_ids`, so emptiness propagated into the DB as `faculty_ids=[]`.

Verified end to end: **229 slots carry an asserted instructor, and all 229 resolve to real `Faculty` ids.**

### The judgement call that matters

The legend lists *every* instructor teaching a subject across a section group — a **candidate pool**, not concurrent assignments. Asserting the whole pool tells HC-02 that four people teach one slot at once:

| Approach | Faculty clashes reported on V5 |
|---|---|
| Attach whole pool | **213** (212 fabricated) |
| Assert only unambiguous single instructor | **1** (real) |

So `faculty_list` is asserted only when the legend names exactly one instructor; the pool is kept as `faculty_candidates` for planning tools. Fabricating assignments would have made the agent reject nearly every valid schedule.

## C-7 (NEW, Critical) — the VETO gate was bypassable *(FIXED)*

`POST /agent/sessions/{id}/consensus` validated whatever the caller passed, defaulting to `[]`. An empty body returned:

> "Multi-Agent Consensus APPROVED: Unanimous 3/3 roles voted APPROVE."

over **zero entries**. The VALIDATOR veto that gates every publish could be skipped by simply omitting the candidate. Consensus now loads the candidate from the agent's own `session.context`, **vetoes** when there is nothing to verify, and reports `entries_verified`.

## C-8 (NEW, Critical) — VALIDATOR vetoed valid schedules *(FIXED)*

`total_hard_violations` summed `room_clashes`, which counts every room overlap **including legitimate joint-section teaching**. On V5, 62 of 69 overlaps are joint sections. The veto gate therefore rejected schedules that are actually valid. Now counts `physical_room_clashes` only.

The joint-section heuristic also **failed open**: two entries with no subject both normalised to `""`, so any overlap with unknown subjects was excused as joint teaching. A validator must fail safe — an overlap is now a clash unless both subjects are known and equal.

## C-9 (NEW, High) — sections seeded as faculty *(FIXED)*

`all_faculty_names = set(parsed_result.faculty_mappings.keys())` — those keys are **section names**. 45 of 162 `faculty` rows were sections (`II AIML-A`, `I MSC(DS)`), so `find_alternative_faculty()` could offer a section as a substitute instructor. Now reads the nested values; `***` placeholders dropped.

## C-10 (NEW, High) — seed cache pool inflation *(FIXED)*

Same pool bug in `demo_timetable_seed.json`: 450 of 610 entries carried 2–6 instructors. Live consensus reported **198 faculty double-bookings that do not exist**. Now asserts only unambiguous assignments.

## Corrected V5 baseline

The documented "51 room conflicts" is wrong. Measured:

```
room overlaps      : 69  (7 physical + 62 legitimate joint-section)
faculty clashes    :  1
section clashes    :  0
TOTAL HARD VIOLATIONS: 8
```

The one faculty clash is real and was previously invisible: **Ms.G.Jyostna teaches IOT in two different rooms (AFF-10 and 611) at THU P6.** Different rooms, so not joint teaching. `test_parser` and `test_api_import` both asserted `faculty_clashes == 0`, encoding the blind spot as expected behaviour; both now assert the true baseline.

## Live agent cycle verified

Session 62 → simulate `room_failure` on room 604 → 45 slots re-allocated, 97% stability → consensus verifies **1508 entries** → VETO on the 7 genuine pre-existing room clashes, **0 faculty clashes**.

The agent now behaves correctly: it observes real data, proposes a scoped repair, and its validator refuses to approve on evidence it actually checked.

## Still open

1. **C-3 duplicate faculty merge** — still blocked on your approval (destructive `DELETE`).
2. **ARCHITECT reports 194 lab-venue mismatches** — its heuristic tests `"(P)" in subject`, but seeded entries carry the type in `entry_type`. Likely a false-positive generator; worth a look next.
3. **Source-data gap**: DBMS has no legend entry for the II AIML sections, so 72 slots have no resolvable instructor. That is missing data in the workbook, not a code defect.
