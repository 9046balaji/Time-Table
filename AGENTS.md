# AGENTS.md — VFSTR Timetable Scheduler

> This file governs how all AI agents (Claude Code sessions, sub-agents, tool calls) must
> behave when working on this project. Read this file **in full before writing any code**.
> Every agent spawned in this project inherits these rules unconditionally.

---

## 0. Project Identity

| Field | Value |
|---|---|
| **Project** | VFSTR ACSE Automated Timetable Scheduler |
| **Institution** | Vignan's Foundation for Science, Technology & Research, Vadlamudi, Guntur |
| **Problem** | Replace a manual Excel-based timetable process (51 room clashes in V5, 5 revisions in 5 days) with an automated constraint-solving web application |
| **Full Problem Doc** | `README_VFSTR_TimetableScheduler.md` — read this first for all math, constraints, and data |
| **Scale** | 44 sections, ~2,360 students, ~80 faculty, ~35 rooms, 48 slots/week |
| **Stack** | Next.js 14 (App Router) + FastAPI (Python) + PostgreSQL + Celery + OR-Tools |
| **Design Skill** | `ui-ux-pro-max` — invoke before every UI component, page, or style decision |

---

## 1. Agent Roles

This project uses **four specialized agent roles**. A single Claude Code session can play
multiple roles sequentially, but must declare which role it is operating in at the start
of each major task block.

---

### 🏗️ Role A — `ARCHITECT`

**Activates when:** designing system structure, database schema, API contracts, folder layout,
Docker services, or any decision that affects more than one layer.

**Responsibilities:**
- Own `README_VFSTR_TimetableScheduler.md` — keep it in sync with code reality
- Enforce the layered architecture: `UI → API → Solver → DB`
- Never let solver logic bleed into API routes
- Never let database queries appear in React components
- Produce ADRs (Architecture Decision Records) in `docs/decisions/` when making
  irreversible choices (library selection, schema changes, algorithm choice)
- Validate that new entities match the PostgreSQL schema in the README (15 tables defined)

**Must NOT:**
- Write UI markup
- Write solver math
- Skip the ADR when a decision is hard to reverse

**Output format for architectural decisions:**
```markdown
## ADR-NNN: [Title]
**Status:** Proposed / Accepted / Deprecated
**Context:** [why this decision is needed]
**Decision:** [what was decided]
**Consequences:** [what changes, what trade-offs]
```

---

### 🎨 Role B — `DESIGNER`

**Activates when:** creating or modifying any `.tsx`, `.css`, `.module.css`, or any file
that produces visual output in the browser.

**Responsibilities:**
- **ALWAYS invoke `ui-ux-pro-max` search BEFORE writing any component** — no exceptions
- Run at minimum 3 search queries: style, ux guidelines, and stack-specific rules
- Apply the design system from `design-system/` token files to every component
- Maintain WCAG 2.1 AA accessibility (contrast ratios, keyboard nav, ARIA labels)
- Use the timetable-specific design language defined in `design-system/tokens.css`

**Mandatory pre-coding ritual (copy-paste this block at the start of every UI task):**

```bash
# 1. Style direction for this component
python "${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max/scripts/search.py" \
  "[describe the component]" --domain style

# 2. UX guidelines
python "${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max/scripts/search.py" \
  "[describe the interaction]" --domain ux

# 3. Chart/data viz rules (for timetable grid, clash reports, dashboards)
python "${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max/scripts/search.py" \
  "[describe the data display]" --domain chart

# 4. Next.js stack rules
python "${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max/scripts/search.py" \
  "[component type]" --stack nextjs
```

**Design tokens (source of truth — never hardcode values outside these):**

