<div align="center">

# 🎓 VFSTR ACSE Automated Timetable Scheduler

### Enterprise-Grade Constraint Optimization & Autonomous Multi-Agent Scheduling Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![OR-Tools](https://img.shields.io/badge/Google%20OR--Tools-CP--SAT-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://developers.google.com/optimization)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)
[![Celery](https://img.shields.io/badge/Celery-5.4-37814A?style=for-the-badge&logo=celery&logoColor=white)](https://docs.celeryq.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)

<p align="center">
  <b>Built for Vignan's Foundation for Science, Technology & Research (VFSTR)</b><br>
  <i>Department of Applied Computer Science & Engineering (ACSE) · Vadlamudi, Guntur District, AP, India</i>
</p>

[The Problem in Depth](#-the-problem-in-depth) •
[Mathematical & Algorithmic Methods](#-mathematical--algorithmic-methods) •
[Autonomous Multi-Agent Architecture](#-autonomous-multi-agent-architecture) •
[Full Feature Index & Pages](#-full-feature-index--pages-in-depth) •
[Institutional Rules & Constraints](#-institutional-rules--constraints-specification) •
[System Architecture](#-system-architecture) •
[Quick Start](#-quick-start--installation) •
[API Reference](#-complete-api-reference)

</div>

---

## 📌 The Problem in Depth

### Background & Scale of the ACSE Department
Vignan's Foundation for Science, Technology & Research (VFSTR) operates one of the largest engineering faculties in Andhra Pradesh. The Department of Applied Computer Science & Engineering (ACSE) comprises:
* **44 to 60 Academic Sections** across 2nd, 3rd, and 4th years, spanning multiple specialized branches: Artificial Intelligence & Machine Learning (`AIML`), Computer Science (`CS`), Data Science (`DS`), Computer Science & Business Systems (`CSBS`), and Internet of Things (`IOT`).
* **~2,360+ Full-Time Students** requiring synchronized lecture, tutorial, practical lab, and self-directed study sessions.
* **~80 to 160 Faculty Members** with varying academic ranks (Professors, Associate Professors, Assistant Professors) governed by strict institutional teaching workload caps.
* **35 Physical Venues** consisting of traditional lecture halls, standard computer laboratories, and specialized high-capacity NVIDIA GPU labs (`AFTF-12`, `AFTF-13`, `AFTF-14`).
* **48 Weekly Time Slots** per section: 6 instructional days (Monday through Saturday) with 8 distinct periods per day (P1 through P8), punctuated by mandatory morning breaks and lunch intervals.

### The Breakdown of Manual Scheduling
Historically, departmental scheduling was conducted entirely through manual entry across multi-sheet Microsoft Excel workbooks. Due to the high combinatorial complexity ($35 \text{ rooms} \times 48 \text{ slots} \times 80 \text{ faculty} \times 44 \text{ sections} \approx 5.9 \times 10^6 \text{ possibilities}$), manual coordination collapsed under scale. 

Between July 10 and July 15, 2026, the department went through **5 emergency revisions in 5 days**:

| Version | Date Released | Total Slots | Primary Changes & Problems Caused | Room Clashes | Faculty Clashes |
|---|---|---|---|:---:|:---:|
| **V1** | 10-Jul-2026 | 894 | Initial manual schedule draft. Numerous unallocated lab hours. | 82 | 14 |
| **V2** | 11-Jul-2026 | ~900 | Minor slot movements to mitigate teacher overlap. Cascaded clashes to other sections. | 71 | 9 |
| **V3** | 13-Jul-2026 | 950 | Large-scale manual room reassignments to address lab constraints. | 64 | 4 |
| **V4** | 14-Jul-2026 | 980 | Faculty teaching hours rebalanced. Broken break protections and lab continuity. | 59 | 2 |
| **V5 (Baseline)** | 15-Jul-2026 | **1,000** | Added centralized `MINORHONORS` cohort sheet. **Current baseline workbook.** | **51** | **0** |

### Why Manual Methods Failed
1. **Hidden Room Clashing**: In Version 5, human coordinators successfully eliminated faculty clashes (0 clashes), but in doing so, accidentally scheduled two sections in the exact same room at the same time in **51 distinct slots**.
2. **Cascading Ripple Effects**: Moving one 3-period lab block to resolve a venue conflict required adjusting 3 separate slots, which in turn forced instructor swaps across up to 4 other sections.
3. **Rigid Cohort Lockouts**: University regulations mandate that `MINORS/HONORS` classes for 3rd-year students must happen simultaneously across all branches on **Wednesday P7–P8 and Thursday P7–P8**. Coordinating 18 sections into compatible venues for that shared time slot proved nearly impossible by hand.
4. **4th Year Industrial Block Constraints**: 4th-year students participate in self-learning and experiential learning (`SL/EL`), requiring **P1–P2 (08:15–09:55) Monday through Saturday** and **Saturday afternoon (P6–P8)** to be reserved without traditional classroom lectures.
5. **Multi-Period Lab Continuity**: Computer science practicals cannot be scheduled in fragmented 1-hour chunks; they require 2 or 3 contiguous periods that must never straddle the morning break (between P2 and P3) or the lunch hour (between P5 and P6).

---

## 🔬 Mathematical & Algorithmic Methods

To guarantee 100% clash-free schedules, the platform replaces guesswork with rigorous mathematical optimization and algorithmic verification.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        Mathematical Solver Suite                         │
├──────────────────────────┬───────────────────────┬───────────────────────┤
│    Google OR-Tools       │  Single-Pass Hash     │  ScheduleIndexStore   │
│    CP-SAT Formulation    │  ConflictChecker      │  O(1) Swap Validator  │
├──────────────────────────┼───────────────────────┼───────────────────────┤
│  • Integer Programming   │  • Multi-bucket index │  • Inverted temporal  │
│  • Domain reduction      │  • Identity keying    │    hash map           │
│  • Global constraints    │  • O(N) linear time   │  • Sub-5ms validation │
│  • Penalty minimization  │  • Joint transparency │  • Drag-and-drop gate │
└──────────────────────────┴───────────────────────┴───────────────────────┘
```

### 1. Google OR-Tools CP-SAT Formulation
The core scheduling engine leverages **Google OR-Tools CP-SAT**, an industrial constraint programming solver utilizing satisfiability (SAT) techniques over finite integer domains.

#### Decision Variables
Let:
* $\mathcal{S}$ be the set of sections ($\approx 44$).
* $\mathcal{C}$ be the set of curriculum subjects / courses.
* $\mathcal{R}$ be the set of physical and virtual rooms ($\approx 35$).
* $\mathcal{T}$ be the set of weekly time slots ($6 \text{ days} \times 8 \text{ periods} = 48$).
* $\mathcal{F}$ be the set of faculty members ($\approx 80$).

We define the binary decision variable:
$$x_{s, c, r, t} \in \{0, 1\}$$
where $x_{s, c, r, t} = 1$ if section $s$ takes subject $c$ in room $r$ at time slot $t$, and $0$ otherwise.

#### Hard Constraints as Mathematical Assertions
* **Room Non-Overlapping (HC-01)**: For every physical room $r \in \mathcal{R}_{\text{physical}}$ and every time slot $t \in \mathcal{T}$:
  $$\sum_{s \in \mathcal{S}} \sum_{c \in \mathcal{C}} x_{s, c, r, t} \le 1$$
* **Faculty Non-Double-Booking (HC-02)**: Let $\mathcal{C}_f \subseteq \mathcal{C}$ be the subjects instructed by faculty $f \in \mathcal{F}$. For every time slot $t \in \mathcal{T}$:
  $$\sum_{s \in \mathcal{S}} \sum_{c \in \mathcal{C}_f} \sum_{r \in \mathcal{R}} x_{s, c, r, t} \le 1$$
* **Section Cohort Exclusivity (HC-03)**: For every section $s \in \mathcal{S}$ and time slot $t \in \mathcal{T}$:
  $$\sum_{c \in \mathcal{C}} \sum_{r \in \mathcal{R}} x_{s, c, r, t} \le 1$$
* **Curriculum Hours Satisfaction (HC-04)**: For every section $s \in \mathcal{S}$ and subject $c \in \mathcal{C}$ requiring $H_{s,c}$ weekly periods:
  $$\sum_{r \in \mathcal{R}} \sum_{t \in \mathcal{T}} x_{s, c, r, t} = H_{s,c}$$
* **Break / Lunch Inviolability (HC-07 & HC-08)**:
  Lab sessions of length $L \in \{2, 3\}$ starting at period $p$ must satisfy $p \notin \{2, 5\}$, guaranteeing that no practical extends across the morning break ($09:55\text{--}10:10$) or lunch ($12:40\text{--}13:40$).

#### Objective Function (Soft Constraint Optimization)
The solver minimizes a weighted penalty function across all soft constraints:
$$\min \sum_{k=1}^{10} w_k \cdot \text{Violation}_k$$
where penalty weights $w_k$ prioritize faculty preferences ($w=50$), inter-building transit minimization ($w=30$), and GPU lab allocations for AI courses ($w=20$).

---

### 2. Single-Pass $O(N)$ ConflictChecker
Located in `backend/solver/conflict_checker.py`, this standalone clash detector processes thousands of slots in **under 15 milliseconds** without requiring database connections or heavy ORM overhead.
* **Multi-Bucket Spatial Indexing**: Partitions allocations into three hash buckets: `(day, period, room) \to \text{entries}`, `(day, period, faculty) \to \text{entries}`, and `(day, period, section) \to \text{entries}`.
* **Fuzzy Identity Normalization**: Collapses variations in names (e.g., `"Dr. S. Srikantha Reddy"`, `"Dr.S.Srikantha Reddy"`, `"DR. S. SRIKANTHA REDDY"`, `"S. Srikantha Reddy"`) to an invariant hash key.
* **Joint-Section Transparency**: Sections that legitimately share an auditorium or lecture venue (such as `CSBS` and `IOT` combined electives) are recognized as co-taught groups rather than flagged as false collisions.
* **Virtual Room Exclusion**: Virtual markers (`LIBRARY`, `BREAK`, `LUNCH`, `SL/EL`, `ONLINE`, `MINORS/HONORS`) are excluded from physical venue occupancy checks.

---

### 3. ScheduleIndexStore: $O(1)$ Incremental Validator
Located in `backend/solver/incremental_validator.py`, this engine powers the real-time interactive timetable UI.
* When a coordinator drags and drops a class cell from **Tuesday P2** to **Thursday P4**, running a full CP-SAT model is impractical.
* `ScheduleIndexStore` builds an in-memory inverted hash map:
  $$\text{Index}: (\text{Day}, \text{Period}) \times (\text{EntityID}) \to \text{SlotAllocation}$$
* Swap feasibility is evaluated in $O(1)$ time by querying whether the destination venue, teacher, or student section is occupied. Responses return in **$< 5\text{ms}$**, allowing immediate visual green/red feedback in the web browser.

---

### 4. Evolutionary Genetic Algorithm (GA)
Located in `backend/solver/genetic_algorithm.py`:
* **Chromosome Representation**: An integer array mapping each required class session to an assigned `(Room, Day, Period)` tuple.
* **Fitness Evaluation**: Evaluates chromosomes against all 13 hard constraints and 10 soft constraints using high-speed vectorized checks.
* **Genetic Operators**:
  - *Tournament Selection*: Selects parent candidates with a tournament size of 5.
  - *Two-Point Crossover*: Recombines schedules while preserving lab continuity blocks.
  - *Adaptive Mutation Rate*: Starts at $5\%$ and automatically scales up if population diversity drops.
  - *Elitism*: Preserves the top 10 fittest chromosomes untouched across generations.

---

## 🤖 Autonomous Multi-Agent Architecture

Beyond raw constraint solving, the platform features a multi-agent cooperative architecture located in `backend/app/services/multi_agent_scheduler.py` and `backend/app/services/exam_scheduler_agent.py`.

```
                        ┌──────────────────────────────┐
                        │   Schedule Change Proposal   │
                        └──────────────┬───────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            │                          │                          │
            ▼                          ▼                          ▼
┌───────────────────────┐  ┌───────────────────────┐  ┌───────────────────────┐
│ SectionCurriculum     │  │ FacultyWorkload       │  │ RoomCompatibility     │
│ Agent                 │  │ Agent                 │  │ Agent                 │
│ • Weekly Quotas       │  │ • Max Rank Hours      │  │ • Room Type Matching  │
│ • Library/IIC Rules   │  │ • Fatigue Limits      │  │ • Capacity Checks     │
│ • Cohort Lockouts     │  │ • Daily 5h Max        │  │ • GPU Lab Priority    │
└───────────┬───────────┘  └───────────┬───────────┘  └───────────┬───────────┘
            │                          │                          │
            └──────────────────────────┼──────────────────────────┘
                                       │
                                       ▼
                        ┌──────────────────────────────┐
                        │ HardConstraintAgent          │
                        │ • HC-01..HC-03 & Break Check │
                        │ • ABSOLUTE VETO POWER        │
                        └──────────────┬───────────────┘
                                       │
                                       ▼
                        ┌──────────────────────────────┐
                        │   3-Role Consensus Engine    │
                        │   ≥ 75% Approval + 0 Vetoes  │
                        └──────────────┬───────────────┘
                                       │
                   ┌───────────────────┴───────────────────┐
                   ▼                                       ▼
           [ COMMIT / PUBLISH ]                 [ MULTI-CYCLE REPAIR ]
           Safe to Persist to DB                Re-route via Substitute/Room
```

### The 4 Specialized Audit Agents

#### 1. `SectionCurriculumAgent`
* **Focus**: Educational fidelity and syllabus adherence.
* **Rules**: Ensures 2nd-year sections receive exactly 36 teaching hours, 1 Library hour, and 1 IIC hour. Verifies that 3rd-year sections receive 45 hours and 4th-year sections receive 39 hours.
* **Veto Power**: Enforces a **Hard Veto** if a proposed timetable causes a section quota deviation $\ge 5$ hours.

#### 2. `FacultyWorkloadAgent`
* **Focus**: Human factors, instructor fatigue, and institutional compliance.
* **Rules**: Restricts weekly teaching hours based on academic designation:
  - *Professor*: Max 12 hours/week.
  - *Associate Professor*: Max 14 hours/week.
  - *Assistant Professor*: Max 16 hours/week.
* Enforces the **5-hour daily teaching cap** and flags consecutive teaching blocks $> 3$ hours as high-fatigue risks.

#### 3. `RoomCompatibilityAgent`
* **Focus**: Physical campus infrastructure and technological requirements.
* **Rules**: Ensures that practical lab courses (`(P)`, `LAB`) are never placed in standard classrooms. Verifies student headcount against room capacity.
* **GPU Lab Priority**: Prioritizes GPU laboratories (`AFTF-12`, `AFTF-13`, `AFTF-14`) specifically for Deep Learning (`DL`), Computer Vision (`CV`), and MLOps (`MLOP`).

#### 4. `HardConstraintAgent`
* **Focus**: Zero-tolerance integrity gating.
* **Rules**: Evaluates every proposed timetable mutation against HC-01 (room overlap), HC-02 (teacher overlap), HC-03 (section overlap), and HC-07 (break violations).
* **VETO Power**: Holds **absolute veto authority**. If any hard collision is detected, the timetable cannot be published under any circumstances.

---

### Consensus Approval Protocol & Multi-Cycle Repair Loop
* Every timetable generated by the solver or modified by an administrator must pass through the **Consensus Protocol**.
* The 4 agents cast formal typed votes (`APPROVE` or `REJECT`) accompanied by critique objects detailing rule IDs, severity ratings, and affected slots.
* **Publication Threshold**: A timetable is only committed if it receives at least a **$75\%$ supermajority ($3/4$ votes)** and **zero hard vetoes**.
* If rejected, the system enters an **Autonomous Multi-Cycle Repair Loop**, iteratively applying localized repair heuristics to reroute conflicting rooms or substitute faculty until consensus is reached.

---

### Campus Disruption Simulator
Located in `backend/app/services/mission_simulator.py`, this module allows administrators to stress-test timetable resilience against real-world emergencies:
1. `room_failure`: An academic hall or computer lab suffers an emergency power outage or equipment failure. The agent automatically evacuates all scheduled classes and relocates them to vacant venues.
2. `gpu_lab_failure`: An outage occurs in `AFTF-12/13/14`. The agent prioritizes high-credit AI/ML courses while temporarily rerouting standard programming labs to regular computer labs.
3. `faculty_absence`: An instructor calls in sick on short notice. The agent triggers the **Substitute Instructor Dispatcher** to identify qualified, non-clashing colleagues with low fatigue scores.
4. `capacity_surge`: Student enrollment in an elective surges beyond room capacity. The agent swaps the class into a larger lecture hall.
5. `priority_reroute`: Department leadership requires an urgent cohort assembly, locking specific periods.

---

### Autonomous Examination Timetabling Agent
Located in `backend/app/services/exam_scheduler_agent.py`, this engine automates mid-term and end-semester examination timetabling:
* **EC-01 (Single Exam Cap)**: No student cohort may sit for more than one exam on any single calendar day.
* **EC-02 (Session Splits)**: Strict segregation between Morning ($09:30\text{--}12:30$) and Afternoon ($14:00\text{--}17:00$) sessions.
* **EC-03 (Anti-Cheating Seating Space)**: Enforces an automatic **$50\%$ room capacity factor** (e.g., a 60-seat hall accommodates a maximum of 30 examinees) to ensure alternate-seat distancing.
* **EC-04 (Invigilation Balancing)**: Distributes exam supervision duties evenly across all available departmental faculty.
* **EC-05 (Conflict of Interest Guard)**: Strictly prohibits faculty members from invigilating exams for courses they teach.

---

## 🖥️ Full Feature Index & Pages (In Depth)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         Full-Stack Web Interface                        │
├──────────────────┬──────────────────┬──────────────────┬─────────────────┤
│  Dashboard (/)   │ Schedule Viewer  │ Agent Console    │ Setup Wizard    │
│  • KPI Metrics   │ (/schedule)      │ (/agent)         │ (/ai-scheduler) │
│  • Clash Alerts  │ • 6x8 Grid       │ • Disruption Sim │ • 3-Step Flow   │
│  • Version Cards │ • Drag & Drop    │ • Consensus UI   │ • Seed Caching  │
├──────────────────┼──────────────────┼──────────────────┼─────────────────┤
│ Master Configure │ Export Hub       │ Testing Lab      │ System Settings │
│ (/configure)     │ (/export)        │ (/testing)       │ (/settings)     │
│ • 5 CRUD Tabs    │ • Excel, PDF, ZIP│ • Benchmarking   │ • Telemetry     │
│ • Workload Bars  │ • iCal & Displays│ • Dataset Switch │ • DB Monitors   │
└──────────────────┴──────────────────┴──────────────────┴─────────────────┘
```

### 1. Dashboard (`/`)
* **Real-Time KPIs**: Live counters for total academic sections, active faculty members, venues, and weekly scheduled teaching slots.
* **Clash Summary Card**: Prominent color-coded health card displaying active hard violations (highlighting the 51 baseline clashes in Version 5).
* **Version Evolution Timeline**: Interactive horizontal timeline displaying Version 1 through Version 5, tracking the historical reduction in timetable errors.
* **Building Block Analytics**: Visual bar charts and heatmaps illustrating venue occupancy rates across campus blocks (Block-VI, U-Block, A-Block).

### 2. Timetable Grid & Schedule Workspace (`/schedule`)
* **Interactive 6×8 Matrix**: View Monday through Saturday schedules across 8 periods with clearly delineated break and lunch rows.
* **Anatomy of a Slot Cell**: Each grid cell displays the course code, venue code, assigned faculty name, and a color badge indicating slot type (Lecture: Blue, Lab: Purple, Tutorial: Green, Library: Amber, Conflict: Red).
* **Drag-and-Drop Move Validation**: Coordinators can drag classes across periods; the `ScheduleIndexStore` validates the move in $< 5\text{ms}$ and warns of any room or instructor collisions before saving.
* **Continuous Multi-Period Lab Merging**: Lab sessions running across 2 or 3 consecutive periods visually merge into unified wide cells.
* **Perspective Switching**: Toggle views instantly between **Section Schedule**, **Faculty Schedule**, **Venue Availability**, and **Cohort Overview**.

### 3. Master Data Configuration Panel (`/configure`)
Five comprehensive management tabs backed by `ConfigureService`:
1. **Faculty Tab**: Searchable roster with real-time weekly workload progress bars (Current Hours / Maximum Rank Cap) and CSV bulk import.
2. **Rooms Tab**: Venue database categorizing physical classrooms, computer labs, GPU labs, and project rooms with seating capacities.
3. **Subjects Tab**: Curriculum registry tracking course titles, subject codes, L/T/P credit breakdowns, and laboratory venue requirements.
4. **Sections Tab**: Academic sections organized by year level (2nd, 3rd, 4th Year) and branch (`AIML`, `CS`, `DS`, `CSBS`, `IOT`).
5. **Assignments Tab**: Section-subject mapping matrix assigning lead lecturers, tutorial assistants, and laboratory co-instructors.

### 4. Guided AI Scheduler Wizard (`/ai-scheduler`)
* Multi-step guided creation flow allowing academic coordinators to configure and generate a completely new semester timetable from scratch.
* In-memory seed caching automatically suggests faculty assignments and room allocations based on departmental historical preferences.
* Real-time solver preview renders the generated CP-SAT schedule directly in the browser upon completion.

### 5. Multi-Format Enterprise Export Hub (`/export`)
* **Institutional Excel (.xlsx)**: Generates workbooks mirroring official VFSTR formatting, complete with separate worksheet tabs for each section, cell styling, faculty legends, and merged lab cells.
* **Printable A4 PDFs**: Generates high-resolution, printable PDF timetables formatted specifically for student notice boards.
* **Department Consolidated Booklet**: Compiles all 44+ section timetables into a single, indexed PDF document for the Head of Department.
* **Streaming ZIP Bundle**: Bundles individual PDFs for all sections into an on-the-fly downloadable `.zip` archive.
* **iCalendar (.ics) Feeds**: Standard calendar files enabling faculty to subscribe to their weekly timetable in Google Calendar or Outlook.
* **SmartClassroom Digital Sync**: Direct POST integration transmitting schedule metadata to electronic lecterns and classroom display panels.

### 6. Autonomous Agent Console (`/agent`)
* Live WebSocket connection tracking autonomous agent reasoning and multi-agent consensus voting.
* Mission simulator interface to trigger emergency room shutdowns or instructor absences and observe real-time rerouting.
* Substitute instructor finder recommending available colleagues with matching subject competencies and low fatigue scores.

### 7. Testing Lab & Validation Arena (`/testing`)
* Test sandbox allowing developers and coordinators to benchmark solver performance against multiple test datasets (`v5_baseline`, `4th_year`, `multi_branch_e2e`).
* Real-time constraint evaluation displaying compliance badges for every individual academic section.

### 8. System Settings & DevOps Telemetry (`/settings`)
* Real-time host telemetry reporting CPU utilization, memory consumption, active thread counts, and container uptimes.
* PostgreSQL database diagnostics monitoring active connection pool limits, WAL checkpoint statuses, and transaction health.

---

## 📜 Institutional Rules & Constraints Specification

### 1. Weekly Schedule & Period Timings
Instruction runs across a 6-day academic week (Monday through Saturday):

| Period | Time Window | Duration | Description |
|---|:---:|:---:|---|
| **P1** | 08:15 – 09:05 | 50 mins | Morning Period 1 |
| **P2** | 09:05 – 09:55 | 50 mins | Morning Period 2 |
| **BREAK** | **09:55 – 10:10** | **15 mins** | **Mandatory Morning Tea Break (Inviolable)** |
| **P3** | 10:10 – 11:00 | 50 mins | Mid-Morning Period 3 |
| **P4** | 11:00 – 11:50 | 50 mins | Mid-Morning Period 4 |
| **P5** | 11:50 – 12:40 | 50 mins | Mid-Morning Period 5 |
| **LUNCH** | **12:40 – 13:40** | **60 mins** | **Departmental Lunch Interval (Inviolable)** |
| **P6** | 13:40 – 14:30 | 50 mins | Afternoon Period 6 |
| **P7** | 14:30 – 15:20 | 50 mins | Afternoon Period 7 |
| **P8** | 15:20 – 16:05 | 45 mins | Afternoon Period 8 |

---

### 2. Hard Constraints (HC) — Zero Tolerance (100% Enforced)
Any timetable violating a Hard Constraint is classified as invalid and cannot be published:

| ID | Constraint Name | Mathematical / Operational Rule | Relaxation Policy |
|---|---|---|---|
| **HC-01** | Room Conflict | No physical room may be assigned to $> 1$ class in the same slot. | **NEVER RELAX** |
| **HC-02** | Faculty Conflict | No faculty member may teach $> 1$ section in the same slot. | **NEVER RELAX** |
| **HC-03** | Section Conflict | No student section may have $> 1$ course in the same slot. | **NEVER RELAX** |
| **HC-04** | Subject Quota | Total weekly hours for lectures, tutorials, and labs must match syllabus. | **NEVER RELAX** |
| **HC-05** | Venue Capacity | Student strength must not exceed room seating capacity. | Last Resort Only |
| **HC-06** | Venue Type Match | Lab courses must be placed in computer/GPU labs, never lecture halls. | Last Resort Only |
| **HC-07** | Break Guard | Teaching sessions cannot be scheduled during Break (09:55) or Lunch (12:40). | **NEVER RELAX** |
| **HC-08** | Lab Consecutiveness | Labs must occupy contiguous periods starting only at P1, P3, P4, P6, or P7. | Relax 3h to 2h if room deficit |
| **HC-09** | Faculty Daily Cap | Faculty teaching hours cannot exceed 5 hours on any single day. | Soft warning threshold |
| **HC-10** | Continuous Limit | Faculty cannot teach $> 3$ consecutive hours without a 50-minute break. | Soft warning threshold |
| **HC-11** | Rank Workload Cap | Professor: $\le 12$h · Assoc. Professor: $\le 14$h · Asst. Professor: $\le 16$h. | Strict ceiling |
| **HC-12** | Self-Directed Slots| 2nd Year: 1 Library + 1 IIC hour. 3rd and 4th Year: 0 Library hours. | Strict quota |
| **HC-13** | Protected Blocks | Minors/Honors locked to WED/THU P7–P8; 4th Year SL/EL locked to MON–SAT P1–P2. | **NEVER RELAX** |

---

### 3. Soft Constraints (SC) — Optimized Penalty Weights
Soft constraints represent institutional preferences and pedagogical quality metrics:

| ID | Constraint Name | Default Penalty | Optimization Objective |
|---|---|:---:|---|
| **SC-01** | Teaching Slot Preference | 50 | Align senior faculty with preferred morning or afternoon slots. |
| **SC-02** | Inter-Building Transit | 30 | Minimize faculty travel between distant building blocks (Block-VI vs. U-Block). |
| **SC-03** | Curriculum Distribution | 10 | Spread core theory subjects evenly across Monday through Saturday. |
| **SC-04** | Gap Elimination | 5 | Avoid isolated 1-hour gaps in student section schedules. |
| **SC-05** | GPU Lab Allocation | 20 | Ensure AI, Deep Learning, and Vision classes receive GPU labs (`AFTF-12/13/14`). |
| **SC-06** | Workload Balance | 5 | Balance daily class distributions to prevent mid-week student fatigue. |
| **SC-07** | Joint Section Placement | 100 | Place co-taught elective sections in high-capacity shared seminar halls. |
| **SC-08** | Room Stability | 15 | Minimize room switching for a student section throughout the same day. |

---

## 🏗️ System Architecture

The application implements a strict zero-trust, decoupled layered architecture:

```
[ Frontend Client ]
        │
        ▼ (Port 80)
[ Nginx Reverse Proxy ]
  ├── Rate Limiting (600 req/min general, 120 req/min solver)
  ├── Gzip Level 6 Compression
  ├── WebSocket Upgrade Gateway
  └── Static Asset Caching
        │
        ▼ (Internal Port 8000)
[ FastAPI ASGI Application ]
  ├── API v1 Router (17 specialized route modules)
  ├── Pydantic v2 Validation
  ├── JWT Auth & RFC 7807 Error Formatting
  └── Service Layer (23 decoupled business logic modules)
        │
        ├──► [ Google OR-Tools CP-SAT Solver ]
        ├──► [ Evolutionary Genetic Algorithm ]
        ├──► [ Multi-Agent Consensus & Simulator ]
        │
        ▼
[ Data & Worker Layer ]
  ├── PostgreSQL 16 (Relational models, asyncpg connection pooling)
  ├── Redis 7 (In-memory broker, session cache, pub/sub)
  └── Celery Workers (Prefork async background task processing)
```

---

## 🚀 Quick Start & Installation

### Prerequisites
* **Docker & Docker Compose** (Recommended): Docker Engine $\ge 24.0$, Docker Compose $\ge 2.20$.
* **Or Local Toolchains**:
  - Python $\ge 3.11$
  - Node.js $\ge 20$ LTS & npm $\ge 10$
  - PostgreSQL $\ge 16$
  - Redis $\ge 7$

---

### Method A: One-Command Docker Setup (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/9046balaji/Time-Table.git
cd Time-Table

# 2. Configure environment variables
cp .env.example .env

# 3. Launch the containerized stack
docker compose up -d

# 4. Initialize database and verify baseline data
docker exec -it vfstr_backend python -m app.services.seed_service
```

Once running, access the web services:
* **Web Application UI**: `http://localhost`
* **Interactive API Documentation (Swagger)**: `http://localhost/docs`
* **Alternative API Documentation (ReDoc)**: `http://localhost/redoc`

---

### Method B: Manual Local Development

#### 1. Backend Setup
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt

# Start backend development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. Celery Worker (Separate Terminal)
```bash
cd backend
# Windows
celery -A tasks.celery_app worker --loglevel=info --pool=solo
# Linux / macOS
celery -A tasks.celery_app worker --loglevel=info --concurrency=2
```

#### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
# Accessible at http://localhost:3000
```

---

## 📡 Complete API Reference

All backend endpoints are prefixed with `/api/v1`.

### 1. Timetable Operations (`/api/v1/timetable`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/timetable` | Retrieve weekly schedule entries with optional version and section filters. |
| `GET` | `/timetable/versions` | List all historical and solver-generated timetable versions. |
| `GET` | `/timetable/version/{version_id}` | Retrieve complete timetable records for a specific version. |
| `GET` | `/timetable/faculty/{faculty_id}` | Retrieve personal weekly teaching schedule for a faculty member. |
| `GET` | `/timetable/room/{room_code}` | Retrieve room occupancy and schedule for a specific venue. |
| `POST` | `/timetable/validate-move` | Perform sub-5ms $O(1)$ incremental validation on a proposed slot drag-and-drop. |
| `POST` | `/timetable/update-slot` | Persist manual slot changes with transactional conflict verification. |
| `DELETE`| `/timetable/slot/{entry_id}` | Safely delete a slot and remove associated faculty junction records. |
| `POST` | `/timetable/sync-master` | Synchronize schedule metadata to SmartClassroom electronic lecterns. |

---

### 2. Constraint Validation (`/api/v1/validate`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/validate/report` | Run comprehensive validation on the active timetable, reporting room and teacher clashes. |
| `GET` | `/validate/{version_id}` | Run complete constraint verification against a specific historical version ID. |

---

### 3. Solver Operations (`/api/v1/solve` & `/api/v1/wizard`)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/solve` | Launch asynchronous CP-SAT solver job via Celery worker queue. |
| `GET` | `/solve/{run_id}/stream` | WebSocket stream providing real-time solver iterations and solution fitness. |
| `POST` | `/solve/generate-from-wizard` | Solve and generate a clash-free timetable directly from wizard-derived requirements. |
| `POST` | `/wizard/generate-from-wizard` | Direct route alias for guided wizard generation. |

---

### 4. Autonomous Agent & Simulations (`/api/v1/agent`)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/agent/sessions` | Initialize an autonomous agent session with specified repair goals. |
| `GET` | `/agent/sessions/{id}` | Fetch current state, active decision trace, and critique history of an agent session. |
| `POST` | `/agent/sessions/{id}/consensus`| Trigger multi-agent consensus voting across curriculum, workload, and venue agents. |
| `POST` | `/agent/simulate/{scenario}` | Trigger campus disruption simulations (`room_failure`, `gpu_lab_failure`, etc.). |
| `GET` | `/agent/substitutes` | Find and rank candidate substitute teachers based on subject domain and fatigue. |
| `POST` | `/agent/substitute/find-candidates`| POST endpoint for complex multi-slot substitute instructor queries. |
| `POST` | `/agent/exam/generate` | Autonomous exam scheduling agent generating conflict-free mid-term or final exams. |
| `POST` | `/agent/exam/audit` | Audit an examination schedule against single-exam caps and 50% room spacing rules. |
| `GET` | `/agent/stream/{session_id}` | HTTP status polling fallback for agent event streaming. |
| `WS` | `/agent/stream/{session_id}` | Real-time WebSocket connection for live agent decision streams. |

---

### 5. Master Data Configuration (`/api/v1/configure`)
| Method | Endpoint | Description |
|---|---|---|
| `GET`/`POST` | `/configure/faculty` | List or register departmental faculty members. |
| `PUT`/`DELETE`| `/configure/faculty/{id}` | Update faculty rank/workload caps or delete faculty records. |
| `POST` | `/configure/faculty/csv-import` | Bulk import faculty rosters via CSV upload. |
| `GET`/`POST` | `/configure/rooms` | List or register physical venues, computer labs, and classrooms. |
| `PUT`/`DELETE`| `/configure/rooms/{id}` | Update room type, seating capacity, or availability. |
| `GET`/`POST` | `/configure/subjects` | List or register curriculum subjects and credit requirements. |
| `GET`/`POST` | `/configure/sections` | List or register academic sections by year and branch. |
| `GET`/`POST` | `/configure/assignments` | List or map faculty assignments to section lecture, tutorial, and lab slots. |
| `GET` | `/configure/wizard-defaults` | Retrieve in-memory cached seed defaults for setup wizards. |

---

### 6. Export Engine (`/api/v1/export`)
| Method | Endpoint | Description |
|---|---|---|
| `GET`/`POST` | `/export/excel` | Download complete department timetable workbook (.xlsx). |
| `GET`/`POST` | `/export/excel/version/{id}` | Download specific versioned Excel timetable workbook. |
| `POST` | `/export/excel/cohort/{key}` | Download cohort-specific workbook (`II_AIML`, `CS_DS`, `SPECIAL_PG`). |
| `POST` | `/export/excel/minors-honors` | Export global master sheet for Minors and Honors subjects. |
| `GET`/`POST` | `/export/pdf/section/{id}` | Download high-resolution single-section printable A4 PDF. |
| `GET`/`POST` | `/export/pdf/sections` | Download complete bundle of all section PDF timetables. |
| `GET`/`POST` | `/export/pdf/department` | Download consolidated single-document departmental timetable booklet. |
| `GET`/`POST` | `/export/zip/sections` | Download streaming .zip bundle containing all section timetable PDFs. |
| `GET`/`POST` | `/export/pdf/faculty` | Download weekly schedule PDFs for all faculty members. |
| `GET` | `/export/pdf/faculty/{id}` | Download weekly schedule PDF for a single faculty member. |
| `GET` | `/export/room-utilization` | Generate and export venue occupancy statistics spreadsheet. |
| `GET` | `/export/ical/faculty/{id}` | Generate RFC-5545 `.ics` calendar sync file for faculty schedules. |
| `GET` | `/export/json` | Export complete raw JSON timetable structure. |

---

## 🧪 Test Suite & Verification

The platform maintains an automated test suite comprising **43 specialized test modules** in `backend/tests/`:

```bash
# Run the complete test suite inside the container
docker exec -it vfstr_backend python -m pytest /app/tests/ -v --tb=short

# Run baseline ground-truth validation against V5 Excel
docker exec -it vfstr_backend python -m parser.excel_parser \
  --input "time_table/ACSE TIMETABLE (V5)  - W.e.f 15-7-2026.xlsx" \
  --validate-only
# Expected Output: "Room clashes: 51, Faculty clashes: 0"
```

### Quality & Performance Metrics
* **Unit & Integration Coverage**: 100% pass rate (**104 passed, 0 failed, 1 warning in 49.70s**).
* **30-Endpoint Integration Audit**: Automated script `comprehensive_endpoint_audit.py` passes 30/30 production endpoints through the Nginx gateway with `200 OK`.
* **Zero Clashes Guaranteed**: All generated CP-SAT timetables are mathematically proven to contain 0 room clashes, 0 faculty clashes, and 0 student cohort clashes.

---

## 👥 Institutional Leadership & Contributors

* **Institution**: Vignan's Foundation for Science, Technology & Research (VFSTR)
* **Department**: Department of Applied Computer Science & Engineering (ACSE)
* **Location**: Vadlamudi, Guntur District, Andhra Pradesh, India — 522213
