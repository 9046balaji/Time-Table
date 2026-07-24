# 🚀 VFSTR Timetable Scheduler — Project Starter Prompt

> Copy everything below the horizontal rule and paste it as your first message
> in a new Claude Code session (or Cowork session). It contains the full context
> the agent needs to start building immediately without asking clarifying questions.

---

## ✂️ PASTE THIS INTO CLAUDE CODE ↓

---

You are starting the **VFSTR ACSE Automated Timetable Scheduler** — a web application
to replace a manual Excel-based university timetable process that currently produces
51 room clashes in its "final" version and requires 5 revisions in 5 days every semester.

---

### 📚 READ THESE TWO FILES FIRST — BEFORE WRITING ANY CODE

1. **`README_VFSTR_TimetableScheduler.md`** — Full problem analysis: 44 sections,
   ~80 faculty, ~35 rooms, 20 hard + soft constraints, NP-Hard math, PostgreSQL schema
   (15 tables), REST API design (20+ endpoints), solver architecture, 8-week roadmap.

2. **`AGENTS.md`** — Your operating rules: 4 agent roles (ARCHITECT, DESIGNER, SOLVER,
   VALIDATOR), file structure, naming conventions, domain constants (period times, room
   codes, subject codes, faculty workload limits), page-by-page UI specs, WebSocket
   protocol, and build phase order.

**Do not skip reading these. They are your specification documents.**

---

### 🎨 UI/UX DESIGN INTELLIGENCE — ui-ux-pro-max Skill

You have the `ui-ux-pro-max` skill installed. Before you write ANY component, page,
or CSS, run the following searches and read the output completely:

```bash
# Run ALL 4 of these before touching any UI file:

# 1. Overall style direction for a scheduling/productivity SaaS tool
python "${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max/scripts/search.py" \
  "scheduling SaaS dashboard productivity" --domain style

# 2. Generate a complete design system for this project
python "${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max/scripts/search.py" \
  "university scheduling tool academic" --design-system -p "VFSTRScheduler"

# 3. UX guidelines for data-heavy admin tools
python "${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max/scripts/search.py" \
  "data grid table admin interface dense layout" --domain ux

# 4. Next.js + shadcn/ui stack guidelines
python "${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max/scripts/search.py" \
  "nextjs app router component library layout" --stack nextjs
```

Store the design system output in `frontend/src/design-system/tokens.css`.
The visual language should feel like: **Linear meets Notion meets a university portal** —
clean, dense-information-friendly, with clear status colors (red for clashes,
green for resolved, amber for warnings).

---

### 🏗️ YOUR TASK FOR THIS SESSION: Phase 1 — Project Scaffold

Build the complete project skeleton. By the end of this session, `make up` must start
all services, `make seed` must import V5 data, and the frontend must render a working
dashboard page (even with placeholder data).

**Work in this exact order:**

---

#### Step 1 — Monorepo Root Setup

Create the root directory structure exactly as defined in `AGENTS.md` Section 2.1.
Create:
- `Makefile` with targets: `up`, `down`, `seed`, `test`, `validate`, `lint`
- `docker-compose.yml` with services: `postgres`, `redis`, `backend`, `celery`, `frontend`
- `.env.example` with all variables from `AGENTS.md` Section 3
- `.gitignore` (Python + Node + env files)

The Makefile must be your CLI interface for every operation in this project.

---

#### Step 2 — Backend Scaffold (FastAPI)

```bash
cd backend/
```

