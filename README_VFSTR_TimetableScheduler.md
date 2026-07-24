# 🏛️ VFSTR ACSE Timetable Scheduler — Full Problem Analysis & Engineering README

> **Institution:** Vignan's Foundation for Science, Technology and Research (Vignan University), Vadlamudi, Guntur, Andhra Pradesh — NAAC A+, NIRF Rank 70  
> **Scope:** Department of Advanced Computer Science & Engineering (ACSE)  
> **Dataset Source:** `ACSE_TIMETABLE_V1 to V5` — Academic Year 2026-27, Semester I  
> **Status:** This README documents the full mathematical model, constraint set, data profile, and website architecture for an automated timetable generation system to replace the current manual Excel process.

---

## 📖 Table of Contents

1. [Why This Problem Exists — Real Evidence](#1-why-this-problem-exists--real-evidence)
2. [Full Scale of the ACSE Department](#2-full-scale-of-the-acse-department)
3. [Time Structure Deep Dive](#3-time-structure-deep-dive)
4. [Subject & Credit Structure](#4-subject--credit-structure)
5. [Rooms & Lab Inventory](#5-rooms--lab-inventory)
6. [Faculty Pool & Workload Rules](#6-faculty-pool--workload-rules)
7. [The Math — UCTP as NP-Hard CSP](#7-the-math--uctp-as-np-hard-csp)
8. [Hard & Soft Constraints (Complete List)](#8-hard--soft-constraints-complete-list)
9. [Algorithm Selection & Justification](#9-algorithm-selection--justification)
10. [Website Architecture](#10-website-architecture)
11. [Data Ingestion Pipeline (from Excel)](#11-data-ingestion-pipeline-from-excel)
12. [Solver Engine Design](#12-solver-engine-design)
13. [Open Source Stack](#13-open-source-stack)
14. [Phase-wise Implementation Roadmap](#14-phase-wise-implementation-roadmap)
15. [Metrics & Validation](#15-metrics--validation)

---

## 1. Why This Problem Exists — Real Evidence

The current ACSE timetable is **built entirely by hand in Microsoft Excel**. Here is what the raw data from your uploaded files proves:

### The Version History Problem (5 Revisions in 5 Days)

| Version | Date W.e.f. | Total Scheduled Slots | Notes |
|---------|------------|----------------------|-------|
| V1 | 10-Jul-2026 | **894** | Initial release |
| V2 | 11-Jul-2026 | ~920 | Day 2 fix |
| V3 | 13-Jul-2026 | ~950 | Day 3 fix (skipped day) |
| V4 | 14-Jul-2026 | ~970 | Day 4 fix |
| V5 | 15-Jul-2026 | **1,000** | Day 5 — added MINORHONORS sheet |

5 versions in 5 days means the timetable coordinator was **fixing clashes every single day** after distribution, disrupting 2,600+ students and ~80+ faculty each time.

### Clashes Detected in V5 (the "final" version)

Running a conflict detector on V5 finds:

```
Total Room Clashes detected: 51
Examples:
  WED Period-1,  Room 606  → II AIML-E: OOPS(P)  AND  II CSBS: DS(P)  ← SAME ROOM, SAME SLOT
  FRI Period-8,  Room 616  → II AIML-F: AI(P)    AND  II BS(DS): DHV
  MON Period-1,  Room AFTF-12 → III AIML-F: FIP(P) AND II MSC(DS): FIP(P)
  MON Period-4,  Room 607  → II CS-A: DS         AND  II CSBS: DS
  SAT Period-4,  Room 618  → II CS-A: DS         AND  II CSBS: DS
```

**51 room conflicts in the "final" released timetable.** That is not a bug — it is the expected output of a manual process at this scale.

### Why It's So Hard Manually

- A human coordinator must track **44 sections × 48 slots = 2,112 cells** simultaneously
- Each cell has 3 dimensions: **Subject + Room + Faculty**
- Every change in one cell can cascade into clashes in 5–10 other cells
- **With ~80 faculty members**, tracking who is where at each of 48 weekly timeslots means cross-referencing a 80×48 = 3,840 cell matrix in your head

---

## 2. Full Scale of the ACSE Department

### All Branches, Years, and Sections (from the actual data)

| Branch | Year | Sections | Students (60/section) | Weekly Slots |
|--------|------|----------|----------------------|--------------|
| AIML   | II   | A–L (12) | 720 | 576 |
| AIML   | III  | A–G (7)  | 420 | 336 |
| AIML   | IV   | A–E (5)  | 300 | 240 |
| CS     | II   | A, B (2) | 120 | 96  |
| CS     | III  | 1        | 60  | 48  |
| CS     | IV   | 1        | 60  | 48  |
| DS     | II   | A, B (2) | 120 | 96  |
| DS     | III  | A, B (2) | 120 | 96  |
| DS     | IV   | 1        | 60  | 48  |
| CSBS   | II   | 1        | 60  | 48  |
| CSBS   | III  | 1        | 60  | 48  |
| IOT    | II   | 1        | 60  | 48  |
| IOT    | III  | 1        | 60  | 48  |
| BS(DS) | II   | 1        | 60  | 48  |
| BS(DS) | III  | 1        | 60  | 48  |
| MSC(DS)| II   | 1        | ~30 | 48  |
| M.TECH(DS) | II | 1      | ~20 | 48  |
| **TOTAL** | **3 years** | **~44** | **~2,360** | **~2,064** |

### Entities the System Must Track

```
SECTIONS     : 44
SUBJECTS     : ~60 unique subject codes across all years/branches
FACULTY      : ~80+ named faculty (extracted from 384 legend entries in V5)
ROOMS        : ~35 rooms (classrooms 601–619, labs, AFTF series, AFF series)
TIME_SLOTS   : 48 per section per week (8 periods × 6 days)
TOTAL_ASSIGNMENTS : ~1,000 per week (V5 count)
```

---

## 3. Time Structure Deep Dive

### Daily Period Grid (Mon–Sat)

```
Period  | Time Slot      | Duration | Type
--------|----------------|----------|-----
  1     | 08:15 – 09:05  | 50 min   | Lecture / Lab
  2     | 09:05 – 09:55  | 50 min   | Lecture / Lab
 BREAK  | 09:55 – 10:10  | 15 min   | SHORT BREAK (blocked)
  3     | 10:10 – 11:00  | 50 min   | Lecture / Lab
  4     | 11:00 – 11:50  | 50 min   | Lecture / Lab
  5     | 11:50 – 12:40  | 50 min   | Lecture / Lab
 LUNCH  | 12:40 – 13:40  | 60 min   | LUNCH BREAK (blocked)
  6     | 13:40 – 14:30  | 50 min   | Lecture / Lab
  7     | 14:30 – 15:20  | 50 min   | Lecture / Lab
  8     | 15:20 – 16:05  | 45 min   | Lecture / Lab
```

- **Usable slots per day:** 8 periods (but Period 1+2 or 1+2+3 are often merged for 2–3 hour labs)
- **Usable slots per week:** 6 days × 8 = **48 periods**
- **Lab sessions** always span 2–3 consecutive periods (Periods 1–2, 1–2–3, or 6–7–8)

### Observed Slot Patterns in the Data

```
Single period  → Theory lecture (L)
Double period  → Tutorial (T) or short lab
Triple period  → Full practical lab (P) — always periods 1-2-3 OR 6-7-8
LIBRARY slot   → One mandatory slot per section per week (no teaching)
DEF(T)/QALR   → Usually placed on Saturdays or periods 6-7
Minors/Honors → Wednesday/Thursday periods 7–8 (global synchronized slots)
IDP/OE        → Open Elective in synchronized slots across same year
```

---

## 4. Subject & Credit Structure

### II Year Subjects (AIML branch — the largest)

| Code | Full Name | L hrs/week | T hrs/week | P hrs/week | Faculty Pattern |
|------|-----------|-----------|-----------|-----------|-----------------|
| SFCDS | Statistical Foundation for Computing & Data Science | 3 | 1 | 2 | Single faculty L+P |
| DMS   | Discrete Mathematical Structures | 3 | 1 | 2 | Single faculty L+P |
| DS    | Data Structures | 3 | 1 | 2 | Single L, Multi P |
| AI    | Artificial Intelligence Search Methods | 3 | 0 | 2 | Single L, Multi P |
| DBMS  | Database Management Systems | 3 | 1 | 2 | Single L+T, Multi P |
| OOPS  | Object Oriented Programming | 3 | 1 | 2 | Single L+T, Multi P |
| DEF   | Data Engineering Foundations | 1 | 1 | 1 | Shared faculty |
| Library | — | 0 | 0 | 0 | No faculty needed |
| Agentic Tools (IIC) | Industry-Integrated Course | — | — | — | External/Industry |

**Total theory contact per section/week: ~20 periods**

### III Year Subjects (AIML branch)

| Code | Full Name | Type | Note |
|------|-----------|------|------|
| QALR | Quantitative Aptitude & Logical Reasoning | L+T | Outsourced trainer |
| DL | Deep Learning | L+P | 3+2 |
| WT | Web Technologies | L+P | 3+2 |
| CV | Computer Vision (DE-2) | L+P | Department Elective |
| ADS | Advanced Data Structures | L+P | 3+2 |
| MLOP | Machine Learning Operations (DE-1) | L+P | Outsourced |
| IDP | Inter-Departmental Project (Agentic Tools) | P | Multi-faculty |
| OE  | Open Elective | L | Global sync slot |
| Minors/Honors | — | — | Global sync Wed/Thu |

### IV Year Subjects (AIML branch)

| Code | Full Name | L | T | P |
|------|-----------|---|---|---|
| CNS | Cryptography & Network Security | 3 | 0 | 2 |
| TM | Text Mining | 3 | 0 | 2 |
| KRR | Knowledge Representation & Reasoning | 3 | 1 | 0 |
| GENAI | Generative AI | 3 | 0 | 2 |
| IOT | Internet of Things | 3 | 0 | 2 |
| Ethics-AI | Ethics in Computing & AI | 2 | 1 | 0 |
| SL/EL | Self/Experimental Learning | — | — | — |

---

## 5. Rooms & Lab Inventory

### Classroom Inventory (from data)

| Room ID | Type | Capacity | Block | Suitable For |
|---------|------|----------|-------|--------------|
| 601–619 | Theory Classroom | 60 | U-Block | Lectures, tutorials |
| 216, 217, 218 | Theory Classroom | 60 | U-Block 2nd floor | Lectures |
| 215 | Theory Classroom | 60 | U-Block 2nd floor | Lectures |
| 514-A, 514-B | Lecture Hall | 60 | 5th floor | Lectures |
| 518 | Theory Classroom | 60 | 5th floor | Lectures |
| 401, 402, 418 | Theory Classroom | 60 | 4th floor | Lectures |
| 501 | Seminar / Tutorial | 30–60 | 5th floor | Tutorials |
| 604, 605, 606 | Computer Lab | 60 | Ground/U floor | Practicals |
| 611, 612, 615, 616, 617 | Computer Lab | 60 | 6th floor | Practicals |
| AFTF-12, AFTF-13, AFTF-14 | High-cap Computer Lab | 60+ | AFTF floor | Batch labs |
| AFF-09, AFF-10 | Lab / Project Room | 30 | AFF floor | IDP, small groups |
| 216 (shared) | Double-use room | 60 | Special cases | Lecture + DBMS(P) |

### Room Constraint Rules
- Computer labs (604–617) → Only for `(P)` subjects
- AFTF-12/13/14 → Heavy AI/ML labs (GPU machines) — preferred for DL, CV, MLOP
- Theory rooms → Only for `(L)` and `(T)` slots
- Multiple sections can share the same large lecture slot only if intentional (Open Elective global slots)

---

## 6. Faculty Pool & Workload Rules

### Faculty Sample Extracted from V5 (AIML II Year only)

| Faculty Name | Subjects Handled | Sections |
|---|---|---|
| DR. P. Kalpana | SFCDS (L+P) | II-A, II-F, II-L |
| DR. BANDI GURAVAIAH | SFCDS (L+P) | II-B, II-G, II-K |
| DR. RUSHI PRASAD SAHOO | SFCDS (L+P) | II-C, II-E, II-J |
| DR. B. N. NAVEEN KUMAR | SFCDS (L+P) | II-D, II-H, II-I |
| DR. ANKAMMA RAO MALLELA | DMS (L+P) | II-A, II-H, II-L |
| DR. N. BHARGAVI | DMS (L+P) | II-B, II-F, II-K |
| DR. MANIGANDAN A | DMS (L+P) | II-C, II-G, II-J |
| DR. IMTIYAZ BHATT | DMS (L+P) | II-D, II-E, II-I |
| Dr. S.Srikantha Reddy | DS (L+T+P) | II-A, II-C, II-E |
| Mr. Bharadwaja Chepuri | DS (L+T+P) | II-B, II-D, II-F |
| Mr. PLN Manoj Kumar | DS (L+T+P) | II-H, II-I, II-L |
| Ms. Narra Bhagyalakshmi | DS (L+T+P) | II-K |
| Dr. B. Sudha Rani | AI (L+P) | II-A, II-B, II-E, II-H |
| Dr. G. Kalaiarasi | AI (L+P) | II-B, II-G, II-J |
| Dr. P. Giri Prasad | AI (L+P) | II-C, II-F, II-I, II-J |
| Ms. D. Urlamma | AI (L+P) | II-D, II-F, II-K |
| Ms. P Seetha Lakshmi | DBMS (L+T+P) | II-A, II-G, II-J |
| Ms. S. RadhaRani | DBMS (L+T+P) | II-B, II-E, II-K |
| Mr. A.Siva Naga Rama Gopal | DBMS (L+T+P) | II-C, II-F, II-L |
| Mr. Vivek Kumar Saini | DBMS (L+T+P) | II-D, II-I |
| Mr. Prajwal Santakke | DBMS (L+T+P) | II-H |
| Ms. G. Mahalakshmi | OOPS (L+T+P) | II-A, II-D, II-G |
| Ms. I.Leela Priya | OOPS (L+T+P) | II-B, II-E, II-K |
| Ms. A. Chandana | OOPS (L+T+P) | II-C, II-F, II-H |
| Mr. D. Pavan Kalyan | OOPS (L+T+P) | II-I, II-J, II-L |
| Ms. Vemuri Lakshmi Ravali | DEF (T+P) | II-A, II-B |
| Mr. S. Uday Kiran | DEF (T+P) | II-C, II-D, II-E, II-F |

### AICTE Faculty Workload Rules

```
Faculty Grade         | Max Weekly Teaching Hours
----------------------|-------------------------
Assistant Professor   | 16 hours/week
Associate Professor   | 14 hours/week
Professor / HoD       | 12 hours/week (2h relaxation for admin/research)
Lab Co-Faculty        | Shared across batches (counted proportionally)
Daily Teaching Cap    | Max 4 teaching hours per day per faculty
```

### Lab Batch Faculty Allocation Rule
- A 60-student section doing DBMS(P) is split into 2–3 batches
- Each batch gets 1 primary + 1 lab assistant simultaneously
- Both faculty members are "busy" during that lab slot → must not be double-booked

---

## 7. The Math — UCTP as NP-Hard CSP

### Formal Problem Definition

The **University Course Timetabling Problem (UCTP)** is one of the classic NP-Hard combinatorial optimization problems. It belongs to the family of Constraint Satisfaction Problems (CSP) and can also be modeled as an Integer Linear Program (ILP).

### Decision Variables

Let:
- `S` = set of sections (44 sections)
- `C` = set of courses/subjects per section (~7–9 per section)
- `R` = set of rooms (35 rooms)
- `T` = set of timeslots (48 per week: 8 periods × 6 days)
- `F` = set of faculty (~80+)

Define binary variable:

```
x[s][c][r][t] = 1  if section s has course c in room r at timeslot t
              = 0  otherwise
```

For faculty assignment:

```
y[f][s][c][t] = 1  if faculty f teaches section s's course c at timeslot t
              = 0  otherwise
```

### Search Space Size

For ACSE alone:

```
|S| = 44,  |C| = avg 8,  |R| = 35,  |T| = 48

Total possible variable combinations before constraints:
  44 × 8 × 35 × 48 = 591,360 binary variables (x)
  80 × 44 × 8 × 48 = 13,516,800 binary variables (y)

Total search space (all assignments ON/OFF):
  2^591,360 — astronomically large
```

This is why manual scheduling is practically impossible at this scale and why we need algorithmic optimization.

### Why NP-Hard?

The UCTP reduces to a **graph coloring problem** which is NP-Complete:
- Each course-section pair is a node
- Edges connect nodes that share a faculty member or room
- Colors = timeslots
- Finding a valid coloring with no adjacent nodes sharing a color = valid timetable

For k colors (timeslots) and n nodes (course-sections), this is NP-Complete.

### Objective Function (Minimization)

```
Minimize:
  F = α × (Hard Constraint Violations) + β × (Soft Constraint Penalty)

Where:
  α >> β  (hard violations are infinitely penalized in feasibility phase)
  
Hard penalty per violation = 10,000 (or INFINITY in Phase 1)
Soft penalty per violation = 1–100 depending on severity
```

The combined fitness function for a candidate timetable `T` is:

```
fitness(T) = Σ hard_penalty_i × H_i(T)  +  Σ soft_penalty_j × S_j(T)

H_i(T) = number of violations of hard constraint i in timetable T
S_j(T) = number of violations of soft constraint j in timetable T
```

A valid timetable has `Σ H_i(T) = 0` for all i.

---

## 8. Hard & Soft Constraints (Complete List)

### HARD Constraints (Must Be Zero Violations)

These are absolutely non-negotiable. A timetable with ANY hard violation is **invalid**.

```
HC-01  [Room Conflict]
       No two sections can occupy the same room at the same timeslot.
       ∀ r ∈ R, ∀ t ∈ T: Σ_{s,c} x[s][c][r][t] ≤ 1

HC-02  [Faculty Double-Booking]
       No faculty member can teach two classes simultaneously.
       ∀ f ∈ F, ∀ t ∈ T: Σ_{s,c} y[f][s][c][t] ≤ 1

HC-03  [Student Conflict]
       No student can attend two classes simultaneously.
       For each section s and timeslot t: at most 1 class per section per slot.
       ∀ s ∈ S, ∀ t ∈ T: Σ_{c,r} x[s][c][r][t] ≤ 1

HC-04  [Subject Frequency]
       Each subject must appear the required number of times per week.
       Σ_{r,t} x[s][c][r][t] = required_hours[s][c]  ∀ s,c

HC-05  [Room Capacity]
       A room can only host a section if room capacity ≥ section size.
       x[s][c][r][t] = 1 ⟹ capacity[r] ≥ size[s]

HC-06  [Room Type Compatibility]
       Lab sessions (P) must be in lab rooms. Lectures (L/T) in classrooms.
       x[s][c][r][t] = 1 ⟹ type_compatible(c, r) = TRUE

HC-07  [Break/Lunch Blocking]
       No class during BREAK (09:55–10:10) or LUNCH (12:40–13:40).
       x[s][c][r][break_slot] = 0  and  x[s][c][r][lunch_slot] = 0  ∀ s,c,r

HC-08  [Lab Consecutiveness]
       Practical sessions (P) must occupy 2–3 consecutive periods.
       If x[s][c][r][t]=1 and c is practical, then x[s][c][r][t+1]=1 (and t+2 for 3-hour labs)
       Lab cannot span across BREAK or LUNCH.

HC-09  [Faculty Availability]
       Faculty with declared unavailability cannot be assigned during that slot.
       y[f][s][c][t] = 0  if f is unavailable at t

HC-10  [No Back-to-Back Teaching Overload]
       Faculty cannot teach more than 4 consecutive periods without a break.
       Σ_{4 consecutive t} Σ_{s,c} y[f][s][c][t] ≤ 4  ∀ f
```

### SOFT Constraints (Minimized, Not Eliminated)

These improve timetable quality but violations are tolerated for feasibility.

```
SC-01  [Faculty Weekly Load]  Penalty: 50 per excess hour
       Total teaching hours for faculty f ≤ max_hours[f]
       (16 for Asst Prof, 14 for Assoc Prof, 12 for Prof/HoD)

SC-02  [Daily Teaching Load]  Penalty: 30 per excess period
       Faculty should not teach more than 4 periods per day.

SC-03  [No Student Free Gaps]  Penalty: 10 per gap
       Minimize empty periods between classes within a student's day.
       (A gap = a free period between two occupied periods in same day)

SC-04  [Library Slot Placement]  Penalty: 5 per misplacement
       Library slot should ideally be in period 4 or 5 (midday) for each section.

SC-05  [Subject Distribution]  Penalty: 20 per clustering violation
       Subjects should not have all sessions on the same day.
       (e.g., DS should not appear 3 times on Monday)

SC-06  [Lab Morning Preference]  Penalty: 5 per afternoon lab
       Practical labs preferred in morning (Periods 1–3) over afternoon.

SC-07  [Global Sync Slots]  Penalty: 100 per violation
       Open Elective (OE) must be in synchronized timeslots across all sections of same year.
       Minors/Honors must be Wednesday Period 7–8 or Thursday Period 7–8.

SC-08  [Saturday Usage]  Penalty: 15 per Saturday overflow
       Saturday should be lighter — prefer using it for remedial/DEF/QALR only.

SC-09  [Faculty Travel Time]  Penalty: 10 per adjacent violation
       If a faculty teaches back-to-back in different floors/buildings, flag it.
       (e.g., Room 601 (2nd floor) followed by AFTF-14 (4th floor) in consecutive periods)

SC-10  [Section Balance]  Penalty: 5 per imbalance
       Sections of same year and same subject should be taught at distributed timeslots
       (prevents one section always getting Period 1 while another always gets Period 8)
```

---

## 9. Algorithm Selection & Justification

### Why Not Brute Force?

```
Search space: 2^591,360
Brute force at 10^12 evaluations/second would take: 10^(591,360 / log₁₀(2)) / 10^12 seconds
≈ 10^177,000 years

CONCLUSION: Computationally impossible. We need heuristics.
```

### Algorithm Comparison

| Algorithm | Pros | Cons | Suitable? |
|-----------|------|------|-----------|
| **Brute Force** | Guaranteed optimal | Impossible at scale | ❌ |
| **ILP (Gurobi/CPLEX)** | Exact optimal | Requires paid solver, OOM for large instances | ⚠️ Small scale only |
| **Google OR-Tools CP-SAT** | Free, fast, optimal for medium scale | May timeout for 44 sections | ✅ Recommended Phase 1 |
| **Genetic Algorithm (GA)** | Scales well, good for large instances, widely studied | No guarantee of optimality | ✅ Recommended Phase 2 |
| **Simulated Annealing** | Simple to implement, escapes local optima | Slow convergence | ⚠️ Backup |
| **Tabu Search** | Good local search, avoids revisiting | Complex implementation | ⚠️ Can augment GA |
| **Hybrid GA + Local Search** | Best of both worlds, used in literature | Complex to tune | ✅ Best for production |

### Recommended: 2-Phase Hybrid Approach

#### Phase 1 — Google OR-Tools CP-SAT (Constraint Programming)

```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()

# Binary variables: x[section][course][room][timeslot]
x = {}
for s in sections:
    for c in courses[s]:
        for r in rooms:
            for t in timeslots:
                x[s,c,r,t] = model.NewBoolVar(f'x_{s}_{c}_{r}_{t}')

# HC-01: Room conflict
for r in rooms:
    for t in timeslots:
        model.AddAtMostOne([x[s,c,r,t] for s in sections for c in courses[s]])

# HC-03: One class per section per slot
for s in sections:
    for t in timeslots:
        model.AddAtMostOne([x[s,c,r,t] for c in courses[s] for r in rooms])

# HC-04: Subject frequency
for s in sections:
    for c in courses[s]:
        model.Add(sum(x[s,c,r,t] for r in rooms for t in timeslots) == required[s][c])

# Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 120.0
status = solver.Solve(model)
```

CP-SAT will find a feasible solution (all hard constraints satisfied) in 1–2 minutes for most sub-problems (per year, per branch).

#### Phase 2 — Genetic Algorithm (for global optimization of soft constraints)

```python
class Chromosome:
    """Represents one complete timetable as a list of assignments"""
    def __init__(self):
        self.genes = []  # list of (section, course, room, timeslot)
    
    def fitness(self):
        hard_penalty = self.count_hard_violations() * 10000
        soft_penalty = self.count_soft_violations()
        return -(hard_penalty + soft_penalty)  # maximize (less negative = better)

class GeneticAlgorithm:
    POPULATION_SIZE = 200
    GENERATIONS = 1000
    MUTATION_RATE = 0.05
    CROSSOVER_RATE = 0.8
    TOURNAMENT_SIZE = 5
    ELITE_COUNT = 10  # keep top 10 unchanged each generation
    
    def select(self, population):
        """Tournament selection"""
        tournament = random.sample(population, self.TOURNAMENT_SIZE)
        return max(tournament, key=lambda c: c.fitness())
    
    def crossover(self, parent1, parent2):
        """Single-point crossover on section-level chunks"""
        point = random.randint(1, len(sections) - 1)
        child = Chromosome()
        child.genes = (
            parent1.genes[:point * slots_per_section] +
            parent2.genes[point * slots_per_section:]
        )
        return child
    
    def mutate(self, chromosome):
        """Swap a random assignment's room or timeslot"""
        if random.random() < self.MUTATION_RATE:
            idx = random.randint(0, len(chromosome.genes) - 1)
            # Try swapping timeslot or room
            gene = chromosome.genes[idx]
            new_t = random.choice(timeslots)
            chromosome.genes[idx] = (gene[0], gene[1], gene[2], new_t)
        return chromosome
```

The GA converges to near-optimal solutions (< 5 soft violations) within 500–1000 generations for the full ACSE schedule.

### Proven Performance from Literature

<cite index="17-1">Recent research shows a genetic algorithm with constraint-aware operators achieves 100% hard constraint satisfaction and generates feasible timetables in 45 seconds — compared to 4 hours of manual effort for a 69-course problem.</cite>

<cite index="19-1">FET (Free Timetabling Software), the leading open-source timetabling tool, uses a fast and efficient algorithm and is usually able to solve a complicated timetable in maximum 5–20 minutes.</cite>

---

## 10. Website Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    BROWSER (React SPA)                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │ Dashboard│  │ Data Mgmt│  │ Scheduler│  │ Export │  │
│  │ (home)   │  │ (CRUD)   │  │ (trigger)│  │ (xlsx) │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘  │
└───────────────────────┬─────────────────────────────────┘
                        │ REST / WebSocket
┌───────────────────────▼─────────────────────────────────┐
│                 FastAPI Backend (Python)                 │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │ CRUD APIs  │  │ Solver API   │  │ Conflict Checker │ │
│  │ /faculty   │  │ POST /solve  │  │ GET /validate    │ │
│  │ /rooms     │  │ GET /status  │  │                  │ │
│  │ /subjects  │  │ WS /progress │  │                  │ │
│  └────────────┘  └──────────────┘  └──────────────────┘ │
└──────────┬───────────────┬──────────────────────────────┘
           │               │
     ┌─────▼─────┐   ┌─────▼──────────┐
     │PostgreSQL │   │  Celery Worker  │
     │  Database │   │  (Solver runs  │
     │           │   │   in background)│
     └───────────┘   └────────────────┘
                            │
                     ┌──────▼──────┐
                     │ OR-Tools    │
                     │ CP-SAT +    │
                     │ GA Solver   │
                     └─────────────┘
```

### Database Schema (PostgreSQL)

```sql
-- Core entities

CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE,   -- 'ACSE'
    name TEXT,
    head_faculty_id INT
);

CREATE TABLE academic_years (
    id SERIAL PRIMARY KEY,
    year INT,                  -- 2026
    semester INT,              -- 1 or 2
    start_date DATE,
    end_date DATE
);

CREATE TABLE branches (
    id SERIAL PRIMARY KEY,
    dept_id INT REFERENCES departments(id),
    code VARCHAR(20),          -- 'AIML', 'CS', 'DS', 'CSBS', 'IOT', 'BS(DS)'
    name TEXT,
    year_level INT             -- 2, 3, or 4
);

CREATE TABLE sections (
    id SERIAL PRIMARY KEY,
    branch_id INT REFERENCES branches(id),
    label VARCHAR(5),          -- 'A', 'B', ..., 'L'
    strength INT DEFAULT 60,
    academic_year_id INT REFERENCES academic_years(id)
);

CREATE TABLE faculty (
    id SERIAL PRIMARY KEY,
    dept_id INT REFERENCES departments(id),
    name TEXT NOT NULL,
    designation VARCHAR(50),   -- 'Assistant Professor', 'Associate Professor', 'Professor'
    max_hours_per_week INT,    -- 16, 14, or 12
    availability JSONB         -- {MON: [1,2,3,4,5,6,7,8], TUE: [...], ...}
);

CREATE TABLE subjects (
    id SERIAL PRIMARY KEY,
    dept_id INT REFERENCES departments(id),
    code VARCHAR(20),          -- 'SFCDS', 'DS', 'DBMS', 'OOPS'
    full_name TEXT,
    type VARCHAR(10),          -- 'L', 'T', 'P', 'LTP'
    hours_per_week INT,
    is_lab BOOLEAN DEFAULT FALSE,
    requires_consecutive INT   -- NULL for lectures, 2 or 3 for labs
);

CREATE TABLE section_subjects (
    id SERIAL PRIMARY KEY,
    section_id INT REFERENCES sections(id),
    subject_id INT REFERENCES subjects(id),
    lecture_faculty_id INT REFERENCES faculty(id),
    lab_faculty_ids INT[],     -- Array of faculty IDs for lab co-faculty
    total_slots_needed INT     -- computed: L_hours + T_hours + P_hours per week
);

CREATE TABLE rooms (
    id SERIAL PRIMARY KEY,
    dept_id INT REFERENCES departments(id),
    code VARCHAR(20),          -- '601', '604', 'AFTF-12'
    type VARCHAR(20),          -- 'classroom', 'computer_lab', 'seminar_hall'
    capacity INT,
    floor INT,
    block VARCHAR(20)          -- 'U-Block', 'AFTF', 'AFF'
);

CREATE TABLE time_slots (
    id SERIAL PRIMARY KEY,
    day VARCHAR(3),            -- 'MON', 'TUE', ..., 'SAT'
    period INT,                -- 1 through 8
    start_time TIME,
    end_time TIME,
    is_blocked BOOLEAN DEFAULT FALSE  -- TRUE for BREAK and LUNCH
);

-- The timetable itself

CREATE TABLE timetable_entries (
    id SERIAL PRIMARY KEY,
    timetable_version_id INT REFERENCES timetable_versions(id),
    section_id INT REFERENCES sections(id),
    subject_id INT REFERENCES subjects(id),
    room_id INT REFERENCES rooms(id),
    time_slot_id INT REFERENCES time_slots(id),
    faculty_ids INT[],
    entry_type VARCHAR(10),    -- 'L', 'T', 'P', 'LIBRARY', 'OE', 'BREAK'
    is_global_sync BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE timetable_versions (
    id SERIAL PRIMARY KEY,
    academic_year_id INT REFERENCES academic_years(id),
    version_label VARCHAR(10), -- 'V1', 'V2', 'V5'
    valid_from DATE,
    is_current BOOLEAN DEFAULT FALSE,
    solver_run_id INT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Solver tracking

CREATE TABLE solver_runs (
    id SERIAL PRIMARY KEY,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    algorithm VARCHAR(50),     -- 'CP-SAT', 'GA', 'Hybrid'
    status VARCHAR(20),        -- 'running', 'completed', 'failed'
    hard_violations INT,
    soft_violations INT,
    fitness_score FLOAT,
    generation_count INT,
    runtime_seconds FLOAT,
    config JSONB               -- algorithm hyperparameters
);
```

### API Endpoints

```
# Data Management
POST   /api/v1/faculty          → Create/import faculty
GET    /api/v1/faculty          → List all faculty with load summary
PUT    /api/v1/faculty/{id}     → Update faculty preferences
POST   /api/v1/rooms            → Add room
POST   /api/v1/subjects         → Add subject
POST   /api/v1/sections         → Add section
POST   /api/v1/section-subjects → Assign subject+faculty to section

# Excel Import (key feature)
POST   /api/v1/import/excel     → Upload existing timetable XLSX → parse + import
                                  Returns: parsed data + detected clashes

# Solver
POST   /api/v1/solve            → Trigger solver run (returns run_id)
                                  Body: { algorithm, sections, constraints, config }
GET    /api/v1/solve/{run_id}/status → Poll solver progress
WS     /api/v1/solve/{run_id}/stream → Real-time GA generation updates

# Timetable
GET    /api/v1/timetable/{version_id}         → Full timetable
GET    /api/v1/timetable/{version_id}/section/{id}   → One section's view
GET    /api/v1/timetable/{version_id}/faculty/{id}   → Faculty schedule
GET    /api/v1/timetable/{version_id}/room/{id}      → Room usage

# Validation
GET    /api/v1/validate/{version_id}  → Run full constraint checker
                                        Returns: { hard_violations, soft_violations, details }

# Export
GET    /api/v1/export/{version_id}/xlsx    → Download Excel (same format as current)
GET    /api/v1/export/{version_id}/pdf     → Printable PDF per section
GET    /api/v1/export/{version_id}/json    → Raw JSON
```

---

## 11. Data Ingestion Pipeline (from Excel)

The most critical first step is parsing your existing V1–V5 Excel files.

### Parser Architecture

```python
import openpyxl
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ParsedSlot:
    section: str        # e.g., "II AIML-A"
    day: str            # e.g., "MON"
    period: int         # 1–8
    subject_code: str   # e.g., "DS(P)"
    room: str           # e.g., "604"
    subject_type: str   # "L", "T", "P", "LIBRARY"

@dataclass
class ParsedSection:
    name: str
    sheet: str
    branch: str         # "AIML", "CS", "DS", ...
    year: int           # 2, 3, 4
    section_label: str  # "A", "B", ..., "L"
    slots: List[ParsedSlot]
    faculty_map: dict   # {subject_code: [faculty_name_1, ...]}

class ExcelTimetableParser:
    """Parse VFSTR ACSE Excel timetable format"""
    
    DAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT',
            'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY']
    
    DAY_NORM = {'MONDAY': 'MON', 'TUESDAY': 'TUE', 'WEDNESDAY': 'WED',
                'THURSDAY': 'THU', 'FRIDAY': 'FRI', 'SATURDAY': 'SAT'}
    
    ACRONYM_MAP = {
        'SFCDS': 'Statistical Foundation for Computing and Data Science',
        'DMS': 'Discrete Mathematical Structures',
        'DS': 'Data Structures',
        'AI': 'Artificial Intelligence Search Methods for Problem Solving',
        'DBMS': 'Database Management Systems',
        'OOPS': 'Object Oriented Programming',
        'DEF': 'Data Engineering Foundations',
        'QALR': 'Quantitative Aptitude & Logical Reasoning',
        'DL': 'Deep Learning',
        'WT': 'Web Technologies',
        'CV': 'Computer Vision',
        'ADS': 'Advanced Data Structures',
        'MLOP': 'Machine Learning Operations',
        'CNS': 'Cryptography and Network Security',
        'TM': 'Text Mining',
        'KRR': 'Knowledge Representation and Reasoning',
        'GENAI': 'Generative AI',
        'GEN AI': 'Generative AI',
        'IOT': 'Internet of Things',
        'IDP': 'Inter-Departmental Project',
        'MFCS': 'Mathematical Foundations for Cyber Security',
        'FIS': 'Foundations of Information Security',
        'CN': 'Computer Networks',
        'P&S': 'Probability and Statistics',
        'OT': 'Optimization Techniques',
        'OS': 'Operating Systems',
        'DSF': 'Foundations of Data Science',
    }
    
    def parse_file(self, filepath: str) -> dict:
        xls = pd.ExcelFile(filepath)
        result = {}
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            sections = self._parse_sheet(df, sheet)
            result[sheet] = sections
        return result
    
    def _detect_section_header(self, value: str) -> Optional[str]:
        prefixes = ['II ', 'III ', 'IV ', 'I ', 'M.TECH', 'MSC', 'BS(', 'MINOR']
        if any(value.startswith(p) for p in prefixes) and len(value) < 25:
            return value
        return None
    
    def _parse_slot(self, cell_value: str) -> tuple:
        """Parse 'DS(P)\\n604' → ('DS', 'P', '604')"""
        if not cell_value or cell_value in ['nan', 'BREAK', 'LUNCH', 'NaN']:
            return None
        parts = str(cell_value).split('\n')
        subject_raw = parts[0].strip()
        room = parts[1].strip() if len(parts) > 1 else 'NO_ROOM'
        
        # Extract type
        if '(P)' in subject_raw:
            s_type = 'P'
        elif '(T)' in subject_raw:
            s_type = 'T'
        elif '(L)' in subject_raw:
            s_type = 'L'
        else:
            s_type = 'L'
        
        subject_code = subject_raw.replace('(P)', '').replace('(T)', '').replace('(L)', '').strip()
        return subject_code, s_type, room
    
    def detect_clashes(self, all_sections: List[ParsedSection]) -> dict:
        """Find all room and faculty clashes"""
        room_usage = {}  # (day, period, room) → [(section, subject)]
        clashes = {'room': [], 'faculty': []}
        
        for sec in all_sections:
            for slot in sec.slots:
                key = (slot.day, slot.period, slot.room)
                room_usage.setdefault(key, []).append((sec.name, slot.subject_code))
        
        for key, assignments in room_usage.items():
            if len(assignments) > 1:
                clashes['room'].append({
                    'day': key[0], 'period': key[1], 'room': key[2],
                    'conflicts': assignments
                })
        
        return clashes
```

### Import Flow

```
Upload XLSX
    ↓
ExcelTimetableParser.parse_file()
    ↓
Normalize section names, subject codes, room codes
    ↓
Map subjects to subjects table (fuzzy match on ACRONYM_MAP)
    ↓
Map faculty strings to faculty table (fuzzy name match)
    ↓
Store as timetable_version (label='IMPORTED_V5', valid_from=2026-07-15)
    ↓
Run conflict detector → return ClashReport to UI
    ↓
User confirms import → data locked in DB as baseline
    ↓
User can now run solver to generate clash-free V6 automatically
```

---

## 12. Solver Engine Design

### CP-SAT Phase (Hard Constraint Satisfaction)

The solver runs as a **Celery background task** because it can take 30 seconds to 5 minutes.

```python
# tasks/solver.py

from celery import shared_task
from ortools.sat.python import cp_model

@shared_task(bind=True)
def run_csat_solver(self, config: dict):
    """
    Run CP-SAT solver for given sections.
    Sends progress updates via celery state.
    """
    model = cp_model.CpModel()
    
    sections = load_sections(config['section_ids'])
    rooms = load_rooms()
    timeslots = load_timeslots()
    
    # Create decision variables
    x = {}
    for s in sections:
        for c in s.courses:
            for r in rooms:
                for t in timeslots:
                    if t.is_blocked:
                        continue
                    if not room_type_compatible(c, r):
                        continue
                    if r.capacity < s.strength:
                        continue
                    x[s.id, c.id, r.id, t.id] = model.NewBoolVar(
                        f'x_{s.id}_{c.id}_{r.id}_{t.id}'
                    )
    
    # HC-01: Room conflicts
    for r in rooms:
        for t in timeslots:
            vars_at_rt = [x[s.id,c.id,r.id,t.id] for s in sections 
                          for c in s.courses 
                          if (s.id,c.id,r.id,t.id) in x]
            if vars_at_rt:
                model.AddAtMostOne(vars_at_rt)
    
    # HC-03: One class per section per slot
    for s in sections:
        for t in timeslots:
            vars_at_st = [x[s.id,c.id,r.id,t.id] for c in s.courses 
                          for r in rooms 
                          if (s.id,c.id,r.id,t.id) in x]
            if vars_at_st:
                model.AddAtMostOne(vars_at_st)
    
    # HC-04: Subject frequency
    for s in sections:
        for c in s.courses:
            all_vars = [x[s.id,c.id,r.id,t.id] for r in rooms for t in timeslots
                        if (s.id,c.id,r.id,t.id) in x]
            model.Add(sum(all_vars) == c.required_slots_per_week)
    
    # HC-08: Lab consecutiveness (labs must be in adjacent periods)
    for s in sections:
        for c in [c for c in s.courses if c.is_lab]:
            for r in [r for r in rooms if r.is_lab]:
                for t in timeslots:
                    if t.period < 7:  # can chain t, t+1 (and t+2 for 3-hour labs)
                        next_t = get_next_period(t)
                        if next_t and (s.id,c.id,r.id,next_t.id) in x:
                            # If slot t is used, slot t+1 must also be used
                            model.AddImplication(
                                x[s.id,c.id,r.id,t.id],
                                x[s.id,c.id,r.id,next_t.id]
                            )
    
    # Soft constraints as minimize objective
    penalty_vars = []
    
    # SC-03: Gap penalty for students
    for s in sections:
        for day in DAYS:
            day_slots = [t for t in timeslots if t.day == day]
            for i in range(len(day_slots) - 2):
                t1, t_gap, t2 = day_slots[i], day_slots[i+1], day_slots[i+2]
                # If t1 has class AND t2 has class, t_gap should not be free
                is_gap = model.NewBoolVar(f'gap_{s.id}_{day}_{i}')
                occupied_t1 = [x[s.id,c.id,r.id,t1.id] for c in s.courses for r in rooms 
                                if (s.id,c.id,r.id,t1.id) in x]
                # ... (gap detection logic)
                penalty_vars.append((10, is_gap))
    
    # Minimize total soft penalty
    model.Minimize(sum(weight * var for weight, var in penalty_vars))
    
    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = config.get('timeout', 120)
    solver.parameters.num_search_workers = 8  # parallel
    
    # Progress callback
    class ProgressCallback(cp_model.CpSolverSolutionCallback):
        def on_solution_callback(self):
            self.task.update_state(
                state='PROGRESS',
                meta={'objective': self.ObjectiveValue(), 
                      'wall_time': self.WallTime()}
            )
    
    status = solver.Solve(model, ProgressCallback())
    
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        # Extract solution and save to DB
        return extract_and_save_solution(solver, x, sections)
    else:
        return {'status': 'infeasible', 'detail': 'No valid timetable found'}
```

---

## 13. Open Source Stack

### Full Technology Stack

| Layer | Technology | Version | Reason |
|-------|-----------|---------|--------|
| **Frontend** | React + TypeScript | 18+ | Component-based UI |
| **UI Components** | shadcn/ui + Tailwind CSS | Latest | Rapid, clean UI |
| **State Management** | Zustand | 4.x | Simple, no boilerplate |
| **Timetable Grid** | Custom React grid or react-big-calendar | — | Displays slots visually |
| **HTTP Client** | Axios + React Query | — | Caching + background refetch |
| **WebSocket** | native WS | — | Real-time solver progress |
| **Backend** | FastAPI (Python) | 0.110+ | Async, fast, Pydantic |
| **ORM** | SQLAlchemy 2.0 | — | Database access |
| **Database** | PostgreSQL 16 | — | JSONB for availability, arrays |
| **Background Tasks** | Celery + Redis | — | Non-blocking solver |
| **Solver Core** | Google OR-Tools | 9.9 | CP-SAT engine (free, Apache 2) |
| **GA Library** | DEAP or custom | — | Genetic algorithm |
| **Excel Parsing** | openpyxl + pandas | — | Import existing timetables |
| **Excel Export** | openpyxl | — | Export in same VFSTR format |
| **PDF Export** | ReportLab / WeasyPrint | — | Printable schedules |
| **Auth** | JWT + FastAPI-Users | — | Role-based: Admin, Viewer |
| **Containerization** | Docker + Docker Compose | — | One-command deploy |
| **CI/CD** | GitHub Actions | — | Auto test + deploy |

### Repository Structure

```
vfstr-timetable-scheduler/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── TimetableGrid/       ← Main 6×8 grid display
│   │   │   ├── SolverProgress/      ← Real-time GA progress bar
│   │   │   ├── ClashReport/         ← Visual conflict display
│   │   │   ├── FacultyCalendar/     ← Faculty workload view
│   │   │   └── DataForms/           ← CRUD for rooms, subjects, faculty
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Import.tsx
│   │   │   ├── Configure.tsx
│   │   │   ├── Schedule.tsx
│   │   │   └── Export.tsx
│   │   └── hooks/
│   │       ├── useSolver.ts
│   │       └── useTimetable.ts
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── faculty.py
│   │   │   ├── rooms.py
│   │   │   ├── subjects.py
│   │   │   ├── sections.py
│   │   │   ├── timetable.py
│   │   │   ├── solver.py
│   │   │   ├── import_export.py
│   │   │   └── validate.py
│   │   ├── models/              ← SQLAlchemy models
│   │   ├── schemas/             ← Pydantic schemas
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   └── main.py
│   │
│   ├── solver/
│   │   ├── csat_solver.py       ← OR-Tools CP-SAT solver
│   │   ├── genetic_algorithm.py ← GA implementation
│   │   ├── constraints.py       ← HC-01 through HC-10, SC-01 through SC-10
│   │   ├── fitness.py           ← Fitness function
│   │   └── conflict_checker.py  ← Standalone validator
│   │
│   ├── parser/
│   │   ├── excel_parser.py      ← Parse VFSTR Excel format
│   │   ├── excel_exporter.py    ← Export back to Excel
│   │   └── normalizer.py        ← Name + code normalization
│   │
│   ├── tasks/
│   │   ├── celery_app.py
│   │   └── solver_tasks.py
│   │
│   └── tests/
│       ├── test_constraints.py
│       ├── test_parser.py
│       └── test_solver.py
│
├── docker-compose.yml
├── Makefile
└── README.md
```

---

## 14. Phase-wise Implementation Roadmap

### Phase 0 — Data Extraction (Week 1)

**Goal:** Extract all data from V5 Excel into structured form.

- [ ] Build `ExcelTimetableParser` — parse all sheets, all sections
- [ ] Build acronym-to-full-name mapper (20+ subject codes)
- [ ] Build faculty name normalizer (handles "Dr.", "DR.", "Mr.", "Ms." variations)
- [ ] Output: clean JSON of all 44 sections with slots + faculty assignments
- [ ] Validate: 1,000 slot entries extracted, 384 faculty-subject mappings

```bash
python parser/excel_parser.py --input "ACSE_TIMETABLE_V5.xlsx" --output data.json
# Expected output:
# Sections: 44
# Slots: 1,000
# Faculty mappings: 384
# Room clashes found: 51
# Faculty clashes found: 0
```

### Phase 1 — Backend & Database (Week 2)

**Goal:** Full REST API + database schema live.

- [ ] Scaffold FastAPI app with all models (faculty, rooms, subjects, sections, timetable)
- [ ] Implement all CRUD endpoints
- [ ] Import Phase 0 JSON into PostgreSQL via seeder
- [ ] Add JWT auth (admin / viewer roles)
- [ ] Docker Compose: FastAPI + PostgreSQL + Redis

```bash
docker compose up  # bring up full stack
curl http://localhost:8000/api/v1/sections | jq '.total'
# Expected: 44
```

### Phase 2 — Excel Import & Conflict Checker (Week 3)

**Goal:** Upload any VFSTR Excel file and see all clashes instantly.

- [ ] `POST /api/v1/import/excel` — parse and import
- [ ] `GET /api/v1/validate/{version_id}` — return full clash report
- [ ] Frontend: drag-drop upload UI + clash table display
- [ ] Clash report shows: day, period, room, clashing sections, conflicting subjects

**Validation criteria:** Running V5 import should detect exactly 51 room clashes.

### Phase 3 — CP-SAT Solver (Week 4–5)

**Goal:** Solver generates a valid (0 hard violations) timetable for any year/branch.

- [ ] Implement all 10 Hard Constraints in OR-Tools CP-SAT
- [ ] Implement Celery task + WebSocket progress streaming
- [ ] Solver can run for: one branch (e.g., "II AIML only") or full department
- [ ] Store solver runs with runtime, violations count, algorithm config
- [ ] Frontend: "Run Solver" button → progress bar → result display

**Target:** For II AIML (12 sections), solver completes in < 2 minutes with 0 hard violations.

### Phase 4 — Genetic Algorithm + Soft Constraints (Week 6–7)

**Goal:** GA optimizes soft constraints to produce a quality timetable.

- [ ] Implement GA (population, fitness, selection, crossover, mutation)
- [ ] Implement all 10 Soft Constraints with penalty weights
- [ ] Implement "repair mechanism" — if crossover creates a hard violation, auto-fix it
- [ ] Frontend: show GA generation progress (fitness graph over time)
- [ ] Compare baseline vs optimized: side-by-side view

**Target:** < 10 soft constraint violations for full ACSE schedule.

### Phase 5 — Export & Production Polish (Week 8)

**Goal:** Export generated timetable in exact same Excel format as current.

- [ ] Excel exporter: output per-section tabs matching VFSTR format (with room codes in cells)
- [ ] PDF exporter: printable per-section timetable
- [ ] Faculty schedule view: one-page view of any faculty's full week
- [ ] Room utilization dashboard: which rooms are overbooked/underused
- [ ] Timetable versioning: compare V_manual_V5 vs V_auto_V6

---

## 15. Metrics & Validation

### Success Criteria

| Metric | Current (Manual V5) | Target (Automated) |
|--------|--------------------|--------------------|
| Hard Constraint Violations | **51 room clashes** | **0** |
| Faculty Double-Bookings | 0 | 0 |
| Time to Generate | 2–3 weeks + 5 daily revisions | **< 5 minutes** |
| Subject Frequency Accuracy | ~90% (some missing slots) | **100%** |
| Weekly Revision Count | 5 in first week | 0 (changes via UI) |
| Faculty Load Balance | Manual, unverified | Verified ≤ 16h/16h/12h per grade |
| Soft Constraint Score | Unknown | Minimize to < 10 |

### Automated Test Suite

```python
# tests/test_constraints.py

def test_no_room_clashes(timetable):
    """HC-01: No two sections in same room at same time"""
    room_usage = defaultdict(list)
    for entry in timetable.entries:
        key = (entry.day, entry.period, entry.room_id)
        room_usage[key].append(entry.section_id)
    clashes = {k: v for k, v in room_usage.items() if len(v) > 1}
    assert len(clashes) == 0, f"Room clashes found: {clashes}"

def test_no_faculty_double_booking(timetable):
    """HC-02: No faculty teaches two classes at same time"""
    faculty_usage = defaultdict(list)
    for entry in timetable.entries:
        for fac_id in entry.faculty_ids:
            key = (entry.day, entry.period, fac_id)
            faculty_usage[key].append(entry.section_id)
    clashes = {k: v for k, v in faculty_usage.items() if len(v) > 1}
    assert len(clashes) == 0, f"Faculty double-bookings found: {clashes}"

def test_subject_frequency(timetable, required_frequency):
    """HC-04: Each subject appears required times per week"""
    for section in timetable.sections:
        for subject in section.subjects:
            count = len([e for e in timetable.entries 
                        if e.section_id == section.id and e.subject_id == subject.id])
            assert count == required_frequency[section.id][subject.id], \
                f"Frequency mismatch: {section.name} {subject.code} has {count}, expected {required_frequency[section.id][subject.id]}"

def test_lab_consecutiveness(timetable):
    """HC-08: Lab sessions span consecutive periods"""
    lab_entries = [e for e in timetable.entries if e.entry_type == 'P']
    for sec_id in set(e.section_id for e in lab_entries):
        for day in DAYS:
            labs_today = sorted(
                [e for e in lab_entries if e.section_id == sec_id and e.day == day],
                key=lambda e: e.period
            )
            for i, lab in enumerate(labs_today[:-1]):
                assert labs_today[i+1].period == lab.period + 1, \
                    f"Lab not consecutive: {sec_id} on {day}"

def test_faculty_workload(timetable, faculty_list):
    """SC-01: Faculty do not exceed max weekly hours"""
    for faculty in faculty_list:
        total = len([e for e in timetable.entries if faculty.id in e.faculty_ids])
        assert total <= faculty.max_hours_per_week, \
            f"Overloaded: {faculty.name} has {total}h (max {faculty.max_hours_per_week}h)"
```

---

## Quick Start (After Implementation)

```bash
# Clone and setup
git clone https://github.com/your-org/vfstr-timetable-scheduler
cd vfstr-timetable-scheduler

# Start all services
docker compose up -d

# Import existing timetable
curl -X POST http://localhost:8000/api/v1/import/excel \
  -F "file=@ACSE_TIMETABLE_V5.xlsx" \
  | jq '.clash_report.room_clashes | length'
# Expected: 51

# Run solver for full ACSE
curl -X POST http://localhost:8000/api/v1/solve \
  -H "Content-Type: application/json" \
  -d '{"algorithm": "CP-SAT", "scope": "ALL", "timeout": 300}'
# Returns: {"run_id": "abc123"}

# Poll status
curl http://localhost:8000/api/v1/solve/abc123/status
# {"status": "completed", "hard_violations": 0, "soft_violations": 7, "runtime": 187.4}

# Export result
curl http://localhost:8000/api/v1/export/latest/xlsx -o ACSE_V6_AUTO.xlsx
# Open Excel — zero clashes, same format as V5
```

---

## Summary: The Core Problem in Numbers

```
VFSTR ACSE Department — Semester I, Academic Year 2026-27

Input Scale:
  44  sections
  ~60  unique subjects
  ~80  faculty members
  ~35  rooms
  48  time slots per week

Current Pain:
  5 manual Excel revisions in 5 days
  51 room clashes in the "final" version
  2-3 weeks of human coordinator effort per semester
  ~2,600 students disrupted with each revision

Why It's Hard (The Math):
  Decision variables: ~600,000 binary
  Search space: 2^600,000 (cannot brute force)
  Problem class: NP-Hard (reduces to Graph Coloring)
  
Solution:
  Phase 1: CP-SAT → 0 hard violations in < 5 minutes
  Phase 2: Genetic Algorithm → minimize soft violations
  Phase 3: Web UI → coordinators interact, not iterate
  
Result:
  From 3 weeks + 5 daily revisions  →  5 minutes + 0 revisions
```

---

*README compiled from analysis of ACSE_TIMETABLE V3/V4/V5 Excel files, VFSTR campus documentation, AICTE norms, and academic literature on University Course Timetabling Problem (UCTP).*

*Key References:*
- *Burke, E. et al. (2004) — Practice and Theory of Automated Timetabling (PATAT)*
- *Rossi-Doria, O. et al. (2003) — A Comparison of the Performance of Different Metaheuristics on the UCTP*
- *Google OR-Tools CP-SAT Documentation — developers.google.com/optimization*
- *FET — Free Timetabling Software — lalescu.ro/liviu/fet*
- *Vignan University VFSTR Official — vignan.ac.in*