```css
/* design-system/tokens.css */
--color-primary:    #1E40AF;   /* Deep university blue */
--color-secondary:  #7C3AED;   /* AI/ML violet accent */
--color-success:    #059669;   /* No-clash green */
--color-warning:    #D97706;   /* Soft constraint amber */
--color-danger:     #DC2626;   /* Hard constraint clash red */
--color-surface:    #F8FAFC;   /* Page background */
--color-card:       #FFFFFF;
--color-border:     #E2E8F0;
--color-text-primary:   #0F172A;
--color-text-muted:     #64748B;

/* Timetable-specific */
--slot-lecture:     #DBEAFE;   /* Lecture slot fill */
--slot-lab:         #EDE9FE;   /* Lab slot fill */
--slot-tutorial:    #D1FAE5;   /* Tutorial slot fill */
--slot-library:     #FEF3C7;   /* Library slot fill */
--slot-break:       #F1F5F9;   /* Break/lunch fill */
--slot-clash:       #FEE2E2;   /* Clash highlight fill */
--slot-empty:       #FFFFFF;

/* Typography */
--font-sans:  'Inter', system-ui, sans-serif;
--font-mono:  'JetBrains Mono', 'Fira Code', monospace;

/* Spacing scale: 4px base */
--space-1: 4px;  --space-2: 8px;   --space-3: 12px;
--space-4: 16px; --space-6: 24px;  --space-8: 32px;
--space-12: 48px; --space-16: 64px;

/* Timetable grid dimensions */
--slot-width:  140px;
--slot-height: 72px;
--day-header:  48px;
--period-col:  80px;
```

**Component rules:**
- All grid cells: `border-radius: 6px`, `font-size: 12px`, truncate overflow with tooltip
- Clash cells: red left-border `4px solid var(--color-danger)` + `--slot-clash` background
- Lab cells spanning 2–3 periods: use `grid-row: span 2` or `span 3`
- Mobile: collapse timetable grid to a list/accordion view below 768px
- Dark mode: all tokens must have a `[data-theme="dark"]` counterpart

**Must NOT:**
- Use magic color hex values outside `tokens.css`
- Use `!important` in CSS
- Create a component without reading `ui-ux-pro-max` output first
- Use inline `style={}` props except for dynamic slot-based widths/heights

---

### ⚙️ Role C — `SOLVER`

**Activates when:** working in `backend/solver/`, `backend/tasks/`, or any file
containing constraint logic, fitness functions, or algorithm implementation.

**Responsibilities:**
- Implement all 10 Hard Constraints (HC-01 through HC-10) from the README
- Implement all 10 Soft Constraints (SC-01 through SC-10) from the README
- Keep constraint definitions in `backend/solver/constraints.py` — never inline them in tasks
- Every solver run must be recorded in `solver_runs` DB table (start, end, violations, config)
- Expose solver progress via WebSocket at `/api/v1/solve/{run_id}/stream`
- Produce JSON output matching `TimetableEntry` Pydantic schema exactly

**Hard constraint priority order (if solver must relax, relax in REVERSE order):**
```
HC-01 Room Conflict         → NEVER relax
HC-02 Faculty Double-Book   → NEVER relax
HC-03 Student Conflict      → NEVER relax
HC-04 Subject Frequency     → NEVER relax
HC-05 Room Capacity         → Relax last resort only
HC-06 Room Type             → Relax last resort only
HC-07 Break/Lunch Block     → NEVER relax
HC-08 Lab Consecutiveness   → Relax only for 3-hour labs if no room available
HC-09 Faculty Availability  → Soft in Phase 1, Hard in Phase 2
HC-10 No 4-consec Teaching  → Soft in Phase 1, Hard in Phase 2
```

**Solver config schema (all runs must use this):**
```python
class SolverConfig(BaseModel):
    algorithm: Literal["CP-SAT", "GA", "Hybrid"] = "CP-SAT"
    scope: str  # "ALL" | "II_AIML" | section ID list
    timeout_seconds: int = 120
    population_size: int = 200      # GA only
    generations: int = 1000         # GA only
    mutation_rate: float = 0.05     # GA only
    elite_count: int = 10           # GA only
    hard_penalty_weight: int = 10000
    soft_penalty_weights: dict = {
        "SC-01": 50, "SC-02": 30, "SC-03": 10,
        "SC-04": 5,  "SC-05": 20, "SC-06": 5,
        "SC-07": 100,"SC-08": 15, "SC-09": 10,
        "SC-10": 5
    }
```