Create:
- `main.py` — FastAPI app with CORS, health check at `GET /health`, API versioning
- `core/config.py` — Pydantic Settings reading from `.env`
- `core/database.py` — SQLAlchemy async engine + session maker
- `requirements.txt` — pin versions:
  ```
  fastapi==0.115.0
  uvicorn[standard]==0.30.0
  sqlalchemy[asyncio]==2.0.35
  asyncpg==0.29.0
  alembic==1.13.2
  pydantic==2.9.0
  pydantic-settings==2.5.2
  python-jose[cryptography]==3.3.0
  celery[redis]==5.4.0
  ortools==9.11.4210
  openpyxl==3.1.5
  pandas==2.2.3
  python-multipart==0.0.12
  ruff==0.6.9
  mypy==1.11.0
  pytest==8.3.3
  pytest-asyncio==0.24.0
  httpx==0.27.2
  ```

---

#### Step 3 — Database Schema (Alembic + SQLAlchemy)

Create all 15 SQLAlchemy models from `README_VFSTR_TimetableScheduler.md` Section 10
(Database Schema). Each model goes in `backend/app/models/`:

```
models/
  __init__.py
  base.py          ← DeclarativeBase + TimestampMixin
  department.py    ← Department
  academic_year.py ← AcademicYear
  branch.py        ← Branch
  section.py       ← Section
  faculty.py       ← Faculty
  subject.py       ← Subject
  section_subject.py  ← SectionSubject (junction)
  room.py          ← Room
  time_slot.py     ← TimeSlot
  timetable.py     ← TimetableVersion + TimetableEntry
  solver_run.py    ← SolverRun
```

Run `alembic init alembic` then `alembic revision --autogenerate -m "initial schema"`.

---

#### Step 4 — Excel Parser

Build `backend/parser/excel_parser.py`.

The parser must handle the exact VFSTR Excel format:
- Cell values like `DS(P)\n604` (subject + room separated by newline)
- Section headers like `II AIML-A`, `III CS`, `IV DS`
- Faculty legend rows like `Data Structures(L): Dr. S.Srikantha Reddy`
- Special slots: `LIBRARY`, `BREAK`, `LUNCH`, `SL/EL`, `MINORS/HONORS`
- Sheet names: `II AIML`, `III AIML`, `IV AIML`, `CS`, `DS`, `CSBS`, `IOT`, `BS(DS)`,
  `MSC(DS) 2`, `M.TECH`, `MINORHONORS`

Use the acronym map from `AGENTS.md` Section 4 to normalize subject codes.

**Validation checkpoint — this test must pass:**
```python
# tests/test_parser.py
def test_v5_baseline():
    result = ExcelTimetableParser().parse_file("data/ACSE_TIMETABLE_V5.xlsx")
    assert result.total_sections == 44
    assert result.total_slots == 1000
    assert len(result.faculty_mappings) == 384
    clashes = ConflictChecker().detect(result)
    assert clashes.room_clashes == 51    # ← This is the baseline. Must be exactly 51.
    assert clashes.faculty_clashes == 0  # ← Faculty got right. Must be 0.
```

Do not move to Step 5 until this test passes.

---

#### Step 5 — Data Seed

Create `backend/seed.py`:
1. Parse `data/ACSE_TIMETABLE_V5.xlsx`
2. Insert entities in order: Department → AcademicYear → Branches → Sections →
   Faculty → Subjects → Rooms → TimeSlots → SectionSubjects → TimetableVersion →
   TimetableEntries
3. Print summary: "Seeded: 44 sections, 384 faculty mappings, 1000 timetable entries"
4. Create `make seed` target that runs this

---

#### Step 6 — Core APIs (Thin Layer)

Create these 5 route files in `backend/app/api/v1/`:

```python
# sections.py  — GET /api/v1/sections (paginated, filter by branch/year)
# faculty.py   — GET /api/v1/faculty (with computed hours_this_week)
# rooms.py     — GET /api/v1/rooms (filter by type)
# timetable.py — GET /api/v1/timetable/{version_id}/section/{section_id}
# validate.py  — GET /api/v1/validate/{version_id}
#                Returns: { hard_violations, soft_violations, details[] }
```

Keep these THIN — no business logic in route handlers. Logic goes in `services/`.

---

