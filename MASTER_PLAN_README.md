# VFSTR ACSE Timetable Scheduler — Master Plan & Full Pattern Analysis

> **Based on:** 46 real timetable screenshots + all 12 uploaded model files + 2 frontend components  
> **Department:** Advanced Computer Science & Engineering (ACSE), Vignan University, Guntur  
> **Academic Year:** 2026–27, Semester I  
> **Branches covered:** AIML, CS, DS, CSBS, IOT, BS(DS), MSC(DS), MTECH(DS)

---

## Table of Contents

1. [Complete Section Inventory](#1-complete-section-inventory)
2. [Deep Pattern Analysis from 46 Screenshots](#2-deep-pattern-analysis-from-46-screenshots)
3. [Subject Profiles by Year and Branch](#3-subject-profiles-by-year-and-branch)
4. [Room Inventory and Type Rules](#4-room-inventory-and-type-rules)
5. [Faculty Load Patterns](#5-faculty-load-patterns)
6. [Special Slot Types and Rules](#6-special-slot-types-and-rules)
7. [Code Review — All 12 Uploaded Files](#7-code-review--all-12-uploaded-files)
8. [Frontend Component Review](#8-frontend-component-review)
9. [Corrected Data Model](#9-corrected-data-model)
10. [Solver Constraint Model](#10-solver-constraint-model)
11. [Full Implementation Plan](#11-full-implementation-plan)
12. [File-by-File Fix List](#12-file-by-file-fix-list)

---

## 1. Complete Section Inventory

Every section found across all 46 screenshots, with its current schedule status:

### UG Programs — B.Tech (Full Timetable Active, AY 2026-27)

| Branch | Year | Sections | Count | Key Subjects |
|--------|------|----------|-------|--------------|
| AIML | II | A, B, C, D, E, F, G, H, I, J, K, L | **12** | SFCDS, DMS, DS, AI, DBMS, OOPS, DEF |
| AIML | III | A, B, C, D, E, F, G | **7** | QALR, DL, WT, CV, ADS/MLOP, IDP |
| AIML | IV | A, B, C, D, E | **5** | CNS, TM, KRR, GENAI, IOT, Ethics-AI |
| CS | II | A, B | **2** | MFCS, FIS, CN, DWV, DS, OOPS, DBMS |
| CS | III | (single) | **1** | NS, EH, C&CC, WT, QALR, IDP |
| CS | IV | (single) | **1** | WDS, ID&PS, IOT, ML, CS (Cloud Security) |
| DS | II | A, B | **2** | P&S, OT, DSF, AI, DS, DBMS, OOPS |
| DS | III | A, B | **2** | TSAF, ML, WT, CV, QALR, IDP |
| DS | IV | (single) | **1** | CCA, TM, CNS, GENAI, TSAF |
| CSBS | II | (single) | **1** | P&S, AI, OS, DS, DBMS, OOPS |
| CSBS | III | (single) | **1** | QALR, MWA, DMA, IIMP, AI, IDP |
| CSBS | IV | (single) | **1** | ITPM, IS, BDA, UDSA, AI |
| IOT | II | (single) | **1** | SFCDS, PQC, MPMC, DS, DBMS, DLCO |
| IOT | III | (single) | **1** | CN, MAD, AI&IES, QALR, IOT A&P, IDP |

**UG Active Total: 38 sections**

### PG / Special Programs (AY 2026-27)

| Program | Year | Count | Status | Notes |
|---------|------|-------|--------|-------|
| BS(DS) | II | 1 | Active | FML, FOOP, DBMS, DHV, BEC |
| BS(DS) | III | 1 | Active | ML, WT, FIP, OS, PROJECT |
| MSC(DS) | II | 1 | Active | FIP, DL, BDA, MAD, PROJECT |
| MTECH(DS) | II | 1 | Minimal | Only INTERNSHIP + PROJECT + MOOCs |
| BS(DS) | I | 1 | **EMPTY** | AY 2025-26 template, unfilled |
| MSC(DS) | I | 1 | **EMPTY** | AY 2025-26 template, unfilled |
| MTECH(DS) | I | 1 | **EMPTY** | AY 2025-26 template, unfilled |

**PG Active Total: 4 sections (3 have empty slot grids)**

### Grand Total Active Sections with Real Schedules: **42**

---

## 2. Deep Pattern Analysis from 46 Screenshots

### Pattern 1 — Cell Format (Universal Across ALL Sections)

Every timetable cell contains exactly two lines:

```
┌────────────────────┐
│  DS(P)  ← black   │   Subject code + optional type tag
│  604    ← red     │   Room code
└────────────────────┘
```

**Subject type tags observed:**
- No suffix → Theory Lecture (L): `DS`, `AI`, `DBMS`, `SFCDS`
- `(P)` → Practical Lab: `DS(P)`, `AI(P)`, `DBMS(P)`, `OOPS(P)`
- `(T)` → Tutorial: `DS(T)`, `DMS(T)`, `OOPS(T)`, `DBMS(T)`
- `(T&P)` → Tutorial + Practical listed together in legend: `DEF(T&P)`
- `(L&T)` → Lecture + Tutorial combined slot: `QALR(L&T)` in some DS sections
- Bare word → Special: `LIBRARY`, `QALR`, `OE`, `IDP`, `SL/EL`, `CRT`, `MINORS/HONORS`

**When room code is absent or special:**
- `LIBRARY` → No room code (students go to central library)
- `OE` → No room code (NPTEL self-paced)
- `SL/EL`, `AL/IL` → No room (self-directed learning)
- `CRT` → No room (offsite / auditorium sessions)
- `MINORS/HONORS` → Room code IS given (e.g., `514-A`, `402`, `NB-518`)

### Pattern 2 — Lab Block Placement Rules (CRITICAL for Solver)

Labs **always** occupy 2 consecutive periods. The valid consecutive pairs are:

```
P1 → P2   ✅  (morning block, 8:15–9:55)
P3 → P4   ✅  (mid-morning, 10:10–11:50) — rare but seen in some CS sections
P4 → P5   ✅  (mid-morning to pre-lunch, 11:00–12:40) — seen in BS(DS)
P6 → P7   ✅  (afternoon block, 13:40–15:20)
P7 → P8   ✅  (late afternoon, 14:30–16:05) — very rare
```

**ILLEGAL pairs — these BREAK the break/lunch guard:**
```
P2 → P3   ❌  BREAK falls between 9:55 and 10:10
P5 → P6   ❌  LUNCH falls between 12:40 and 13:40
```

**Visual confirmation from screenshots:**
- II AIML-A: AI(P) is always P1+P2, never P2+P3
- III AIML-A: ADS(P) Monday P1+P2, spanning break would be impossible
- IV AIML-A: CNS(P) Wednesday P3+P4 (confirmed mid-morning lab)
- III AIML-F: FIP(P) uses AFTF-12, always P1+P2

**Solver rule HC-08 must encode:**
```python
BREAK_GUARD_PAIRS = {(2, 3), (5, 6)}  # these can NEVER be a lab pair
VALID_LAB_STARTS = {1, 3, 4, 6, 7}    # period p where p + 1 is valid
```

### Pattern 3 — Faculty Legend Below Grid (Universal)

Every section's Excel sheet has a faculty legend table immediately below the 6×8 grid. Format:

```
Subject(L): Lead Faculty Name
Subject(T&P): Lead Faculty, Co-Faculty-1, Co-Faculty-2, Co-Faculty-3
```

**Example from II AIML-A (Screenshot 1):**
```
Statistical Foundation for Computing and Data Science(L): DR. P. Kalpana
Statistical Foundation for Computing and Data Science(P): DR. P. Kalpana
Discrete Mathematical Structures(L): DR. ANKAMMA RAO MALLELA
Discrete Mathematical Structures(P): DR. ANKAMMA RAO MALLELA
Data Structures(L): Dr. S.Srikantha Reddy
Data Structures(T&P): Dr. S.Srikantha Reddy, P. Girija, K. Nikhitha, Mr. Mahendra Varma
Artificial Intelligence(L): Dr. B. Sudha Rani
Artificial Intelligence(P): Dr. B. Sudha Rani, Ms. D. Urlamma, V. Amarnath
Data Base Management Systems(L): Ms. P Seetha Lakshmi
DBMS(T&P): Ms. P Seetha Lakshmi, CHALLA SAI MOHITHA, GUNTI VASANTHI, Mr K Karthik
Object Oriented Programming(L): Ms. G. Mahalakshmi
OOPS(T&P): Ms. G. Mahalakshmi, PALAPARTHI YAMUNA, PALLAKI SRI HARSHAVARDHAN REDDY, Ms. M. YAMINI
Agentic Tools (IIC - Course)
Data Engineering Foundations
Data Engineering Foundations(T&P): Ms. Vemuri Lakshmi Ravali, Mr. Mahendra Varma
```

**Key observation:** Agentic Tools has NO faculty assigned in the legend — it's an industry course with external instructors. DEF lecture has no faculty listed but T&P does. This means the data model must support `nullable` lecture faculty.

### Pattern 4 — Year-Level Structural Differences

#### II Year (AIML) — 12 sections
- **Structure:** 8 subjects × varying L+T+P credits
- **Total slots/week:** ~36 (75% of 48 available)
- **No** MINORS/HONORS, no CRT, no OE, no SL/EL
- **Has:** LIBRARY (mandatory, 1 slot)
- **Has:** IIC/Agentic Tools (1 slot, no assigned room)
- **DEF:** appears as `DEF` (tutorial, 1 slot) and sometimes `DEF(P)` (2-period lab)
- Rooms used: 601–619, 215–218, 514-A, 514-B, 604–617

#### III Year (AIML) — 7 sections
- **Structure:** 7 subjects — QALR, DL, WT, CV or ADS, MLOP, IDP, OE
- **Total slots/week:** ~30 (fewer because OE/SL slots are not scheduled by dept)
- **Has:** `MINORS/HONORS` — always at P7-P8 on Wednesday and Thursday
- **Has:** `SL/EL` — self-learning slot replacing a regular period
- **Has:** `CRT` — P7-P8 on some days (career/placement training)
- **Has:** `LIB` or `LIBRARY` — 1 slot
- **Has:** `IDP` — project lab (AFTF-12 or AFF-09/10)
- **OE is NPTEL** — no room, no faculty
- **AFTF labs dominate:** DL(P), CV(P), MLOP(P) all use AFTF-12/13/14

#### IV Year (AIML) — 5 sections
- **Structure:** 5-6 subjects — CNS, TM, KRR, GEN AI, IOT, Ethics-AI
- **Total slots/week:** ~25 (lightest load)
- **P1+P2 often occupied by SL/EL/AL/IL** (self-learning placeholder on Mon/Fri/Sat)
- **Has:** `GEN AI & AS` — "Generative AI and Agentic Systems" combined lecture
- **Has:** `MINORS/HONORS` — Wed/Thu P7-P8
- **AFTF labs:** CNS(P), TM(P), GENAI(P) all use AFTF-12/13/14
- **IV AIML-B** shows `AFTF-12(U-BLOCK LOCK)` — coordinator flagged room as reserved
- **IV AIML-D** shows `CAL/AL/P-Block First Floor: skruthi Seminar` — external venue

#### CS Branch Differences (II, III, IV)
- **II CS:** replaces DMS with `MFCS` (Math Foundations for Cyber Security), replaces DEF with `DWV` (Data Wrangling & Visualization), adds `CN` (Computer Networks), `FIS` (Foundations of Info Security)
- **III CS:** Cyber security focus — `NS` (Network Security), `EH` (Ethical Hacking), `C&CC` (Cloud Computing & Cybersecurity, NPTEL), `QALR`
- **IV CS:** `WDS` (Web & Database Security), `ID&PS` (Intrusion Detection & Prevention), cloud-focused

#### DS Branch Differences
- **II DS:** adds `P&S` (Probability & Statistics), `OT` (Optimization Techniques), `DSF` (Foundations of Data Science)
- **III DS:** adds `TSAF` (Time Series Analysis & Forecasting), `ML`
- **IV DS:** adds `CCA` (Cloud Computing & Analytics), `TSAF`
- **Heavy use of rooms 613, 607** which are mid-block classrooms

#### CSBS Branch
- **II CSBS:** adds `OS` (Operating Systems), uses `P&S` instead of DMS
- **III CSBS:** adds `IIMP` (Intro to Innovation, IP Mgmt & Entrepreneurship), `MWA` (Modern Web Applications), `DMA` (Data Mining & Analytics)
- **IV CSBS:** `ITPM`, `IS`, `UDSA`, `BDA` — management + tech combined

#### IOT Branch
- **II IOT:** unique subjects `PQC` (Physics for Quantum Computing), `MPMC` (Microprocessors), `DLCO` (Digital Logic & Computer Organization)
- **III IOT:** `IOT A&P` (IoT Architecture & Protocols), `AI&IES` (AI Integrated Embedded Systems), `MAD`

### Pattern 5 — Minors/Honors Master Schedule (Screenshot 46)

The last screenshot reveals the MINORS/HONORS master coordination sheet:

```
AIML (III Year):
  Minor — Digital Image Processing,  Section A,  Room NB-518,  Tutorial ***
  Minor — Web and Sequence,           Section A,  Room NB-218,  Tutorial ***
  Honors — Data Mining,               Section B,  Room NB-614,  Tutorial ***
  Minor — Deep Learning,              Section A,  Room NB-418,  Tutorial ***

AIML (IV Year):
  Honors — Cloud Computing for ML,    Section A,  Room NB-501,  Lecture ***

CS (III Year):
  Honors — Penetration & Vulnerability Assessment, Sec A, Room 514-B
CS (IV Year):
  Honors — (same subject), Sec A, Room 514-A

CSBS (III): Honors — Image Processing & Pattern Recognition, Room 402
CSBS (IV): Honors — Business Analytics & Decision Systems, Room 502

DS (III): Honors — Web and Sequence Data Mining, Room 514-A
DS (IV): Honors — Business Analytics & Decision Systems, Room 501

IoT (III): Honors — Machine Learning for IoT Systems, Room NB-514
```

**Critical solver rule:** All MINORS/HONORS slots across ALL sections of ALL years must be in the SAME synchronized timeslot (Wed P7+P8 or Thu P7+P8). This is a global cross-section constraint.

### Pattern 6 — SL/EL, AL/IL, CRT — Unscheduled Slots

These appear in grids but are NOT scheduled by the timetable coordinator:

| Code | Full Form | Rule |
|------|-----------|------|
| `SL/EL` | Self Learning / Experimental Learning | Mark as blocked; no faculty, no room needed |
| `AL/IL` | Activity Learning / Interactive Learning | Same as SL/EL |
| `SL/EL/IL` | Combined variant | Same as above |
| `CRT` | Campus Recruitment Training | Placed in P7-P8 by training dept separately |
| `OE` | Open Elective | Student chooses NPTEL course; no room/faculty |
| `PROJECT` | Project Phase I/II | BS/MSC/MTECH only; no room in grid |
| `IIC` | Industry-Integrated Course / Agentic Tools | External instructor; no room assigned |

**Solver implication:** These slots consume timeslot cells but require no faculty/room assignment from the solver. Mark them as `SELF_STUDY` type in the database.

### Pattern 7 — QALR Placement (III Year Universal)

`QALR` (Quantitative Aptitude & Logical Reasoning) appears across ALL III year sections across ALL branches (AIML, CS, DS, CSBS, IOT). The faculty `Mr. T. Krishna` (AIML) and `Sk Chand Basha` (CS/DS) appear consistently. This subject is taught by the Training & Placement (T&P) department, not ACSE faculty, and is always scheduled once per week without a lab.

### Pattern 8 — IDP Placement (III Year Universal)

`IDP` (Inter-Departmental Project with Agentic Tools) appears in ALL III year sections. It always uses AFTF or AFF labs (`AFTF-12`, `AFTF-13`, `AFTF-14`, `AFF-09`). Faculty assigned varies by section. This is a project-based course that needs a 2-period block.

### Pattern 9 — DEF Inconsistency Discovered

From II year screenshots, `DEF` (Data Engineering Foundations) is treated inconsistently:
- In some sections it shows `DEF` (lecture, 1 period) and `DEF(P)` (2-period lab)
- In others it shows only `DEF(T)` (tutorial, 1 period)
- The faculty legend sometimes says "Data Engineering Foundations" with no faculty for lecture
- But T&P version has clear faculty: `Ms. Vemuri Lakshmi Ravali, Mr. S. Uday Kiran, Ms. Sabhamini`

**Root cause:** DEF is a bridge course, not a full 3L+1T+2P subject. Its credits are L=0, T=1, P=2. The "lecture" is optional/self-study; only T and P need scheduling.

### Pattern 10 — Saturday Usage Pattern

Saturday is used but has a lighter load than Mon-Fri:

```
Typical Saturday pattern (from II AIML sections):
  P1: DEF or SFCDS or AI or OOPS (single theory)
  P2: AI or DMS or DBMS (single theory)
  P3-P5: Usually 1-2 theory lectures
  P6-P8: DMS(T) or DBMS(T) or OOPS(T) — tutorials preferred on Saturday
```

No lab (P) blocks are placed on Saturday in any II year section. This seems intentional.

---

## 3. Subject Profiles by Year and Branch

### Complete Weekly Credit Structure

#### II Year — AIML (Sections A–L)

| Code | Full Name | L | T | P | Lab Rooms | Lecture Rooms | Consecutive? |
|------|-----------|---|---|---|-----------|---------------|-------------|
| SFCDS | Statistical Foundation for Computing & Data Science | 3 | 0 | 2 | 611, 612, 616, 617 | 614, 218, 418 | Yes (2-period) |
| DMS | Discrete Mathematical Structures | 3 | 1 | 0 | — | 215, 218, 514-B, 616 | No |
| DS | Data Structures | 3 | 1 | 2 | 601, 604, 605, 615 | 619, 601, 607 | Yes (2-period) |
| AI | Artificial Intelligence Search Methods | 3 | 0 | 2 | 604, 612, 216 | 607, 514-A, 217 | Yes (2-period) |
| DBMS | Database Management Systems | 3 | 1 | 2 | 604, 612, 616 | 607, 611 | Yes (2-period) |
| OOPS | Object Oriented Programming | 3 | 1 | 2 | 604, 606, 611 | 607, 418, 501 | Yes (2-period) |
| DEF | Data Engineering Foundations | 0 | 1 | 2 | 605, 616, 607 | 215 | Yes (2-period) |
| IIC | Agentic Tools (Industry-Integrated) | 0 | 0 | 0 | — | — | No faculty/room |
| LIB | Library | 0 | 0 | 0 | — | — | 1 slot, midday |

**II Year total contact hours/week: 3+3+3+3+3+3+1 = ~19 lecture hrs + labs + tuts = ~36 slot occupancies**

#### III Year — AIML (Sections A–G)

| Code | Full Name | L | T | P | Lab Type | Consecutive? |
|------|-----------|---|---|---|----------|-------------|
| QALR | Quantitative Aptitude & Logical Reasoning | 2 | 1 | 0 | — | No |
| DL | Deep Learning | 3 | 0 | 2 | AFTF GPU | Yes (2-period) |
| WT | Web Technologies | 3 | 0 | 2 | Computer Lab | Yes (2-period) |
| CV | Computer Vision (DE-2) | 3 | 0 | 2 | AFTF GPU | Yes (2-period) |
| ADS | Advanced Data Structures (DE-1) | 3 | 0 | 2 | Computer Lab | Yes (2-period) |
| MLOP | Machine Learning Operations (DE-1 alt) | 3 | 0 | 2 | AFTF GPU | Yes (2-period) |
| FIP | Fundamentals of Image Processing (DE alt) | 3 | 0 | 2 | AFTF GPU | Yes (2-period) |
| IDP | Inter-Departmental Project (Agentic Tools) | 0 | 0 | 2 | AFTF/AFF | Yes (2-period) |
| OE | Open Elective (NPTEL) | 0 | 0 | 0 | — | Self-study |
| M/H | Minors/Honors | 0 | 2 | 2 | Special room | Global sync |
| LIB | Library | 0 | 0 | 0 | — | 1 slot |
| SL/EL | Self Learning | 0 | 0 | 0 | — | Self-study |
| CRT | Campus Recruitment Training | 0 | 0 | 0 | — | P7-P8 |

**III Year total schedulable: ~28 slots/week (OE, SL/EL, CRT are self-study/external)**

#### IV Year — AIML (Sections A–E)

| Code | Full Name | L | T | P | Lab Type | Consecutive? |
|------|-----------|---|---|---|----------|-------------|
| CNS | Cryptography & Network Security | 3 | 0 | 2 | AFTF or computer lab | Yes |
| TM | Text Mining | 3 | 0 | 2 | AFTF/computer lab | Yes |
| KRR | Knowledge Representation & Reasoning | 3 | 1 | 0 | — | No |
| GENAI | Generative AI & Agentic Systems | 3 | 0 | 2 | AFTF GPU | Yes |
| IOT | Internet of Things | 3 | 0 | 2 | Computer/AFF lab | Yes |
| Ethics | Ethics in Computing & AI | 2 | 1 | 0 | — | No |
| M/H | Minors/Honors | — | 2 | 2 | Special room | Global sync |
| SL/EL/AL/IL | Self/Activity Learning | 0 | 0 | 0 | — | Self-study |

---

## 4. Room Inventory and Type Rules

### Complete Room Registry (from all 46 screenshots)

#### Category 1: Regular Classrooms (Theory Lectures + Tutorials)

| Room Code | Floor | Block | Capacity | Seen Used By |
|-----------|-------|-------|----------|--------------|
| 601 | 6 | U-Block | 60 | II-III AIML, DS, CS |
| 602 | 6 | U-Block | 60 | III BS(DS), MSC |
| 603 | 6 | U-Block | 60 | — |
| 607 | 6 | U-Block | 60 | II AIML (very frequent) |
| 608 | 6 | U-Block | 60 | CS, DS, CSBS |
| 609 | 6 | U-Block | 60 | — |
| 610 | 6 | U-Block | 60 | — |
| 613 | 6 | U-Block | 60 | DS, IV AIML |
| 614 | 6 | U-Block | 60 | CSBS, CS, DS |
| 618 | 6 | U-Block | 60 | II AIML, CS |
| 619 | 6 | U-Block | 60 | II AIML (very frequent) |
| 215 | 2 | U-Block | 60 | II AIML (DMS, DEF) |
| 216 | 2 | U-Block | 60 | II AIML, IV AIML |
| 217 | 2 | U-Block | 60 | II AIML-J, MSC |
| 218 | 2 | U-Block | 60 | II AIML, IV AIML |
| 514-A | 5 | U-Block | 60 | II AIML, III AIML |
| 514-B | 5 | U-Block | 60 | II AIML, CS, DS |
| 518 | 5 | U-Block | 60 | III DS, IV AIML |
| 401 | 4 | U-Block | 60 | — |
| 402 | 4 | U-Block | 60 | II CSBS, IV CSBS, BS |
| 418 | 4 | U-Block | 60 | II AIML, IV AIML |
| 501 | 5 | U-Block | ~30 | II AIML-G, II AIML-H, IV DS |
| 502 | 5 | U-Block | ~30 | CSBS, BS(DS) |

#### Category 2: Computer Labs (Practicals for Software Subjects)

| Room Code | Floor | Block | Capacity | Used For |
|-----------|-------|-------|----------|----------|
| 604 | 6 | U-Block | 60 | DS(P), AI(P), DBMS(P), OOPS(P) |
| 605 | 6 | U-Block | 60 | DEF(P), OOPS(P), SFCDS(P) |
| 606 | 6 | U-Block | 60 | II AIML OOPS(P), DS(P) |
| 611 | 6 | U-Block | 60 | SFCDS(P), OOPS(P), DBMS(P) |
| 612 | 6 | U-Block | 60 | AI(P), DBMS(P), DS(P) |
| 615 | 6 | U-Block | 60 | DS(P), OOPS(P) |
| 616 | 6 | U-Block | 60 | SFCDS(P), DMS(P), OOPS(P) |
| 617 | 6 | U-Block | 60 | DBMS(P), DMS(P), DS(P) |

#### Category 3: GPU/AI Labs — AFTF Series (III/IV Year Only)

| Room Code | Floor | Block | Capacity | Used For |
|-----------|-------|-------|----------|----------|
| AFTF-12 | AFTF | U-Block | 60+ | DL(P), CV(P), IDP, QAL(P), FIP(P) |
| AFTF-13 | AFTF | U-Block | 60+ | MLOP(P), DL(P), FIP(P), IDP, CNS(P) |
| AFTF-14 | AFTF | U-Block | 60+ | CV(P), WT(P), DL(P), IDP, GENAI(P) |

#### Category 4: Small Project / Tutorial Rooms — AFF Series

| Room Code | Floor | Block | Capacity | Used For |
|-----------|-------|-------|----------|----------|
| AFF-09 | AFF | U-Block | 30 | IDP, III AIML-F/G project sessions |
| AFF-10 | AFF | U-Block | 30 | IDP, III DS, III CS project sessions |

#### Category 5: Cross-Block / Special

| Room Code | Notes |
|-----------|-------|
| 501A | Small seminar room (III IOT) |
| 619A | Annex to 619 |
| UFTF-13 (U-BLOCK) | IV AIML-D mentions this variant |
| NB-518, NB-214, NB-418 | "NB" prefix = New Block (Minors/Honors sheet) — different building |

### Room Type → Subject Type Compatibility Matrix

```
ROOM TYPE          │ L(Lecture) │ T(Tutorial) │ P(Practical) │ IDP │ M/H │
───────────────────┼────────────┼─────────────┼──────────────┼─────┼─────┤
classroom          │     ✅     │      ✅      │      ❌      │ ❌  │ ✅  │
computer_lab       │     ❌     │      ❌      │      ✅      │ ✅  │ ❌  │
gpu_lab (AFTF)     │     ❌     │      ❌      │      ✅      │ ✅  │ ❌  │
project_room (AFF) │     ❌     │      ❌      │      ✅*     │ ✅  │ ❌  │
small_room (501)   │     ✅     │      ✅      │      ❌      │ ❌  │ ✅  │
nb_room            │     ❌     │      ✅      │      ❌      │ ❌  │ ✅  │
───────────────────┴────────────┴─────────────┴──────────────┴─────┴─────┘
* AFF labs can host small IDP groups but not full 60-student labs
```

---

## 5. Faculty Load Patterns

### Faculty Teaching Multiple Sections (Cross-Section Teaching)

From the legends across II AIML sections:

| Faculty | Subject | Sections Taught | Weekly Slots Total |
|---------|---------|-----------------|-------------------|
| Dr. S.Srikantha Reddy | DS (L+T+P) | II AIML-A, C, E | 3×6 = 18 slots |
| Mr. Bharadwaja Chepuri | DS (L+T+P) | II AIML-B, D, F, G | 4×6 = 24 slots |
| Mr. PLN Manoj Kumar | DS (L+T+P) | II AIML-H, I, L | 3×6 = 18 slots |
| DR. P. Kalpana | SFCDS (L+P) | II AIML-A, F, L | 3×5 = 15 slots |
| DR. BANDI GURAVAIAH | SFCDS (L+P) | II AIML-B, G, K | 3×5 = 15 slots |
| DR. RUSHI PRASAD SAHOO | SFCDS (L+P) | II AIML-C, E, J | 3×5 = 15 slots |
| DR. ANKAMMA RAO MALLELA | DMS (L+T) | II AIML-A, H, L | 3×4 = 12 slots |
| DR. N. BHARGAVI | DMS (L+T) | II AIML-B, F, K | 3×4 = 12 slots |
| DR. MANIGANDAN A | DMS (L+T) | II AIML-C, G, J | 3×4 = 12 slots |
| Ms. G. Mahalakshmi | OOPS (L+T+P) | II AIML-A, D, G | 3×6 = 18 slots |
| Mr. T. Krishna | QALR (L+T) | III AIML-A,B,C,D,E,F,G | 7×3 = 21 slots |

**Critical insight: Mr. T. Krishna's 21-slot load for QALR across 7 sections**
He cannot teach all 7 sections simultaneously. His 7 QALR lectures must all be at DIFFERENT timeslots, making the QALR distribution a highly constrained problem.

### Maximum Load Analysis (AICTE Rules)

```
Faculty Grade         | Max hrs/week | Observed load risk
──────────────────────┼──────────────┼─────────────────────────
Assistant Professor   |   16 hrs     | Mr. Bharadwaja: 24 slots for DS alone → OVERLOADED
Associate Professor   |   14 hrs     | Mr. T. Krishna: 21 slots for QALR → OVERLOADED
Professor             |   12 hrs     | Most Professors within limit
HoD                   |   12 hrs     | Administrative load reduces teaching
```

**The overloading of Mr. Bharadwaja Chepuri and Mr. T. Krishna is a REAL constraint failure in V5.**

The solver must flag when a faculty's total slots exceed their grade limit and either:
1. Refuse to generate and ask coordinator to add more faculty
2. Generate but mark these as soft constraint violations

### Co-Faculty Pattern — Lab Sessions

Every Lab (P) session has 1 Lead + 2-3 Student TAs or Junior Faculty:

```python
# Actual pattern from II AIML screenshots
LAB_TEAM_SIZES = {
    'SFCDS_P': 2,   # Lead + 1 co-faculty
    'DMS_P':   2,   # Lead + 1 co-faculty  
    'DS_P':    4,   # Lead + 3 co-faculty/TAs
    'AI_P':    3,   # Lead + 2 co-faculty
    'DBMS_P':  4,   # Lead + 3 co-faculty/TAs
    'OOPS_P':  4,   # Lead + 3 co-faculty/TAs
    'DEF_P':   3,   # Lead + 2 co-faculty
    'DL_P':    4,   # Lead + 3 co-faculty (AFTF)
    'WT_P':    4,   # Lead + 3 co-faculty
    'CV_P':    4,   # Lead + 3 co-faculty (AFTF)
    'IDP':     1,   # Single faculty guide
}
```

**ALL co-faculty are locked during the same slot as lead faculty.** The solver HC-02 (no faculty double booking) must apply to co-faculty too.

---

## 6. Special Slot Types and Rules

### Complete Slot Type Registry

```python
class SlotType(str, Enum):
    # Regular teaching slots
    LECTURE      = "L"          # 1 period, classroom
    TUTORIAL     = "T"          # 1 period, classroom
    PRACTICAL    = "P"          # 2 consecutive periods, lab
    
    # Fixed institutional slots (DO NOT schedule, just reserve)
    LIBRARY      = "LIBRARY"    # 1 slot per week per section, midday preferred
    IIC          = "IIC"        # Agentic Tools / Industry-Integrated (no room/faculty)
    
    # Self-directed learning (no faculty, no room — just block the cell)
    SELF_STUDY   = "SL_EL"      # SL/EL, AL/IL, IL, SL/EL/IL variants
    OPEN_ELECTIVE = "OE"        # NPTEL, external platform
    
    # External scheduling (CRT dept, Training dept schedule this)
    CRT          = "CRT"        # Career/Placement training (P7-P8)
    
    # Global synchronized — ALL sections same time
    MINORS       = "MINORS"     # Minor course (NB-block rooms)
    HONORS       = "HONORS"     # Honors course (different room)
    MINORS_HONORS = "M_H"       # Combined slot
    
    # Project-based
    IDP          = "IDP"        # Inter-Departmental Project (AFTF/AFF, 2 periods)
    PROJECT      = "PROJECT"    # BS/MSC semester project (flexible)
    
    # Administrative
    BREAK        = "BREAK"      # Tea break (blocked, no teaching)
    LUNCH        = "LUNCH"      # Lunch break (blocked, no teaching)
```

### Global Sync Constraint Details

The Minors/Honors constraint is the most complex global constraint:

```
RULE: ∀ section s ∈ All_III_Year_Sections ∪ All_IV_Year_Sections:
      minors_honors_slot(s) = (day='WED', period=7) ∨ (day='WED', period=8)
                             ∨ (day='THU', period=7) ∨ (day='THU', period=8)
      
      AND: The specific day/period chosen for (WED,P7) must be the SAME for ALL sections
           of the same year level and branch.
```

From the screenshots: Most III AIML sections show MINORS/HONORS at WED-P8 and THU-P8. Some use only one of these.

---

## 7. Code Review — All 12 Uploaded Files

### 7.1 `base.py` — Rating: 8/10

```python
# CURRENT — has this issue:
created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# FIX: datetime.utcnow is deprecated in Python 3.12+
from datetime import datetime, timezone
created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                    onupdate=lambda: datetime.now(timezone.utc))
```

Also: `Base` is imported from `app.core.database` but that file is not provided. Verify `Base = declarative_base()` exists there.

### 7.2 `department.py` — Rating: 6/10

**Issues found:**
1. `head_faculty_id` is Integer but not a ForeignKey — should be `ForeignKey("faculty.id", nullable=True)`
2. Missing `program_type` field: AIML is B.Tech (4yr), MSC is 2yr, MTECH is 2yr — these have different total sections
3. No `is_active` flag to mark departments that have active timetables

**Fix:**
```python
class Department(BaseModel):
    __tablename__ = "departments"
    
    code = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(Text, nullable=False)
    head_faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=True)  # ADD FK
    program_type = Column(String(20), default="BTECH", nullable=False)          # NEW
    # Values: "BTECH", "BSC", "MSC", "MTECH"
```

### 7.3 `academic_year.py` — Rating: 7/10

**Issues found:**
1. Missing `name` field (e.g., "2026-27 Semester I") for display
2. Missing `regulation` field — CS uses different regulation than AIML
3. No `is_current` flag

**Fix:**
```python
class AcademicYear(BaseModel):
    __tablename__ = "academic_years"
    
    year = Column(Integer, nullable=False)          # e.g., 2026
    semester = Column(Integer, nullable=False)       # 1 or 2
    label = Column(String(30), nullable=True)        # NEW: "2026-27 (I Semester)"
    regulation = Column(String(10), nullable=True)   # NEW: "R22", "R25"
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    is_current = Column(Boolean, default=False)      # NEW
```

### 7.4 `branch.py` — Rating: 5/10

**Critical Issue:** `year_level` on Branch is semantically wrong. A Branch is AIML (the program), not "II AIML". The year level belongs to each **section's intake year**, not to the branch definition.

The current schema would require creating 3 separate "Branch" rows for AIML (year_level=2, year_level=3, year_level=4) — that's wrong. AIML is ONE branch running across 4 years.

**Fix:**
```python
class Branch(BaseModel):
    __tablename__ = "branches"
    
    dept_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    code = Column(String(20), nullable=False, index=True)   # "AIML", "CS", "DS", "CSBS", "IOT"
    name = Column(Text, nullable=False)                      # "Artificial Intelligence & Machine Learning"
    total_years = Column(Integer, default=4, nullable=False) # B.Tech=4, BSc=3, MSc=2, MTech=2
    # REMOVE: year_level — this belongs to Section, not Branch
    
    department = relationship("Department", back_populates="branches")
    sections = relationship("Section", back_populates="branch")
```

### 7.5 `section.py` — Rating: 8/10

Good model but minor fix needed:

```python
class Section(BaseModel):
    __tablename__ = "sections"
    
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    year_level = Column(Integer, nullable=False)    # MOVED HERE from Branch: 2, 3, or 4
    label = Column(String(10), nullable=False)       # "A", "B", ..., "L"
    name = Column(String(50), nullable=False, index=True)  # "II AIML-A"
    strength = Column(Integer, default=60, nullable=False)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)  # NEW
    
    # Add unique constraint: (branch_id, year_level, label, academic_year_id)
    __table_args__ = (
        UniqueConstraint('branch_id', 'year_level', 'label', 'academic_year_id',
                         name='uq_section_identity'),
    )
```

### 7.6 `faculty.py` — Rating: 7/10

**Issues found:**
1. `availability` JSON has no documented schema — will cause bugs at runtime
2. No `employee_id` or `email` for identification
3. No `is_external` flag for industry faculty (Agentic Tools IIC)

**Fix:**
```python
class Faculty(BaseModel):
    __tablename__ = "faculty"
    
    dept_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    name = Column(Text, nullable=False, index=True)
    designation = Column(String(50), default="Assistant Professor", nullable=False)
    max_hours_per_week = Column(Integer, default=16, nullable=False)
    # availability JSON schema: {"MON": [1,2,3,4,5,6,7,8], "TUE": [1,2,3,...], ...}
    # Missing period = unavailable. If key absent = fully available that day.
    availability = Column(JSON, nullable=True, comment=
        'Dict of day->List[int] of available periods. Absent day = fully available.')
    employee_id = Column(String(20), nullable=True, unique=True)  # NEW
    is_external = Column(Boolean, default=False, nullable=False)   # NEW — for IIC/industry faculty
```

### 7.7 `subject.py` — CRITICAL ISSUE — Rating: 3/10

**The most broken model.** A subject has separate L, T, and P slots. The current schema stores only one `type` and one `hours_per_week`, which means:
- DS cannot be represented as "L=3, T=1, P=2"
- The solver cannot distinguish "how many lecture rooms needed" from "how many lab rooms needed"
- `is_lab` is a bool but a subject can be BOTH L (lecture) AND P (lab)

**Full Fix:**
```python
class Subject(BaseModel):
    __tablename__ = "subjects"
    
    dept_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    code = Column(String(30), nullable=False, index=True)  # "DS", "AI", "DBMS"
    full_name = Column(Text, nullable=False)
    
    # LTP Credit Structure — replaces type + hours_per_week + is_lab
    lecture_hours_per_week   = Column(Integer, default=3, nullable=False)  # L
    tutorial_hours_per_week  = Column(Integer, default=0, nullable=False)  # T
    lab_hours_per_week       = Column(Integer, default=0, nullable=False)  # P
    lab_consecutive_periods  = Column(Integer, default=2, nullable=True)   # 2 or 3 (NULL if no lab)
    
    # Room requirements
    requires_lab_room      = Column(Boolean, default=False, nullable=False)
    requires_gpu_lab       = Column(Boolean, default=False, nullable=False)  # NEW: AFTF labs
    preferred_room_type    = Column(String(30), nullable=True)  # "computer_lab", "gpu_lab"
    
    # Special slot types
    slot_type = Column(String(20), default="REGULAR", nullable=False)
    # Values: "REGULAR", "LIBRARY", "IIC", "SELF_STUDY", "OE", "CRT", "MINORS", "HONORS", "IDP", "PROJECT"
    
    # Keep for legacy compatibility
    code_prefix = Column(String(5), nullable=True)  # "DS" for DS(L), DS(T), DS(P) grouping
    
    __table_args__ = (
        UniqueConstraint('code', 'dept_id', name='uq_subject_code_dept'),
    )
```

**Subject seeding from patterns:**
```python
SUBJECT_SEEDS = [
    # II Year AIML
    {"code": "SFCDS", "full_name": "Statistical Foundation for Computing and Data Science",
     "lecture_hours": 3, "tutorial_hours": 0, "lab_hours": 2,
     "lab_consecutive": 2, "requires_lab_room": True, "requires_gpu_lab": False},
    
    {"code": "DMS", "full_name": "Discrete Mathematical Structures",
     "lecture_hours": 3, "tutorial_hours": 1, "lab_hours": 0,
     "lab_consecutive": None, "requires_lab_room": False},
    
    {"code": "DS", "full_name": "Data Structures",
     "lecture_hours": 3, "tutorial_hours": 1, "lab_hours": 2,
     "lab_consecutive": 2, "requires_lab_room": True},
    
    {"code": "AI", "full_name": "Artificial Intelligence Search Methods for Problem Solving",
     "lecture_hours": 3, "tutorial_hours": 0, "lab_hours": 2,
     "lab_consecutive": 2, "requires_lab_room": True},
    
    {"code": "DBMS", "full_name": "Database Management Systems",
     "lecture_hours": 3, "tutorial_hours": 1, "lab_hours": 2,
     "lab_consecutive": 2, "requires_lab_room": True},
    
    {"code": "OOPS", "full_name": "Object Oriented Programming",
     "lecture_hours": 3, "tutorial_hours": 1, "lab_hours": 2,
     "lab_consecutive": 2, "requires_lab_room": True},
    
    {"code": "DEF", "full_name": "Data Engineering Foundations",
     "lecture_hours": 0, "tutorial_hours": 1, "lab_hours": 2,
     "lab_consecutive": 2, "requires_lab_room": True},
    
    # III Year AIML
    {"code": "QALR", "full_name": "Quantitative Aptitude & Logical Reasoning",
     "lecture_hours": 2, "tutorial_hours": 1, "lab_hours": 0, "requires_lab_room": False},
    
    {"code": "DL", "full_name": "Deep Learning",
     "lecture_hours": 3, "tutorial_hours": 0, "lab_hours": 2,
     "lab_consecutive": 2, "requires_lab_room": True, "requires_gpu_lab": True},
    
    {"code": "WT", "full_name": "Web Technologies",
     "lecture_hours": 3, "tutorial_hours": 0, "lab_hours": 2,
     "lab_consecutive": 2, "requires_lab_room": True},
    
    {"code": "CV", "full_name": "Computer Vision",
     "lecture_hours": 3, "tutorial_hours": 0, "lab_hours": 2,
     "lab_consecutive": 2, "requires_lab_room": True, "requires_gpu_lab": True},
    
    {"code": "IDP", "full_name": "Inter-Departmental Project with Agentic Tools",
     "lecture_hours": 0, "tutorial_hours": 0, "lab_hours": 2,
     "lab_consecutive": 2, "requires_lab_room": True, "slot_type": "IDP"},
    
    # IV Year AIML
    {"code": "CNS", "full_name": "Cryptography and Network Security",
     "lecture_hours": 3, "tutorial_hours": 0, "lab_hours": 2,
     "lab_consecutive": 2, "requires_lab_room": True, "requires_gpu_lab": True},
    
    {"code": "GENAI", "full_name": "Generative AI and Agentic Systems",
     "lecture_hours": 3, "tutorial_hours": 0, "lab_hours": 2,
     "lab_consecutive": 2, "requires_lab_room": True, "requires_gpu_lab": True},
]
```

### 7.8 `section_subject.py` — CRITICAL ISSUE — Rating: 4/10

**Problem:** `total_slots_needed` is one integer. For DS (3L+1T+2P), the solver needs to know:
- 3 slots must be in classrooms (L)
- 1 slot must be in a classroom (T)
- 2 slots must be consecutive in a lab (P)

This distinction is completely lost with a single total.

**Full Fix:**
```python
class SectionSubject(BaseModel):
    __tablename__ = "section_subjects"
    
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    
    # Faculty assignments — split by slot type
    lecture_faculty_id  = Column(Integer, ForeignKey("faculty.id"), nullable=True)
    tutorial_faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=True)  # NEW
    lab_lead_faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=True)  # NEW (renamed)
    lab_co_faculty_ids  = Column(JSON, nullable=True)  # List[int] of co-faculty IDs
    
    # Slot counts — CRITICAL for solver
    lecture_slots_needed  = Column(Integer, default=3, nullable=False)  # NEW
    tutorial_slots_needed = Column(Integer, default=0, nullable=False)  # NEW
    lab_slots_needed      = Column(Integer, default=0, nullable=False)  # NEW
    # lab_slots_needed=2 means ONE 2-period block (not two separate periods)
    # So total cell occupancy = lecture_slots + tutorial_slots + lab_slots
    
    # Override consecutive from subject level if needed
    lab_consecutive_override = Column(Integer, nullable=True)  # NULL = use subject default
    
    __table_args__ = (
        UniqueConstraint('section_id', 'subject_id', name='uq_section_subject'),
    )
    
    # Relationships
    section          = relationship("Section", back_populates="section_subjects")
    subject          = relationship("Subject", back_populates="section_subjects")
    lecture_faculty  = relationship("Faculty", foreign_keys=[lecture_faculty_id])
    tutorial_faculty = relationship("Faculty", foreign_keys=[tutorial_faculty_id])
    lab_lead_faculty = relationship("Faculty", foreign_keys=[lab_lead_faculty_id])
```

### 7.9 `room.py` — Rating: 6/10

**Issues found:**
1. `floor = Column(Integer, default=6)` — AFF/AFTF rooms don't have integer floor numbers
2. `block = Column(String(30), default="U-Block")` — "NB" (New Block) rooms from Minors/Honors sheet not handled
3. No `gpu_capable` flag for AFTF rooms vs regular computer labs

**Fix:**
```python
class Room(BaseModel):
    __tablename__ = "rooms"
    
    dept_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    room_type = Column(String(30), nullable=False)  # renamed from 'type' (reserved word)
    # Values: "classroom", "computer_lab", "gpu_lab", "project_room", "seminar_hall", "external"
    capacity = Column(Integer, default=60, nullable=False)
    floor = Column(String(10), nullable=True)  # Changed to String: "6", "5", "AFTF", "AFF", "NB"
    block = Column(String(30), default="U-Block", nullable=False)
    gpu_capable = Column(Boolean, default=False, nullable=False)  # NEW: True for AFTF labs
    is_available = Column(Boolean, default=True, nullable=False)  # NEW: can be locked for maintenance
```

### 7.10 `time_slot.py` — Rating: 7/10

**Issues found:**
1. `period` is nullable — but all real periods have numbers (1-8). Only breaks are different.
2. Missing UNIQUE constraint on (day, period)
3. Missing `slot_label` for display ("P1", "P2", "TEA BREAK", "LUNCH")

**Fix:**
```python
class TimeSlot(BaseModel):
    __tablename__ = "time_slots"
    
    day = Column(String(3), nullable=False, index=True)  # "MON"-"SAT"
    period = Column(Integer, nullable=True)               # 1-8, NULL for breaks
    slot_label = Column(String(20), nullable=True)        # NEW: "P1", "TEA BREAK", "LUNCH"
    start_time = Column(Time, nullable=False)             # make non-nullable
    end_time = Column(Time, nullable=False)               # make non-nullable
    is_blocked = Column(Boolean, default=False, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('day', 'period', name='uq_timeslot_day_period'),
    )
```

**Seeding the 60 time slots (6 days × 10 rows including 2 breaks):**
```python
TIMESLOT_SEEDS = []
DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT"]
PERIODS_DATA = [
    (1,  "P1",          "08:15", "09:05", False),
    (2,  "P2",          "09:05", "09:55", False),
    (None, "TEA BREAK", "09:55", "10:10", True),
    (3,  "P3",          "10:10", "11:00", False),
    (4,  "P4",          "11:00", "11:50", False),
    (5,  "P5",          "11:50", "12:40", False),
    (None, "LUNCH",     "12:40", "13:40", True),
    (6,  "P6",          "13:40", "14:30", False),
    (7,  "P7",          "14:30", "15:20", False),
    (8,  "P8",          "15:20", "16:05", False),
]
for day in DAYS:
    for period, label, start, end, blocked in PERIODS_DATA:
        TIMESLOT_SEEDS.append({
            "day": day, "period": period, "slot_label": label,
            "start_time": start, "end_time": end, "is_blocked": blocked
        })
```

### 7.11 `timetable.py` — Rating: 7/10

**Issues found:**
1. `TimetableVersion.solver_run_id` is `Integer` without `ForeignKey` — orphan reference
2. `TimetableEntry.faculty_ids` JSON — the format `List[int]` should be documented and validated
3. `entry_type` uses "L"/"T"/"P" but needs to include "LIBRARY", "IIC", "SL_EL", "OE", "IDP", "M_H" etc.

**Fix:**
```python
class TimetableVersion(BaseModel):
    __tablename__ = "timetable_versions"
    
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=False)
    version_label = Column(String(20), nullable=False, index=True)  # "V5", "AUTO-V6"
    valid_from = Column(Date, nullable=True)
    is_current = Column(Boolean, default=False, nullable=False)
    solver_run_id = Column(Integer, ForeignKey("solver_runs.id"), nullable=True)  # FIX: add FK
    source = Column(String(20), default="MANUAL", nullable=False)  # NEW: "MANUAL", "SOLVER", "IMPORTED"
    notes = Column(Text, nullable=True)  # NEW: version notes

class TimetableEntry(BaseModel):
    __tablename__ = "timetable_entries"
    
    timetable_version_id = Column(Integer, ForeignKey("timetable_versions.id"), nullable=False)
    section_id           = Column(Integer, ForeignKey("sections.id"), nullable=False)
    subject_id           = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    room_id              = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    time_slot_id         = Column(Integer, ForeignKey("time_slots.id"), nullable=False)
    faculty_ids          = Column(JSON, nullable=True)  # List[int]: [lead_id, co1_id, co2_id]
    entry_type           = Column(String(20), default="L", nullable=False)
    # Values: "L","T","P","LIBRARY","IIC","SL_EL","OE","CRT","IDP","M_H","PROJECT","BREAK","LUNCH"
    is_global_sync       = Column(Boolean, default=False, nullable=False)  # True for OE, M/H
    span_periods         = Column(Integer, default=1, nullable=False)  # NEW: 1 or 2 (for lab blocks)
    raw_subject_text     = Column(String(100), nullable=True)  # Keep for import traceability
    raw_room_text        = Column(String(50), nullable=True)   # Keep for import traceability
    
    __table_args__ = (
        # Prevent double-booking a section at the same time
        UniqueConstraint('timetable_version_id', 'section_id', 'time_slot_id',
                         name='uq_entry_section_slot'),
    )
```

### 7.12 `solver_run.py` — Rating: 8/10

Minor issue: `generation_count` only makes sense for GA algorithm.

```python
class SolverRun(BaseModel):
    __tablename__ = "solver_runs"
    
    started_at       = Column(DateTime(timezone=True), nullable=True)
    completed_at     = Column(DateTime(timezone=True), nullable=True)
    algorithm        = Column(String(50), default="CP-SAT", nullable=False)
    status           = Column(String(20), default="pending", nullable=False)
    # status values: "pending", "running", "completed", "failed", "cancelled"
    hard_violations  = Column(Integer, default=0, nullable=False)
    soft_violations  = Column(Integer, default=0, nullable=False)
    fitness_score    = Column(Float, default=0.0, nullable=False)
    generation_count = Column(Integer, default=0, nullable=False)  # GA only, 0 for CP-SAT
    runtime_seconds  = Column(Float, default=0.0, nullable=False)
    scope_json       = Column(JSON, nullable=True)  # NEW: which sections were solved
    config           = Column(JSON, nullable=True)
    error_message    = Column(Text, nullable=True)  # NEW: failure reason
```

---

## 8. Frontend Component Review

### 8.1 `TimetableGrid.tsx` — Rating: 6/10

**Issue 1: Negative period IDs are an anti-pattern**
```typescript
// CURRENT — bug-prone:
{ id: -1, label: "TEA BREAK", time: "09:55 - 10:10", isBreak: true },
{ id: -2, label: "LUNCH BREAK", time: "12:40 - 01:40", isBreak: true },

// FIX: use null and discriminate by isBreak flag
{ id: null, label: "TEA BREAK", time: "09:55 - 10:10", isBreak: true },
{ id: null, label: "LUNCH BREAK", time: "12:40 - 13:40", isBreak: true },
// Also fix "01:40" → "13:40" (12-hour confusion in display)
```

**Issue 2: `facultyName` is a single string but labs have 4 faculty**
```typescript
// CURRENT:
facultyName: string;  // "Dr. Srikantha Reddy"

// FIX:
facultyNames: string[];     // ["Dr. Srikantha Reddy", "P. Girija", "K. Nikhitha"]
primaryFaculty: string;     // "Dr. Srikantha Reddy"
coFaculty: string[];        // ["P. Girija", "K. Nikhitha", "Mr. Mahendra Varma"]
```

**Issue 3: No visual indicator for multi-period lab spans**

Labs in P1+P2 should render as a single merged cell spanning 2 rows. Current implementation renders two separate cells with the same data — a visual inconsistency that makes the grid look like a clash.

```typescript
// FIX: Add spanPeriods field and merge rendering
interface SlotEntry {
  spanPeriods?: number;  // 1 = single period, 2 = lab block (P1+P2 or P6+P7)
}

// In render: when spanPeriods === 2 and period is "start of span":
// render cell with rowSpan={2}, skip the next period cell
```

**Issue 4: Missing slot type colors**

From screenshots, timetables use distinct colors per subject type. Current `getSlotStyle` only handles L/P/T/LIBRARY/CLASH. Missing:

```typescript
// ADD to getSlotStyle:
case "IDP":    return "bg-teal-100 border-l-4 border-l-teal-600";
case "MINORS_HONORS": return "bg-violet-100 border-l-4 border-l-violet-600";
case "SL_EL":  return "bg-gray-100 border-l-4 border-l-gray-400 italic";
case "OE":     return "bg-yellow-50 border-l-4 border-l-yellow-400";
case "CRT":    return "bg-orange-100 border-l-4 border-l-orange-500";
case "QALR":   return "bg-indigo-100 border-l-4 border-l-indigo-600";
```

**Issue 5: The legend is at top — real timetables show it below the grid**

The real Excel format places the faculty legend BELOW the grid. The component should render it at the bottom.

### 8.2 `ScheduleSetupWizard.tsx` — Rating: 5/10

**Issue 1: Hardcoded faculty pool (17 faculty) vs 80+ real faculty**
```typescript
// CURRENT: 17 hardcoded names
const FACULTY_POOL = ["Dr. S. Srikantha Reddy", ...]

// FIX: Load from API
const { data: facultyList } = useQuery({
  queryKey: ['faculty', yearLevel, branch],
  queryFn: () => timetableApi.getFaculty({ yearLevel, branch })
})
```

**Issue 2: `YEAR_SECTIONS` only shows subset of sections**
```typescript
// CURRENT:
"II Year": ["II AIML-A", "II AIML-B", "II AIML-C", "II CS-A", "II DS-A"]
// Missing II AIML-D through L, II DS-B, II CSBS, II IOT!

// FIX: Load dynamically from API
const { data: sections } = useQuery({
  queryKey: ['sections', yearLevel, branch],
  queryFn: () => timetableApi.getSections({ year_level: yearLevel, branch })
})
```

**Issue 3: `MINORS/HONORS` is modeled as a regular P-type subject**
```typescript
// CURRENT (wrong):
{ subject_code: "MINORHONOR", subject_type: "P", weekly_hours: 2, continuous_slots: 2 }

// FIX: Treat as a global-sync slot type, not a regular subject
// The wizard should have a separate "Global Sync Slots" section:
// - Minors/Honors: DAY={Wed/Thu} PERIODS={7+8} — auto-applied to all III/IV year sections
// - Open Elective: handled separately (no room/faculty)
```

**Issue 4: `faculty_name` in `CourseAssignmentInput` conflicts with backend `primary_faculty`**

The frontend type uses `faculty_name` but the backend schema (from master plan) uses `lecture_faculty_id`. The wizard sends strings but the API expects IDs.

```typescript
// FIX: Add faculty resolution step before API call
const resolveToIds = async (assignments: CourseAssignmentInput[]) => {
  return assignments.map(a => ({
    ...a,
    lecture_faculty_id: facultyNameToIdMap[a.faculty_name],
    lab_co_faculty_ids: a.co_faculty.map(n => facultyNameToIdMap[n])
  }))
}
```

**Issue 5: No LIBRARY slot configuration**

LIBRARY is mandatory (1 slot/week/section) but doesn't appear in the wizard. It must be auto-added by the solver.

**Issue 6: No validation that total weekly slots fit within 48**
```typescript
// ADD validation before step 4:
const totalSlotsNeeded = assignments.reduce((sum, a) => {
  return sum + (a.subject_type === 'L' ? a.weekly_hours : 
                a.subject_type === 'T' ? a.weekly_hours :
                a.weekly_hours);  // P counts as block
}, 0) + 1; // +1 for LIBRARY

if (totalSlotsNeeded > 40) {  // 48 - 8 reserved for breaks/free
  setError(`Total slots ${totalSlotsNeeded} exceeds safe limit of 40/week`);
  return;
}
```

---

## 9. Corrected Data Model

### Complete ERD (Entity Relationship Summary)

```
AcademicYear (1) ─────────────── (N) Section
     │                                  │
     │                            (N) SectionSubject
     │                                  │
Department (1) ──── (N) Branch ──── (used by Section)
     │                   │
     ├── (N) Faculty      └─── (multiple years)
     ├── (N) Subject
     └── (N) Room

Faculty ──── (N) SectionSubject (lecture_faculty_id, lab_lead_faculty_id)
           └── (JSON) lab_co_faculty_ids → List[Faculty.id]

TimeSlot (48 rows: 6 days × 8 periods + 12 blocked = 72 rows total)

TimetableVersion ──── (N) TimetableEntry
                            ├── section_id → Section
                            ├── subject_id → Subject (nullable for LIBRARY, SL/EL)
                            ├── room_id    → Room (nullable for OE, SL/EL, IIC)
                            ├── time_slot_id → TimeSlot
                            └── faculty_ids  → JSON[int]

SolverRun ──── (used by) TimetableVersion.solver_run_id
```

---

## 10. Solver Constraint Model

### Complete Constraint Set (HC = Hard, SC = Soft)

#### Hard Constraints — ZERO violations required

```python
# HC-01: No room double-booking
# ∀ room r, ∀ timeslot t: count(entries where room=r, timeslot=t) ≤ 1
# Exception: rooms where is_global_sync=True may share (e.g., joint OE lecture)

# HC-02: No faculty double-booking (lead AND co-faculty)
# ∀ faculty f, ∀ timeslot t: count(entries where f in faculty_ids, timeslot=t) ≤ 1

# HC-03: One class per section per timeslot
# ∀ section s, ∀ timeslot t: count(entries where section=s, timeslot=t) ≤ 1

# HC-04: Subject frequency met exactly
# ∀ (section, subject): count(L entries) = lecture_slots_needed
#                        count(T entries) = tutorial_slots_needed
#                        count(P entries) = lab_slots_needed (as blocks)

# HC-05: Room capacity ≥ section strength
# ∀ entry e: room.capacity ≥ section.strength

# HC-06: Room type compatibility
# L/T entries → classroom or seminar_hall only
# P entries   → computer_lab or gpu_lab or project_room
# GPU-required subjects (DL, CV, MLOP, GENAI, CNS) → gpu_lab preferred, computer_lab fallback

# HC-07: Break and lunch are blocked
# No entry in any timeslot where is_blocked = True

# HC-08: Lab blocks must be consecutive and uninterrupted
# If DS(P) is at period p on day d, then period p+1 on same day must also be DS(P)
# INVALID: (day=MON, period=2) → (day=MON, period=3) because BREAK falls between
# INVALID: (day=MON, period=5) → (day=MON, period=6) because LUNCH falls between
FORBIDDEN_LAB_STARTS = {2, 5}  # periods where consecutive block crosses break/lunch

# HC-09: Faculty availability respected
# If faculty f has availability = {"MON": [3,4,5,6,7,8]}, they cannot be assigned P1 or P2 on MON

# HC-10: Global sync slots fixed
# All MINORS/HONORS entries across ALL sections of same year must be at same (day, period)
# Valid candidates: (WED, P7), (WED, P8), (THU, P7), (THU, P8)
# AND: the 2 consecutive M/H periods must be adjacent
```

#### Soft Constraints — Minimized

```python
# SC-01: Faculty weekly load ≤ grade limit
# Penalty 50 per excess hour over limit

# SC-02: Faculty daily load ≤ 4 consecutive periods
# Penalty 30 per day-faculty pair exceeding 4 consecutive

# SC-03: No student free gaps (compact schedule)
# Penalty 10 per idle period between two occupied periods in same section's day

# SC-04: Library slot in midday (P4 or P5)
# Penalty 5 per section where LIBRARY is not in {P4, P5}

# SC-05: Spread subjects across days
# Penalty 20 per subject that has 2+ lecture slots on the same day for same section

# SC-06: Labs preferred in morning block (P1-P2) over afternoon (P6-P7)
# Penalty 5 per lab placed in P6-P7 instead of P1-P2

# SC-07: Saturday lightweight
# Penalty 15 per lab (P) placed on Saturday

# SC-08: GPU labs reserved for GPU-required subjects
# Penalty 25 per non-GPU subject placed in AFTF lab (wastes high-compute resources)

# SC-09: Faculty building travel time
# Penalty 10 if same faculty has consecutive periods in rooms far apart
# (e.g., Period 3 in Room 215 and Period 4 in AFTF-14 — different floors)

# SC-10: Section load balance across days
# Penalty 5 per day where section has 0 classes while other days have 7-8 classes
```

### Solver Decomposition Strategy

Given 42 sections, the full model has ~600k variables. Run CP-SAT in stages:

```
Stage 1: Solve each YEAR LEVEL independently
  ├── Solve all 12 II AIML sections together (shared faculty constraint)
  ├── Solve 7 III AIML sections together
  ├── Solve 5 IV AIML sections together
  ├── Solve CS sections (2+1+1=4) together
  ├── Solve DS sections (2+2+1=5) together
  └── Solve minor branches (CSBS, IOT, BS, MSC, MTECH) individually

Stage 2: Cross-year GLOBAL constraints
  ├── Fix MINORS/HONORS timeslots across III+IV year sections
  ├── Fix QALR timeslot for Mr. T. Krishna (7 sections → 7 different times)
  └── Fix OE slots (synchronized per branch per year)

Stage 3: Soft constraint optimization (GA or Local Search)
  └── Improve fitness score without violating hard constraints
```

---

## 11. Full Implementation Plan

### Phase 0 — Already Done ✅
- Problem documented in README
- AGENTS.md defined
- Backend model files created (12 files uploaded)
- TimetableGrid component created
- ScheduleSetupWizard component created

### Phase 1 — Fix Models (Week 1, Days 1-3)

**Day 1: Fix all 12 model files**

File-by-file changes (see Section 12 for exact code):
1. `base.py` — Fix datetime deprecation
2. `department.py` — Add FK for head_faculty_id, add program_type
3. `academic_year.py` — Add label, regulation, is_current
4. `branch.py` — Remove year_level (move to Section)
5. `section.py` — Add year_level, is_active, UniqueConstraint
6. `faculty.py` — Add employee_id, is_external, document availability JSON
7. `subject.py` — COMPLETE REWRITE: separate L/T/P hours, gpu flag, slot_type
8. `section_subject.py` — COMPLETE REWRITE: separate lecture/tutorial/lab faculty + slot counts
9. `room.py` — Fix floor type to String, add gpu_capable, rename `type` to `room_type`
10. `time_slot.py` — Add slot_label, make times non-nullable, add UniqueConstraint
11. `timetable.py` — Fix solver_run_id FK, add span_periods, add source, entry_type values
12. `solver_run.py` — Add scope_json, error_message, fix datetime

**Day 2: Create `core/database.py` and `core/config.py`**

```python
# backend/app/core/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

class Base(DeclarativeBase):
    pass

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

**Day 3: Alembic migrations + seed data**

```bash
alembic init alembic
alembic revision --autogenerate -m "initial_corrected_schema"
alembic upgrade head

# Seed in order:
python seed/01_timeslots.py    # 72 rows (6 days × 12 rows including breaks)
python seed/02_departments.py  # 1 row: ACSE
python seed/03_branches.py     # AIML, CS, DS, CSBS, IOT, BS(DS), MSC(DS), MTECH(DS)
python seed/04_faculty.py      # 80+ faculty from extracted legends
python seed/05_rooms.py        # 35+ rooms from all screenshots
python seed/06_subjects.py     # ~60 unique subject codes
python seed/07_academic_year.py # 2026-27 Semester I
python seed/08_sections.py     # 42 sections
python seed/09_section_subjects.py  # ~350 section-subject mappings with faculty
```

### Phase 2 — Excel Parser + Conflict Checker (Week 1, Days 4-5)

**Build `backend/parser/excel_parser.py`:**

```python
# Key parsing logic for VFSTR format
def parse_cell(cell_value: str) -> Optional[ParsedSlot]:
    """Parse 'DS(P)\n604' or 'SFCDS\n218' or 'LIBRARY' """
    if not cell_value or cell_value in BLOCKED_VALUES:
        return None
    
    lines = str(cell_value).strip().split('\n')
    subject_raw = lines[0].strip()
    room_raw = lines[1].strip() if len(lines) > 1 else None
    
    # Extract type tag
    slot_type = "L"  # default
    if "(P)" in subject_raw:
        slot_type = "P"
    elif "(T)" in subject_raw:
        slot_type = "T"
    elif subject_raw == "LIBRARY":
        slot_type = "LIBRARY"
    elif subject_raw in {"OE", "SL/EL", "AL/IL", "SL/EL/IL", "CRT"}:
        slot_type = "SELF_STUDY"
    elif "MINORS" in subject_raw or "HONORS" in subject_raw:
        slot_type = "M_H"
    elif subject_raw == "IDP":
        slot_type = "IDP"
    
    subject_code = subject_raw.replace("(P)","").replace("(T)","").replace("(L)","").strip()
    
    return ParsedSlot(subject_code=subject_code, room_code=room_raw, slot_type=slot_type)
```

**Build `backend/solver/conflict_checker.py` (standalone, no DB dependency):**

```python
def check_all_conflicts(sections: List[ParsedSection]) -> ConflictReport:
    room_usage: Dict[Tuple, List] = {}
    faculty_usage: Dict[Tuple, List] = {}
    
    for section in sections:
        for slot in section.slots:
            if slot.room_code:
                key = (slot.day, slot.period, slot.room_code)
                room_usage.setdefault(key, []).append((section.name, slot.subject_code))
            
            for faculty in slot.all_faculty:
                key = (slot.day, slot.period, faculty)
                faculty_usage.setdefault(key, []).append((section.name, slot.subject_code))
    
    room_clashes = [(k, v) for k, v in room_usage.items() if len(v) > 1]
    faculty_clashes = [(k, v) for k, v in faculty_usage.items() if len(v) > 1]
    
    return ConflictReport(
        room_clashes=room_clashes,        # Should be 51 for V5
        faculty_clashes=faculty_clashes,   # Should be 0 for V5
        total_sections=len(sections),
        total_slots=sum(len(s.slots) for s in sections)
    )
```

**Baseline validation test (must pass before proceeding):**
```bash
python parser/excel_parser.py --input data/ACSE_TIMETABLE_V5.xlsx --validate
# Expected output:
# ✅ Parsed: 42 sections, 1,000 slots
# ✅ Faculty mappings: 384
# ❌ Room clashes: 51
# ✅ Faculty clashes: 0
```

### Phase 3 — FastAPI Backend (Week 2)

**Day 1-2: Core API routes**

```
GET  /api/v1/health
GET  /api/v1/sections?branch=AIML&year=2&academic_year_id=1
GET  /api/v1/sections/{id}
POST /api/v1/sections

GET  /api/v1/faculty?dept_id=1
GET  /api/v1/faculty/{id}/schedule   ← faculty's full week view
GET  /api/v1/faculty/{id}/load       ← hours assigned this week

GET  /api/v1/rooms?type=computer_lab&block=U-Block
GET  /api/v1/subjects?year=2&branch=AIML

GET  /api/v1/timetable/{version_id}/section/{section_id}
GET  /api/v1/timetable/{version_id}/faculty/{faculty_id}
GET  /api/v1/timetable/{version_id}/room/{room_id}

GET  /api/v1/validate/{version_id}
     Response: {hard_violations: 51, soft_violations: 0, room_clashes: [...], faculty_clashes: [...]}

POST /api/v1/import/excel
     Body: multipart/form-data with .xlsx file
     Response: {version_id, sections_found, slots_parsed, clash_report}

POST /api/v1/solve
     Body: {algorithm, scope, timeout, sections}
     Response: {run_id}

GET  /api/v1/solve/{run_id}/status
WS   /api/v1/solve/{run_id}/stream

GET  /api/v1/export/{version_id}/excel
GET  /api/v1/export/{version_id}/pdf/{section_id}
```

**Day 3-5: Celery solver task**

```python
# backend/tasks/solver_tasks.py
from celery import shared_task
from ortools.sat.python import cp_model

@shared_task(bind=True, name="solver.run_cpsat")
def run_cpsat_solver(self, run_id: int, config: dict):
    """CP-SAT solver as background Celery task"""
    solver_run = db.get(SolverRun, run_id)
    solver_run.status = "running"
    db.commit()
    
    try:
        model = cp_model.CpModel()
        # Build variables and constraints (see Section 10)
        # ...
        
        class ProgressCallback(cp_model.CpSolverSolutionCallback):
            def on_solution_callback(self):
                # Broadcast to WebSocket
                ws_manager.broadcast(run_id, {
                    "type": "progress",
                    "hard_violations": self.violation_count,
                    "runtime": self.WallTime()
                })
        
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = config.get("timeout", 120)
        solver.parameters.num_search_workers = 8
        status = solver.Solve(model, ProgressCallback())
        
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            save_solution_to_db(solver, variables, run_id)
            solver_run.status = "completed"
            solver_run.hard_violations = 0
        else:
            solver_run.status = "failed"
            solver_run.error_message = "No feasible solution found"
    
    except Exception as e:
        solver_run.status = "failed"
        solver_run.error_message = str(e)
    finally:
        db.commit()
```

### Phase 4 — Frontend (Week 3)

**Fix TimetableGrid.tsx:**
1. Replace negative period IDs with null + isBreak flag
2. Fix "01:40" → "13:40" in period display
3. Add `spanPeriods` support for merged lab cells
4. Replace `facultyName: string` with `facultyNames: string[]`
5. Add missing slot type colors (IDP, M/H, SL/EL, OE, CRT, QALR)
6. Move faculty legend below grid

**Fix ScheduleSetupWizard.tsx:**
1. Load faculty list from API instead of hardcoded array
2. Load sections from API
3. Remove MINORS/HONORS from CourseAssignmentInput — treat as global sync
4. Add LIBRARY auto-slot (not configurable, auto-applied)
5. Add weekly slots validation (total ≤ 40/week)
6. Resolve faculty names to IDs before API call
7. Add IIC/Agentic Tools as a special slot type
8. Add branch selector (currently only year level is selectable)

**New pages to build:**
```
/dashboard     ← Stats + Version Timeline + ClashSummaryCard + QuickActions
/import        ← Excel upload + ParseProgress + ClashReport table
/configure     ← Tabs: Sections | Faculty | Rooms | Subjects | Assignments
/schedule      ← TimetableGrid + Wizard + SolverProgress + VersionSelector
/export        ← Excel / PDF / JSON download buttons
```

### Phase 5 — CP-SAT Solver (Weeks 3-4)

Build the solver in stages, testing each constraint independently:

```
Stage 1: HC-01 + HC-03 + HC-07 (rooms + sections + breaks)
  → Verify no room clashes and no section clashes

Stage 2: Add HC-04 (subject frequency)
  → Verify each subject appears correct number of times

Stage 3: Add HC-02 (faculty double booking, including co-faculty)
  → Verify no faculty conflicts

Stage 4: Add HC-05 + HC-06 (room capacity + room type)
  → Verify labs only in lab rooms, classrooms only for lectures

Stage 5: Add HC-08 (lab consecutiveness with break guard)
  → Verify all (P) entries are in valid consecutive pairs

Stage 6: Add HC-09 + HC-10 (availability + global sync)
  → Verify M/H slots are globally synchronized

Stage 7: Add soft constraints (SC-01 through SC-10) to objective
  → Minimize gaps, balance load, prefer morning labs
```

**Target metrics for successful solve:**
```
Full ACSE department (42 sections, 2026-27):
  Hard violations: 0
  Soft violation score: < 50
  Generation time: < 5 minutes
  Solver: CP-SAT with 8 workers, 300-second timeout
```

### Phase 6 — Export Engine (Week 4)

Recreate exact VFSTR Excel format:

```python
# backend/parser/excel_exporter.py
def export_to_excel(timetable_version_id: int) -> bytes:
    wb = openpyxl.Workbook()
    
    # Group sections by sheet: II AIML, III AIML, IV AIML, CS, DS, CSBS, IOT, etc.
    for sheet_name, sections in group_by_sheet(timetable_entries):
        ws = wb.create_sheet(title=sheet_name)
        
        for section in sections:
            # Write section header (merged cells, blue background)
            write_section_header(ws, section, row_offset)
            
            # Write period header row (Period 1-8 with break/lunch)
            write_period_headers(ws, row_offset + 1)
            
            # Write 6 day rows
            for day_idx, day in enumerate(DAYS):
                row = row_offset + 2 + day_idx
                ws.cell(row, 1, day)
                for period in PERIODS:
                    entry = get_entry(section, day, period)
                    cell = ws.cell(row, period_to_col(period))
                    if entry:
                        # Format: "DS(P)" in black, room in red below
                        cell.value = f"{entry.subject_code}\n{entry.room_code or ''}"
                        apply_cell_style(cell, entry.entry_type)
            
            # Write faculty legend below grid
            write_faculty_legend(ws, section, row_offset + 10)
            
            row_offset += 25  # next section
    
    return save_workbook_to_bytes(wb)
```

---

## 12. File-by-File Fix List

### Priority 1 (Blocks everything else — fix FIRST)

| File | Problem | Fix |
|------|---------|-----|
| `subject.py` | Single `type` field for L/T/P | Replace with `lecture_hours`, `tutorial_hours`, `lab_hours` |
| `section_subject.py` | Single `total_slots_needed` | Replace with `lecture_slots_needed`, `tutorial_slots_needed`, `lab_slots_needed` + split faculty fields |
| `branch.py` | `year_level` on Branch is wrong | Remove year_level from Branch, add to Section |
| `section.py` | Missing `year_level` | Add `year_level` (moved from Branch) |

### Priority 2 (Schema correctness)

| File | Problem | Fix |
|------|---------|-----|
| `room.py` | `floor = default=6` wrong, `type` is reserved word | `floor → String`, rename to `room_type`, add `gpu_capable` |
| `timetable.py` | `solver_run_id` missing FK | Add `ForeignKey("solver_runs.id")` |
| `time_slot.py` | No unique constraint, `period` nullable without purpose | Add UniqueConstraint, add `slot_label` |
| `faculty.py` | `availability` JSON undocumented | Add docstring/comment with exact format |

### Priority 3 (Nice to have)

| File | Problem | Fix |
|------|---------|-----|
| `base.py` | `datetime.utcnow` deprecated | Switch to `datetime.now(timezone.utc)` |
| `department.py` | `head_faculty_id` not FK | Add `ForeignKey("faculty.id")` |
| `academic_year.py` | No `label` or `is_current` | Add both fields |
| `solver_run.py` | No `error_message` field | Add Text column for failure details |

### Frontend Fixes

| File | Problem | Priority |
|------|---------|----------|
| `TimetableGrid.tsx` | Negative period IDs | HIGH |
| `TimetableGrid.tsx` | Single `facultyName` for multi-faculty labs | HIGH |
| `TimetableGrid.tsx` | No lab span support (merged cells) | HIGH |
| `TimetableGrid.tsx` | Missing slot type colors | MEDIUM |
| `ScheduleSetupWizard.tsx` | Hardcoded faculty/sections | HIGH |
| `ScheduleSetupWizard.tsx` | MINORS/HONORS as regular P subject | HIGH |
| `ScheduleSetupWizard.tsx` | No LIBRARY auto-slot | MEDIUM |
| `ScheduleSetupWizard.tsx` | No branch selector | MEDIUM |
| `ScheduleSetupWizard.tsx` | `faculty_name` string instead of ID | HIGH |

---

## Appendix A — The Complete Real Section-Subject-Faculty Matrix

From actual screenshots (II AIML only — same pattern repeats for all 12 sections):

```
Section │ SFCDS-L  │ DMS-L            │ DS-L                  │ AI-L
────────┼──────────┼──────────────────┼───────────────────────┼──────────────────
II-A    │ P.Kalpana│ Ankamma Rao M.   │ Srikantha Reddy       │ B.Sudha Rani
II-B    │ Guravaiah│ N.Bhargavi       │ Bharadwaja Chepuri    │ G.Kalaiarasi
II-C    │ Rushi P. │ Manigandan A     │ Srikantha Reddy       │ P.Giri Prasad
II-D    │ BN Naveen│ Imtiyaz Bhatt    │ Bharadwaja Chepuri    │ D.Urlamma
II-E    │ Rushi P. │ Imtiyaz Bhatt    │ Srikantha Reddy       │ B.Sudha Rani
II-F    │ P.Kalpana│ N.Bhargavi       │ Bharadwaja Chepuri    │ D.Urlamma
II-G    │ Guravaiah│ Manigandan A     │ Bharadwaja Chepuri    │ G.Kalaiarasi
II-H    │ BN Naveen│ Ankamma Rao M.   │ PLN Manoj Kumar       │ B.Sudha Rani
II-I    │ BN Naveen│ Imtiyaz Bhatt    │ PLN Manoj Kumar       │ P.Giri Prasad
II-J    │ Rushi P. │ Manigandan A     │ Srikantha Reddy       │ G.Kalaiarasi
II-K    │ Guravaiah│ N.Bhargavi       │ Narra Bhagyalakshmi   │ D.Urlamma
II-L    │ P.Kalpana│ Ankamma Rao M.   │ PLN Manoj Kumar       │ P.Giri Prasad
```

---

## Appendix B — Known Issues from V5 Data

1. **II AIML-K: DS taught by Ms. Narra Bhagyalakshmi alone** — This section has only 1 co-faculty for DS(P), while other sections have 3-4. Possible understaffing.

2. **IV AIML-B: `AFTF-12(U-BLOCK LOCK)`** — Room marked as locked in coordinator note. Solver must treat this room as UNAVAILABLE during that slot.

3. **IV AIML-D: `UFTF-13` room code** — "UFTF" instead of "AFTF" may be a typo. Parser must normalize this.

4. **IV AIML-D: `CAL/AL/P-Block First Floor: skruthi Seminar`** — External venue reference in a cell. Parser should store as `raw_room_text` and mark `room_id=NULL`.

5. **II AIML-B: Lunch shows `12:40-1:30`** — Most sections show `12:40-1:40`. This is a typo in the Excel template. Parser must normalize.

6. **III AIML-G: `SL/EL/AL/IL`** — Four-variant self-study code not seen in other sections. Normalize to `SL_EL`.

7. **III BS(DS): `QALR` uses `AFF-10`** — QALR is normally a theory lecture in classrooms, but BS(DS) section uses a project room. This may be due to small batch size.

8. **I BS(DS), I MSC(DS), I MTECH(DS)**: All three are AY 2025-26 templates that are completely EMPTY (no slots filled). The solver should skip these sections entirely.

---

## Summary: What to Build in What Order

```
WEEK 1  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Day 1-2: Fix all 12 model files using corrections in Section 12
Day 3:   Run Alembic migrations, create seed data scripts
Day 4:   Build Excel parser (handle all 10 sheet types)
Day 5:   Build standalone conflict checker, run V5 baseline test
         → GATE: parser returns 42 sections, checker returns 51 room clashes

WEEK 2  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Day 1-2: FastAPI routes (health, sections, faculty, rooms, timetable)
Day 3:   Excel import API + WebSocket setup + Celery
Day 4:   Docker Compose (postgres, redis, backend, celery)
Day 5:   Integration test: import V5 → API returns 51 clashes
         → GATE: `make validate` shows 51 room clashes from API

WEEK 3  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Day 1-2: Fix TimetableGrid.tsx (5 issues listed in Section 8)
Day 2-3: Fix ScheduleSetupWizard.tsx (8 issues listed in Section 8)
Day 4-5: Build remaining 5 pages (dashboard, import, configure, schedule, export)

WEEK 4  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Day 1-2: CP-SAT solver HC-01 through HC-10 (in stages from Section 11)
Day 3:   Soft constraint objective function (SC-01 through SC-10)
Day 4:   Excel exporter (recreate VFSTR format exactly)
Day 5:   End-to-end test: import V5 → solve → export V6 → V6 has 0 clashes
         → GATE: V6 Excel has 0 room clashes and 0 faculty clashes
```

---

*Document compiled from: 46 real timetable screenshots (all sections), 12 SQLAlchemy model files,  
2 React frontend components, official VFSTR campus documentation, AICTE norms.*  
*Author: Analysis by Balaji Rao Konda | VFSTR ACSE Timetable Scheduler Project*