**Must NOT:**
- Return a timetable with any HC-01, HC-02, HC-03, or HC-07 violations
- Block the FastAPI event loop (always use Celery tasks)
- Skip writing the solver run record to DB
- Use `time.sleep()` for progress — use Celery `self.update_state()`

---

### 🧪 Role D — `VALIDATOR`

**Activates when:** writing tests, running the conflict checker, reviewing a PR,
or verifying that a generated timetable is correct.

**Responsibilities:**
- Every API endpoint must have at least 1 integration test in `backend/tests/`
- Every constraint must have a unit test that proves violation detection works
- Baseline validation: import V5 Excel → must detect **exactly 51 room clashes**
- Solver validation: any solver output must pass `validate_hard_constraints()` before saving
- Run `pytest backend/tests/ -v --tb=short` and fix ALL failures before committing

**Required test coverage gates:**
```
Constraint tests:     100% (all 20 constraints must have tests)
Parser tests:          90% (all sheet types must be parsed)
API endpoint tests:    80% (all routes must have at least smoke test)
Solver output tests:  100% (output must always be validated before saving)
```

**Canonical validation script (run before every merge):**
```bash
# 1. Parse V5 and check baseline clashes
python backend/parser/excel_parser.py \
  --input "data/ACSE_TIMETABLE_V5.xlsx" \
  --validate-only
# Expected: "Room clashes: 51, Faculty clashes: 0"

# 2. Run full test suite
pytest backend/tests/ -v --tb=short --cov=backend --cov-report=term-missing

# 3. Type check
mypy backend/ --strict

# 4. Lint
ruff check backend/

# 5. Frontend checks
cd frontend && npm run type-check && npm run lint
```

**Must NOT:**
- Merge code that fails the baseline clash detection (51 room clashes in V5)
- Skip the solver output validation step
- Mark a constraint as "tested" with only a happy-path test (must also test violation detection)

---

## 2. Universal Rules (ALL agents, ALL roles)

### 2.1 File Structure — Never Deviate

```
vfstr-timetable-scheduler/
├── AGENTS.md                    ← This file (never modify without team discussion)
├── README_VFSTR_TimetableScheduler.md  ← Problem doc (keep in sync)
├── docs/
│   ├── decisions/               ← ADR files (ADR-001.md, ADR-002.md, ...)
│   └── api/                     ← OpenAPI spec snapshots
├── frontend/
│   ├── src/
│   │   ├── app/                 ← Next.js App Router pages
│   │   │   ├── (dashboard)/
│   │   │   ├── (timetable)/
│   │   │   ├── (import)/
│   │   │   ├── (configure)/
│   │   │   └── (export)/
│   │   ├── components/
│   │   │   ├── ui/              ← shadcn/ui primitives (DO NOT modify these)
│   │   │   ├── timetable/       ← TimetableGrid, SlotCell, DayHeader, PeriodLabel
│   │   │   ├── solver/          ← SolverProgress, FitnessChart, RunHistory
│   │   │   ├── clash/           ← ClashReport, ClashBadge, ClashDiffView
│   │   │   ├── faculty/         ← FacultyCalendar, WorkloadBar, FacultyCard
│   │   │   └── forms/           ← ImportForm, SectionForm, SubjectForm, RoomForm
│   │   ├── hooks/
│   │   │   ├── useTimetable.ts
│   │   │   ├── useSolver.ts     ← WebSocket connection + progress state
│   │   │   ├── useClashReport.ts
│   │   │   └── useImport.ts
│   │   ├── lib/
│   │   │   ├── api.ts           ← Axios instance + all API call functions
│   │   │   └── types.ts         ← All TypeScript types (mirrors Pydantic schemas)
│   │   └── design-system/
│   │       ├── tokens.css       ← SINGLE SOURCE OF TRUTH for all design values
│   │       └── globals.css
│   ├── public/
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── api/v1/             ← Route handlers ONLY (no business logic)
│   │   ├── models/             ← SQLAlchemy ORM models
│   │   ├── schemas/            ← Pydantic request/response schemas
│   │   ├── services/           ← Business logic (timetable service, faculty service)
│   │   └── core/               ← Config, DB connection, auth
│   ├── solver/
│   │   ├── constraints.py      ← HC-01..HC-10, SC-01..SC-10 as functions
│   │   ├── csat_solver.py      ← OR-Tools CP-SAT implementation
│   │   ├── genetic_algorithm.py
│   │   ├── fitness.py
│   │   └── conflict_checker.py ← Standalone, importable, no DB dependency
│   ├── parser/
│   │   ├── excel_parser.py
│   │   ├── excel_exporter.py
│   │   └── normalizer.py
│   ├── tasks/
│   │   ├── celery_app.py
│   │   └── solver_tasks.py
│   ├── tests/
│   │   ├── conftest.py         ← Fixtures: test DB, sample sections, V5 Excel
│   │   ├── test_constraints.py
│   │   ├── test_parser.py
│   │   ├── test_solver.py
│   │   └── test_api/
│   ├── alembic/                ← DB migrations
│   └── main.py
│
├── data/
│   ├── ACSE_TIMETABLE_V5.xlsx  ← Source of truth for baseline validation
│   └── seed/                   ← JSON seeds extracted from V5
│
├── docker-compose.yml
├── Makefile
└── .env.example
```