#### Step 7 — Frontend Scaffold (Next.js 14)

```bash
npx create-next-app@latest frontend \
  --typescript --tailwind --eslint --app --src-dir \
  --import-alias "@/*"
cd frontend
npx shadcn@latest init
npx shadcn@latest add button card badge table tabs progress separator skeleton
```

Install additional deps:
```bash
npm install axios @tanstack/react-query zustand lucide-react recharts
npm install -D @types/node
```

Create `src/design-system/tokens.css` — paste the design tokens from `AGENTS.md`
Section 1 (Role B) PLUS any additional tokens from the `ui-ux-pro-max` design system
output you got in Step 0.

Import `tokens.css` in `src/app/globals.css`.

---

#### Step 8 — App Router Structure

Create the route group structure from `AGENTS.md` Section 5:

```
src/app/
  layout.tsx              ← Root layout: fonts, theme, QueryClientProvider
  (dashboard)/
    page.tsx              ← Dashboard with stats cards
  (timetable)/
    page.tsx              ← TimetableGrid viewer + Solver panel
  (import)/
    page.tsx              ← Excel upload + clash report
  (configure)/
    page.tsx              ← CRUD tabs (sections/faculty/rooms/subjects)
  (export)/
    page.tsx              ← Export options
```

Create a shared `src/components/layout/`:
- `AppShell.tsx` — sidebar nav + top bar wrapper
- `Sidebar.tsx` — navigation links to all 5 pages
- `TopBar.tsx` — breadcrumb + academic year badge + user menu

---

#### Step 9 — Dashboard Page (First Rendered UI)

This is the first thing the user sees. Make it polished.

**Run ui-ux-pro-max FIRST:**
```bash
python "${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max/scripts/search.py" \
  "admin dashboard stats overview SaaS" --domain style

python "${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max/scripts/search.py" \
  "KPI metrics card grid status" --domain ux

python "${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max/scripts/search.py" \
  "timeline version history comparison" --domain style
```

Then build `(dashboard)/page.tsx` with:

```tsx
// Components to create:
<DashboardPage>
  <StatsRow>
    <StatCard label="Sections" value="44" icon={<Users />} />
    <StatCard label="Faculty" value="80+" icon={<GraduationCap />} />
    <StatCard label="Rooms" value="35" icon={<Building2 />} />
    <StatCard label="Slots / Week" value="1,000" icon={<Calendar />} />
  </StatsRow>

  <ClashSummaryCard
    hardViolations={51}          // from /api/v1/validate/current
    softViolations={0}
    status="NEEDS_FIX"           // "VALID" | "NEEDS_FIX"
  />

  <VersionTimeline versions={[
    { label: "V1", date: "10 Jul", violations: 67, current: false },
    { label: "V2", date: "11 Jul", violations: 58, current: false },
    { label: "V3", date: "13 Jul", violations: 51, current: false },
    { label: "V4", date: "14 Jul", violations: 51, current: false },
    { label: "V5", date: "15 Jul", violations: 51, current: true  },
    { label: "V6 AUTO", date: "—",   violations: 0,  current: false, pending: true },
  ]} />

  <QuickActions>
    <ActionButton href="/import"    icon={<Upload />}    label="Import Excel" />
    <ActionButton href="/schedule"  icon={<Bot />}       label="Run Solver"   primary />
    <ActionButton href="/configure" icon={<Settings />}  label="Configure"    />
    <ActionButton href="/export"    icon={<Download />}  label="Export"       />
  </QuickActions>
</DashboardPage>
```

The `ClashSummaryCard` must be visually prominent:
- When violations > 0: red background tint, warning icon, "51 Room Clashes Detected"
- When violations = 0: green background tint, checkmark, "✓ No Clashes — Ready to Export"

---

#### Step 10 — API Client + React Query Setup