### 2.2 Naming Conventions

| Layer | Convention | Example |
|---|---|---|
| Python files | `snake_case` | `excel_parser.py`, `csat_solver.py` |
| Python classes | `PascalCase` | `TimetableEntry`, `SolverConfig` |
| Python functions | `snake_case` | `detect_room_clashes()` |
| TypeScript files | `PascalCase` for components | `TimetableGrid.tsx` |
| TypeScript files | `camelCase` for hooks/lib | `useSolver.ts`, `api.ts` |
| CSS classes | `kebab-case` | `.slot-cell--clash`, `.faculty-card` |
| DB tables | `snake_case` plural | `timetable_entries`, `solver_runs` |
| API routes | `kebab-case` | `/api/v1/section-subjects` |
| Constants | `SCREAMING_SNAKE` | `MAX_FACULTY_HOURS = 16` |
| Constraint IDs | Exact README format | `HC-01`, `SC-07` |

### 2.3 Commit Message Format

All commits must follow Conventional Commits:
```
<type>(<scope>): <subject>

Types: feat | fix | refactor | test | docs | style | chore | perf
Scopes: solver | parser | api | ui | db | auth | config

Examples:
  feat(solver): implement HC-01 room conflict constraint in CP-SAT
  fix(parser): handle 'LIBRARY' slots without room codes in V5
  feat(ui): add TimetableGrid component with clash highlighting
  test(constraints): add violation detection tests for HC-04 and HC-08
  docs: update ADR-003 for CP-SAT timeout strategy
```

### 2.4 Agent Communication Protocol

When an agent completes a task and hands off to another role, it MUST leave a handoff note:

```markdown
## 🤝 HANDOFF NOTE
**From:** [Role A/B/C/D]
**To:** [Role A/B/C/D]
**Task completed:** [one line]
**Files changed:** [list]
**Next task:** [exact description]
**Blockers / questions:** [or "None"]
**Tests passing:** [YES / NO — if NO, explain]
```

### 2.5 What Agents Must NEVER Do

- ❌ Delete or overwrite `AGENTS.md` or `README_VFSTR_TimetableScheduler.md`
- ❌ Push code with failing tests
- ❌ Use `any` type in TypeScript (use `unknown` and narrow)
- ❌ Write solver logic inside API route handlers
- ❌ Write UI components without first running `ui-ux-pro-max` searches
- ❌ Hardcode room names, faculty names, or subject codes as string literals outside seed files
- ❌ Run solver synchronously (always Celery)
- ❌ Return timetable data with HC-01/HC-02/HC-03 violations
- ❌ Merge a branch without `VALIDATOR` role sign-off

---

## 3. Environment Setup (Every Agent Must Verify)

### Required Tools

```bash
# Python (solver, parser, backend)
python --version    # Must be >= 3.11
pip install -r backend/requirements.txt

# Node (frontend)
node --version      # Must be >= 20 LTS
npm install         # in frontend/

# OR-Tools (solver engine)
pip install ortools>=9.9

# Celery + Redis
pip install celery[redis]
redis-server --version  # Must be >= 7.0

# Database
psql --version      # PostgreSQL >= 16

# ui-ux-pro-max skill (REQUIRED FOR DESIGNER ROLE)
# Verify installation:
python "${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max/scripts/search.py" \
  "test query" --domain style
# Must return results without error
```

### Environment Variables (copy from `.env.example`)

```bash
# Database
DATABASE_URL=postgresql://vfstr:password@localhost:5432/timetable_db

# Redis / Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# API
SECRET_KEY=<generate with: openssl rand -hex 32>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Solver
SOLVER_DEFAULT_TIMEOUT=120
SOLVER_MAX_WORKERS=8

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Docker One-Command Start

```bash
make up         # docker compose up -d (postgres, redis, celery, fastapi, nextjs)
make seed       # Import V5 Excel into DB
make test       # Run full test suite
make validate   # Run V5 baseline clash check (expect: 51 room clashes)
```

---

## 4. Domain Knowledge Every Agent Must Know

### Subject Code → Type Mapping

```python
# All codes from the actual VFSTR ACSE data
LAB_SUBJECTS = {  # Must have consecutive periods, must use lab rooms
    'SFCDS', 'DMS', 'DS', 'AI', 'DBMS', 'OOPS', 'DEF',
    'DL', 'WT', 'CV', 'ADS', 'MLOP', 'IDP',
    'CNS', 'TM', 'GENAI', 'IOT'
}

LECTURE_ONLY = {'QALR', 'KRR', 'Ethics-AI', 'OE'}
SPECIAL_SLOTS = {'LIBRARY', 'BREAK', 'LUNCH', 'SL/EL', 'Minors/Honors'}

# Type suffix convention from the Excel files:
# DS     → Lecture (L)
# DS(T)  → Tutorial (T)
# DS(P)  → Practical/Lab (P)
# DS(T&P) → Combined Tutorial + Practical
```

### Period Numbers → Times

```python
PERIODS = {
    1: ("08:15", "09:05"),
    2: ("09:05", "09:55"),
    # BREAK: 09:55–10:10 (is_blocked=True, period_id=None)
    3: ("10:10", "11:00"),
    4: ("11:00", "11:50"),
    5: ("11:50", "12:40"),
    # LUNCH: 12:40–13:40 (is_blocked=True, period_id=None)
    6: ("13:40", "14:30"),
    7: ("14:30", "15:20"),
    8: ("15:20", "16:05"),
}
DAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']
```

### Room Types

```python
LAB_ROOMS = {
    '604', '605', '606',           # Computer labs (ground/2nd floor)
    '611', '612', '615', '616', '617',  # Computer labs (6th floor)
    'AFTF-12', 'AFTF-13', 'AFTF-14',   # High-capacity GPU labs
    'AFF-09', 'AFF-10',            # Small project rooms
}

CLASSROOM_ROOMS = {
    '601', '602', '603', '607', '608', '609', '610',
    '613', '614', '618', '619',
    '215', '216', '217', '218',
    '514-A', '514-B', '518',
    '401', '402', '418',
    '501',
}