Create `src/lib/api.ts`:
```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: { 'Content-Type': 'application/json' }
})

export const timetableApi = {
  getSections: () => api.get('/api/v1/sections'),
  getFaculty: () => api.get('/api/v1/faculty'),
  getRooms: () => api.get('/api/v1/rooms'),
  getTimetable: (versionId: number, sectionId: number) =>
    api.get(`/api/v1/timetable/${versionId}/section/${sectionId}`),
  validate: (versionId: number) =>
    api.get(`/api/v1/validate/${versionId}`),
  importExcel: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/api/v1/import/excel', form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  runSolver: (config: SolverConfig) =>
    api.post('/api/v1/solve', config),
}
```

Create `src/lib/types.ts` mirroring all Pydantic schemas from the backend.

---

### ✅ Session End Checklist

Before ending this session, verify ALL of the following:

```bash
# 1. All services start
make up
curl http://localhost:8000/health     # → {"status": "ok"}
curl http://localhost:3000            # → Dashboard renders in browser

# 2. Seed runs cleanly
make seed
# → "Seeded: 44 sections, 384 faculty mappings, 1000 timetable entries"

# 3. Baseline validation passes
make validate
# → "Room clashes: 51, Faculty clashes: 0" ← EXACTLY THIS

# 4. API returns data
curl http://localhost:8000/api/v1/sections | jq '.total'
# → 44

curl http://localhost:8000/api/v1/validate/1 | jq '.hard_violations'
# → 51

# 5. Tests pass
make test
# → all green, 0 failures

# 6. TypeScript compiles
cd frontend && npm run type-check
# → 0 errors

# 7. Frontend accessible
# Open http://localhost:3000 — Dashboard renders:
# - 4 stat cards (44 sections, 80+ faculty, 35 rooms, 1,000 slots)
# - Red clash card showing "51 Room Clashes Detected"
# - Version timeline V1→V5→V6 AUTO
# - 4 quick action buttons
```

If any check fails, fix it before declaring this session complete.

---

### 🤝 Handoff Note Template (Fill This In At End of Session)

```markdown
## 🤝 HANDOFF NOTE — Phase 1 Complete
**From:** ARCHITECT + DESIGNER (Phase 1 session)
**To:** SOLVER role (Phase 2 — Conflict Checker + CP-SAT)

**Completed:**
- [ ] Monorepo root (Makefile, docker-compose, .env.example)
- [ ] FastAPI backend with 5 core API routes
- [ ] SQLAlchemy models for all 15 DB tables
- [ ] Alembic initial migration applied
- [ ] Excel parser (V5: 44 sections, 1000 slots, 51 clashes ✓)
- [ ] DB seeder working
- [ ] Next.js frontend with 5 route groups + AppShell
- [ ] Dashboard page with StatsRow, ClashSummaryCard, VersionTimeline
- [ ] Design system tokens.css + ui-ux-pro-max applied
- [ ] All 10 checklist items above passing

**Files changed:** [list key files created]

**Next task for SOLVER role:**
Build `backend/solver/conflict_checker.py` (standalone, no DB dep),
then `backend/solver/csat_solver.py` implementing HC-01 through HC-10.
Reference `AGENTS.md` Section 1 (Role C) for all solver rules.

**Blockers:** [none / describe any]
**Tests passing:** YES / NO
```

---

### ⚡ Key Facts to Keep in Mind Throughout

- **The department is ACSE at VFSTR** — Advanced Computer Science & Engineering
- **The baseline is V5** — 44 sections, 1,000 slots/week, 51 room clashes, 0 faculty clashes
- **The goal is V6 AUTO** — 0 hard violations, generated in < 5 minutes
- **Every UI decision** goes through `ui-ux-pro-max` first
- **Every solver output** must be validated before saving to DB
- **Every commit** follows the Conventional Commits format from `AGENTS.md` Section 2.3
- **Read AGENTS.md** whenever you are unsure what role you should be playing

Now start with Step 1. Good luck.