GPU_LABS = {'AFTF-12', 'AFTF-13', 'AFTF-14'}  # Prefer for DL, CV, MLOP
```

### Faculty Grades → Max Hours

```python
FACULTY_MAX_HOURS = {
    'Professor': 12,
    'Associate Professor': 14,
    'Assistant Professor': 16,
}
```

### The 5 Versions & What Changed

| Version | Date | Key Change |
|---|---|---|
| V1 | 10-Jul | Initial release (894 slots) |
| V2 | 11-Jul | Minor slot adjustments |
| V3 | 13-Jul | Significant room reassignments |
| V4 | 14-Jul | Faculty allocation fixes |
| V5 | 15-Jul | Added MINORHONORS sheet (1000 slots) — **CURRENT BASELINE** |

**V5 is the ground truth.** All parser tests, baseline clash counts (51), and slot
counts (1000) are verified against V5 specifically.

---

## 5. Page-by-Page UI Spec

The DESIGNER role must follow this page spec. Each page corresponds to an App Router
route group. Run `ui-ux-pro-max` before implementing each page.

### Page 1: `/` — Dashboard

**Purpose:** At-a-glance status of the current timetable

**Components:**
- Header: `VFSTR ACSE Timetable Scheduler` + academic year badge + `[Run Solver]` CTA
- Stats row: `44 Sections` | `~80 Faculty` | `35 Rooms` | `1,000 Slots/week`
- Clash Summary Card: big red number showing current hard violations (51 in V5)
- Version Timeline: horizontal list of V1–V5 cards, each showing date + violation count
- Quick Actions: Import Excel | View Timetable | Export | Validate

**ui-ux-pro-max queries for this page:**
```bash
python ... "admin dashboard stats cards" --domain style
python ... "data overview KPI metrics layout" --domain ux
python ... "status indicator badge alerts" --domain ux
```

---

### Page 2: `/import` — Excel Import

**Purpose:** Upload existing VFSTR Excel → parse → show clash report → confirm import

**Components:**
- Drag-drop zone (show accepted file format)
- Parse progress: "Reading 10 sheets... Found 44 sections... Extracted 1,000 slots..."
- Results summary: sections found, faculty mappings, room codes detected
- Clash Report Table: Day | Period | Room | Section A | Section B | Subject Conflict
- Confirm/Cancel buttons

**ui-ux-pro-max queries:**
```bash
python ... "file upload drag drop zone" --domain ux
python ... "data table conflict error report" --domain ux
python ... "import wizard multi-step progress" --domain style
```

---

### Page 3: `/configure` — Data Management

**Purpose:** CRUD for all entities before running the solver

**Tabs:**
- **Sections** — list of 44 sections with branch/year filter
- **Faculty** — list with workload bar (current h / max h per week)
- **Rooms** — grid showing type (classroom/lab) and capacity
- **Subjects** — table with L/T/P hours and room type requirement
- **Assignments** — matrix: which faculty teaches which subject to which section

**ui-ux-pro-max queries:**
```bash
python ... "admin CRUD table list sidebar tabs" --domain style
python ... "data management form validation" --domain ux
python ... "progress bar workload indicator" --domain chart
```

---

### Page 4: `/schedule` — Timetable View & Solver

**Purpose:** View generated timetable, trigger solver, see progress

**Layout:**
- Left sidebar: section tree (Year → Branch → Section A, B, ...)
- Main area: `TimetableGrid` — 6 columns (days) × 8 rows (periods)
- Right panel: Clash report for selected section
- Top bar: Version selector | Solver button | View toggle (Section/Faculty/Room)
- Solver panel: algorithm picker, config sliders, "Run" button, progress bar + fitness chart

**TimetableGrid cell anatomy:**
```
┌──────────────────────┐
│ DS(P)     ← subject  │
│ 604       ← room     │
│ Dr.Reddy  ← faculty  │
└──────────────────────┘
• Color = slot type (lecture/lab/tutorial/library)
• Red left border = CLASH (click for details)
• Purple badge = Minors/Honors global slot
```

**ui-ux-pro-max queries:**
```bash
python ... "scheduling calendar grid week view" --domain style
python ... "data grid cell selection highlight" --domain ux
python ... "real-time progress chart genetic algorithm" --domain chart
python ... "split panel layout sidebar main" --domain style
```

---

### Page 5: `/export` — Export

**Purpose:** Download timetable in multiple formats

**Options:**
- Excel (same format as V5 — section tabs, room codes in cells, faculty legend below)
- PDF per section (printable A4)
- PDF full department (all sections, 2 per page)
- JSON (raw for API integrations)
- Faculty Schedule PDF (one page per faculty showing their full week)
- Room Utilization Report (which rooms are free vs occupied each period)

---

## 6. Solver Progress WebSocket Protocol

The frontend `useSolver.ts` hook connects to `ws://backend/api/v1/solve/{run_id}/stream`.
The backend MUST emit messages in this exact JSON format:

```typescript
// Message types the WebSocket emits:
type SolverMessage =
  | { type: 'status';      message: string }
  | { type: 'progress';    generation: number; fitness: number; hard_violations: number; soft_violations: number }
  | { type: 'feasible';    message: string; hard_violations: number }
  | { type: 'complete';    version_id: number; hard_violations: number; soft_violations: number; runtime_seconds: number }
  | { type: 'error';       message: string; detail: string }
```

The frontend must render:
- A fitness score line chart updating in real time (generation on X-axis, fitness on Y)
- Hard violations countdown: `51 → 43 → 21 → 7 → 0` with each update
- Green checkmark animation when `hard_violations` reaches 0
- Time elapsed counter

---

## 7. Priority Build Order

Follow this order strictly. Do NOT jump ahead:

```
Phase 0  ✅ Problem documented (README_VFSTR_TimetableScheduler.md — DONE)
Phase 0  ✅ Agents defined    (AGENTS.md — THIS FILE — DONE)

Phase 1  🔲 Project scaffold  (Next.js + FastAPI + Docker Compose)
Phase 2  🔲 DB schema         (Alembic migrations for all 15 tables)
Phase 3  🔲 Excel parser      (parse V5 → 44 sections, 1000 slots, 51 clashes)
Phase 4  🔲 Data seed         (V5 data → PostgreSQL)
Phase 5  🔲 CRUD APIs         (all entity endpoints)
Phase 6  🔲 Conflict checker  (standalone, no DB dep, 100% tested)
Phase 7  🔲 Frontend shell    (routing, layout, design system tokens)
Phase 8  🔲 Import UI         (upload → parse → clash report)
Phase 9  🔲 CP-SAT solver     (HC-01..HC-10, Celery task, WS progress)
Phase 10 🔲 Timetable grid    (TimetableGrid component with clash rendering)
Phase 11 🔲 GA optimizer      (SC-01..SC-10, fitness chart)
Phase 12 🔲 Export engine     (Excel + PDF generators)
Phase 13 🔲 Polish & deploy   (auth, dark mode, Docker prod build)
```

**Do not start Phase N+1 until Phase N has passing tests.**

---

## 8. Skill Integration: `ui-ux-pro-max`

This skill is installed at:
```
${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max/
```

### Installation (if not already installed)

```bash
# Method 1: Claude Code plugin
/plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill
/plugin install ui-ux-pro-max@ui-ux-pro-max-skill

# Method 2: npm CLI
npm install -g ui-ux-pro-max-cli
uipro init --ai claude --global
```

### Usage Pattern for This Project

```bash
# When building the TimetableGrid:
python "${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max/scripts/search.py" \
  "scheduling calendar grid week" --domain style

python "${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max/scripts/search.py" \
  "scheduling grid SaaS productivity" --design-system -p "VFSTRScheduler"

python "${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max/scripts/search.py" \
  "data grid conflict highlighting" --domain ux

python "${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max/scripts/search.py" \
  "data table sorting filtering" --stack nextjs

# When building the Solver Progress dashboard:
python "${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max/scripts/search.py" \
  "real-time monitoring dashboard" --domain style

python "${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max/scripts/search.py" \
  "line chart real-time streaming" --domain chart
```

Always read the output fully, extract the relevant palette + typography + spacing rules,
and apply them before writing any JSX.

---

*AGENTS.md — VFSTR Timetable Scheduler — Version 1.0*  
*Created: July 2026 | Maintained by: Project Lead*  
*Last updated: when constraints, tech stack, or team roles change*
