# VFSTR ACSE Automated Timetable Scheduler

> Production-grade, constraint-solving timetable automation platform for Vignan's Foundation for Science, Technology and Research (Vadlamudi, Guntur) - ACSE Department.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black?logo=next.js)](https://nextjs.org)
[![OR-Tools](https://img.shields.io/badge/OR--Tools-CP--SAT-orange)](https://developers.google.com/optimization)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://docs.docker.com/compose)

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [What We Built](#what-we-built)
3. [Architecture Overview](#architecture-overview)
4. [Tech Stack](#tech-stack)
5. [Project Structure](#project-structure)
6. [Database Schema](#database-schema)
7. [Feature Index](#feature-index)
8. [Hard and Soft Constraints](#hard-and-soft-constraints)
9. [API Reference](#api-reference)
10. [Constraint Engine Details](#constraint-engine-details)
11. [Domain Knowledge](#domain-knowledge)
12. [Docker and Infrastructure](#docker-and-infrastructure)
13. [Environment Setup](#environment-setup)
14. [Running the Project](#running-the-project)
15. [Test Suite](#test-suite)
16. [Timetable Versions](#timetable-versions)

---

## Problem Statement

The ACSE Department timetable was manually assembled in Excel. Version 5 (current baseline):

| Metric | Value |
|---|---|
| Total slots | **1,000** |
| Sections | **44-60** (multi-year/multi-branch) |
| Faculty | **~80-160** |
| Rooms | **35-71** |
| Hard violations (V5) | **51 room clashes** |
| Revision cycles | **5 versions in 5 days** |

The goal: replace this error-prone manual process with an automated, constraint-satisfying, production-ready web platform.

---

## What We Built

A full-stack SaaS platform that:

- **Parses** real VFSTR Excel timetable workbooks (multi-sheet, complex structure)
- **Detects** all 51 room clashes and 0 faculty clashes in the V5 baseline
- **Generates** clash-free schedules using Google OR-Tools CP-SAT
- **Repairs** conflicts autonomously via a multi-agent system with consensus voting
- **Exports** timetables to Excel (section tabs, faculty legend, merged lab cells) and PDF
- **Runs** fully containerized via Docker Compose with zero-trust Nginx gateway

---

## Architecture Overview

```
Browser (Next.js 14)
      |  HTTP / WebSocket
      v
  Nginx (Port 80)  <-- Rate limiting, gzip, zero-trust single entrypoint
      |
  FastAPI (Port 8000)
  API v1 Router -> 16 route modules
  Services -> Business Logic
  SQLAlchemy Async ORM -> PostgreSQL
  Celery -> async solver tasks via Redis
      |
  Solver Layer
  - CP-SAT (OR-Tools 9.11)
  - Genetic Algorithm
  - Conflict Checker (single-pass O(n))
  - Incremental Validator (O(1) swap check)
```

**Layered rule**: UI -> API -> Services -> Solver -> DB.
Solver logic never bleeds into routes. DB queries never appear in React components.

---

## Tech Stack

### Backend

| Package | Version | Role |
|---|---|---|
| FastAPI | 0.115.0 | Async REST API + WebSocket |
| SQLAlchemy asyncio | 2.0.35 | ORM with async session |
| asyncpg | 0.29.0 | PostgreSQL async driver |
| OR-Tools | 9.11 | CP-SAT constraint solver |
| Celery + Redis | 5.4.0 | Async task queue for solver |
| Pydantic | 2.9.0 | Schema validation |
| openpyxl | 3.1.5 | Excel parsing and export |
| pandas | 2.2.3 | Data processing |
| reportlab | 4.0+ | PDF generation |
| psutil | 6.0+ | System telemetry |
| aiosqlite | 0.19+ | SQLite fallback for tests |
| ruff | 0.6.9 | Linting |
| mypy | 1.11.0 | Type checking |
| pytest-asyncio | 0.24.0 | Async test runner |

### Frontend

| Package | Version | Role |
|---|---|---|
| Next.js | 14.2 | App Router SSR/CSR |
| React | 18.3 | Component framework |
| TanStack Query | 5.59 | Server state management |
| Zustand | 4.5.5 | Client state store |
| Axios | 1.7.7 | HTTP client |
| Recharts | 2.12.7 | Analytics charts |
| Lucide React | 0.446 | Icon system |
| Tailwind CSS | 3.4 | Utility styling |
| Vitest | 2.1.9 | Unit testing |
| Playwright | 1.61.1 | E2E testing |
| TypeScript | 5.6.2 | Type safety |

### Infrastructure

| Service | Image | Role |
|---|---|---|
| PostgreSQL | postgres:16-alpine | Primary DB |
| Redis | redis:7-alpine | Celery broker + cache |
| Nginx | nginx:alpine | Reverse proxy, rate limiting |
| Celery Worker | backend image | Async solver tasks |

---

## Project Structure

```
vfstr-timetable-scheduler/
|-- AGENTS.md                          <- AI agent governance rules
|-- README.md                          <- This file
|-- Makefile                           <- dev shortcuts (up/down/seed/test/validate)
|-- docker-compose.yml                 <- Dev compose (6 services)
|-- docker-compose.prod.yml            <- Production compose
|-- nginx.conf                         <- Rate-limiting, gzip, WebSocket proxy
|-- .env / .env.example                <- Environment variables
|
|-- backend/
|   |-- main.py                        <- FastAPI app entry + lifespan startup
|   |-- requirements.txt
|   |-- Dockerfile
|   |-- seed.py                        <- CLI seed utility
|   |-- remediate_data_integrity.py    <- Data integrity repair script
|   |
|   |-- app/
|   |   |-- api/v1/                    <- Route handlers ONLY (thin controllers)
|   |   |   |-- router.py              <- Central router (16 modules)
|   |   |   |-- agent.py               <- Autonomous agent API (508 LOC)
|   |   |   |-- configure.py           <- CRUD: faculty, rooms, subjects, sections
|   |   |   |-- export.py              <- Excel / PDF / JSON exports
|   |   |   |-- import_excel.py        <- Secure file upload + parsing
|   |   |   |-- solve.py               <- CP-SAT solver trigger
|   |   |   |-- wizard_solve.py        <- Wizard-driven generation (260 LOC)
|   |   |   |-- wizard_defaults.py     <- Wizard seed data
|   |   |   |-- timetable.py           <- Read, validate-move, faculty/room views
|   |   |   |-- testing.py             <- Testing lab benchmarks (222 LOC)
|   |   |   |-- telemetry.py           <- System health metrics
|   |   |   |-- validate.py            <- Full constraint validation
|   |   |   |-- sections.py
|   |   |   |-- faculty.py
|   |   |   `-- rooms.py
|   |   |
|   |   |-- models/                    <- SQLAlchemy ORM (19 model files)
|   |   |-- schemas/                   <- Pydantic request/response schemas
|   |   |-- services/                  <- Business logic (19 service files)
|   |   |   |-- agent_service.py       <- Agent session + NLP command parsing (693 LOC)
|   |   |   |-- multi_agent_scheduler.py  <- 4-agent audit system (684 LOC)
|   |   |   |-- multi_agent_consensus.py  <- 3-role consensus voting (171 LOC)
|   |   |   |-- tool_registry.py       <- 19 read tools + write tools (524 LOC)
|   |   |   |-- write_tools.py         <- Mutations gated by ConflictChecker (481 LOC)
|   |   |   |-- mission_simulator.py   <- Campus disruption simulation (183 LOC)
|   |   |   |-- export_service.py      <- Excel + PDF generation (674 LOC)
|   |   |   |-- timetable_service.py   <- Core timetable queries + validation
|   |   |   |-- seed_service.py        <- Auto-seed from V5 Excel on first boot
|   |   |   |-- configure_service.py   <- CRUD business logic
|   |   |   |-- solve_service.py       <- Solver orchestration
|   |   |   |-- wizard_defaults_service.py <- Dynamic seed data for wizard
|   |   |   |-- preflight_analyzer.py  <- Pre-solve capacity/workload diagnostic
|   |   |   `-- validate_service.py    <- Constraint validation service
|   |   |
|   |   `-- core/
|   |       |-- config.py              <- Settings (pydantic-settings, .env)
|   |       |-- database.py            <- Async engine + session factory
|   |       |-- auth.py                <- JWT authentication
|   |       |-- exceptions.py          <- RFC 7807 problem+json handler
|   |       |-- migrations.py          <- Alembic migration helper
|   |       |-- seed_cache.py          <- In-memory seed cache (fast wizard)
|   |       `-- seed_full_database.py  <- Complete DB seeding from V5 Excel
|   |
|   |-- solver/
|   |   |-- constraints.py             <- HC-01 to HC-13 + SC-01 to SC-10
|   |   |-- csat_solver.py             <- OR-Tools CP-SAT solver (687 LOC)
|   |   |-- conflict_checker.py        <- High-performance clash detector (389 LOC)
|   |   |-- genetic_algorithm.py       <- GA solver (alternative algorithm)
|   |   |-- fitness.py                 <- GA fitness function
|   |   |-- incremental_validator.py   <- O(1) drag-drop swap validator
|   |   `-- diagnostics.py             <- Solver diagnostics + reporting
|   |
|   |-- parser/
|   |   |-- excel_parser.py            <- Multi-sheet VFSTR Excel parser (20K bytes)
|   |   |-- excel_exporter.py          <- Excel workbook exporter (24K bytes)
|   |   `-- normalizer.py              <- Faculty/subject name normalization
|   |
|   |-- tasks/
|   |   |-- celery_app.py              <- Celery app factory
|   |   `-- solver_tasks.py            <- Async solver Celery tasks
|   |
|   `-- tests/                         <- 35 test files
|       |-- conftest.py
|       |-- test_constraints.py
|       |-- test_solver.py
|       |-- test_parser.py
|       |-- test_e2e_timetable_suite.py (34K bytes)
|       |-- test_multi_agent_scheduler.py
|       |-- test_agent_phase1_models.py
|       |-- test_agent_phase2_consensus_approval.py
|       |-- test_agent_phase3_tools_quality.py
|       |-- test_agent_phase4_fallback_diagnostics.py
|       |-- test_agent_phase5_mission_multicycle.py
|       |-- test_agent_phase6_celery_schema_audit.py
|       |-- test_agent_phase7_nlp_notifications.py
|       |-- test_agent_phase8_security_priority.py
|       |-- test_agent_phase9_production_safeguards.py
|       |-- test_agent_phase10_resilience_locks.py
|       |-- test_agent_phase11_production_perfection.py
|       `-- ... (18 more test files)
|
|-- frontend/
|   |-- src/
|   |   |-- app/                       <- Next.js App Router pages
|   |   |   |-- page.tsx               <- Dashboard (23K bytes)
|   |   |   |-- schedule/page.tsx      <- Timetable Viewer (69K bytes, 1418 lines)
|   |   |   |-- import/page.tsx        <- Excel Import
|   |   |   |-- configure/page.tsx     <- Master Data CRUD (22K bytes)
|   |   |   |-- export/page.tsx        <- Export Hub (33K bytes)
|   |   |   |-- agent/page.tsx         <- Agent Console (16K bytes)
|   |   |   |-- ai-scheduler/page.tsx  <- AI Scheduler / Wizard
|   |   |   |-- testing/page.tsx       <- Testing Lab (41K bytes, 859 lines)
|   |   |   |-- settings/page.tsx      <- Settings + Telemetry (29K bytes)
|   |   |   |-- layout.tsx             <- Root layout + dark mode init
|   |   |   |-- error.tsx
|   |   |   |-- loading.tsx
|   |   |   `-- not-found.tsx
|   |   |
|   |   |-- components/
|   |   |   |-- timetable/
|   |   |   |   |-- TimetableGrid.tsx  <- 6x8 grid (drag-drop, clash highlight, spans)
|   |   |   |   `-- SlotEditorModal.tsx <- Inline slot editing modal
|   |   |   |-- agent/
|   |   |   |   |-- MultiAgentSynthesisWorkspace.tsx (33K bytes, 755 lines)
|   |   |   |   |-- DecisionTrace.tsx  <- Agent decision log viewer
|   |   |   |   |-- DiffView.tsx       <- Before/after timetable diff
|   |   |   |   `-- MissionSimulator.tsx <- Campus disruption simulator UI
|   |   |   |-- wizard/
|   |   |   |   `-- ScheduleSetupWizard.tsx (35K bytes, 701 lines)
|   |   |   |-- analytics/
|   |   |   |   |-- BuildingBlockChart.tsx
|   |   |   |   |-- ClashAnalyticsChart.tsx
|   |   |   |   |-- FacultyWorkloadChart.tsx
|   |   |   |   `-- RoomUtilizationHeatmap.tsx
|   |   |   |-- solver/SolverProgress.tsx
|   |   |   |-- layout/
|   |   |   |   |-- AppShell.tsx
|   |   |   |   |-- Sidebar.tsx
|   |   |   |   `-- TopBar.tsx
|   |   |   |-- faculty/FacultyMasterProfile.tsx
|   |   |   |-- rooms/VenueMasterProfile.tsx
|   |   |   `-- subjects/CurriculumMasterProfile.tsx
|   |   |
|   |   |-- hooks/
|   |   |   |-- useSolver.ts           <- WebSocket solver progress state
|   |   |   |-- useTimetable.ts        <- Timetable fetch + cache
|   |   |   |-- useTimetableQuery.ts   <- TanStack Query wrapper
|   |   |   |-- useAgentStream.ts      <- Agent WebSocket stream
|   |   |   |-- useTheme.ts            <- Dark/light mode toggle
|   |   |   `-- useToast.ts            <- Toast notification system
|   |   |
|   |   |-- lib/
|   |   |   |-- api.ts                 <- Axios instance + all API call functions
|   |   |   |-- types.ts               <- TypeScript types (mirrors Pydantic schemas)
|   |   |   `-- store.ts               <- Zustand global store
|   |   |
|   |   `-- design-system/             <- CSS tokens (single source of truth)
|   |
|   `-- e2e/                           <- Playwright E2E tests
|
|-- data/
|   |-- seed/                          <- JSON seed data from V5
|   `-- test_outputs/                  <- Solver test output Excel files
|
|-- docs/
|   |-- system_architecture.md
|   |-- v2_architecture_blueprint.md
|   `-- vfstr_academic_regulations_spec.md
|
`-- time_table/                        <- Source Excel workbooks (V3, V5, 4th Year)
```

---

## Database Schema

**15 core tables** + agent/audit tables:

| Table | Purpose |
|---|---|
| `departments` | Department master |
| `branches` | Branch master (AIML, CS, DS, CSBS, IOT) |
| `academic_years` | Academic year periods |
| `faculty` | Faculty master (name, designation, max hours) |
| `rooms` | Room master (code, type, capacity) |
| `subjects` | Subject master (code, L/T/P credits, room type) |
| `sections` | Section master (name, year, branch, strength) |
| `section_subjects` | Section-Subject-Faculty assignments |
| `multi_faculty_assignments` | Co-faculty for shared classes |
| `time_slots` | Day x Period grid (48 slots/week) |
| `timetable_versions` | V1-V5 + solver-generated versions |
| `timetable_entries` | Individual slot allocations |
| `timetable_entry_faculty` | Per-entry faculty junction table |
| `solver_runs` | Solver execution records |
| `constraint_definitions` | HC/SC constraint registry |
| `agent_sessions` | Autonomous agent session state |
| `agent_events` | Agent event log |
| `agent_actions` | Tool execution audit trail |
| `agent_decisions` | Agent decision trace |
| `approval_requests` | Human-in-the-loop approval gate |
| `audit_log` | Change audit log |
| `clash_reports` | Persisted clash report snapshots |

Key model features:
- `timetable_entries.span_periods` (1-4): consecutive lab block support
- `timetable_entries.is_global_sync`: cohort-wide slot flag
- Dual FK + raw_subject_text/raw_room_text fields for import compatibility
- DB indexes: `idx_tt_entries_room_slot`, `idx_tt_entries_section_slot`
- Unique constraint: one entry per (version, section, time_slot)

---

## Feature Index

### 1. Dashboard (`/`)

Live stats pulled from `/api/v1/telemetry/metrics`:

| Sub-feature | Detail |
|---|---|
| Live KPI cards | Sections, Faculty, Rooms, Total slots |
| Clash summary card | Hard violations with colour-coded badge |
| Version timeline | V1 to V5 cards showing date and violation count |
| Dataset selector | Switch between 4th_year, multi_branch_e2e, v5_baseline |
| BuildingBlockChart | Room utilization by building/floor |
| ClashAnalyticsChart | Clash distribution by type |
| Quick action links | Import, View Schedule, Export, Configure |
| Feature overview grid | CP-SAT Engine, Multi-Agent AI, Conflict Detection, Export |

---

### 2. Excel Import Pipeline (`/import`)

**API:** `POST /api/v1/import/excel`

| Sub-feature | Detail |
|---|---|
| File validation | Extension (.xlsx/.xls), 15 MB limit, byte-level OOXML magic number check |
| Filename sanitisation | Path-traversal-safe rename, truncated to 100 chars |
| Multi-sheet parsing | ExcelTimetableParser reads all section tabs in V3/V5 workbooks |
| Faculty normalisation | normalize_faculty_name() collapses spelling variants into canonical keys |
| Clash detection on import | ConflictChecker.detect() runs immediately after parse |
| Section extraction | Parses class teacher name + phone from cell headers |
| Import summary | Returns sections_found, total_slots, room_clashes, faculty_clashes |
| Baseline validation | V5 must produce exactly 51 room clashes, 0 faculty clashes |

---

### 3. Timetable Viewer and Schedule Page (`/schedule`)

1,418 lines of timetable viewer:

| Sub-feature | Detail |
|---|---|
| Section tree sidebar | Year -> Branch -> Section navigation (collapsible) |
| TimetableGrid | 6-column (MON-SAT) x 8-row (P1-P8) grid with break/lunch rows |
| Slot cell anatomy | Subject code, room code, faculty name, colour by type |
| Slot type colour coding | Lecture=blue, Lab=purple, Tutorial=green, Library=amber, Clash=red |
| Clash highlighting | Red left-border + red background on clash cells |
| Lab cell spanning | span_periods support for 2-3 consecutive lab blocks |
| Drag-and-drop swap | POST /api/v1/timetable/validate-move (O(1) validation < 5ms) |
| Inline slot editor | SlotEditorModal - edit subject, room, faculty for any slot |
| Section compare mode | Side-by-side two-section comparison |
| Faculty view | Filter timetable by faculty member |
| Room view | Filter timetable by room code |
| Version selector | Switch between V3, V5, solver-generated versions |
| Cohort view | View all sections in a cohort simultaneously |
| Solver trigger | Inline Run Solver button with live progress |
| Export from view | Per-section PDF download |
| Fullscreen mode | Toggle fullscreen grid |
| Clash panel | Side panel showing clash details for selected section |

---

### 4. CP-SAT Solver Engine

**File:** `backend/solver/csat_solver.py` (687 LOC)

| Sub-feature | Detail |
|---|---|
| Algorithm | Google OR-Tools CP-SAT (constraint programming) |
| Hard constraint enforcement | HC-01 through HC-13 |
| Soft constraint optimization | Minimises penalty-weighted objective function |
| Room assignment | Matches room type to subject type |
| GPU lab preference | DL, CV, MLOP subjects prefer AFTF-12/13/14 |
| Virtual library room | VIRTUAL_LIBRARY room for LIBRARY/IIC/SL_EL slots |
| Self-directed slot types | LIBRARY, IIC, SL/EL, OE, CRT, MINORS/HONORS without room clash |
| Faculty uniqueness | Double-booking enforced via canonical identity key |
| Break guard | Periods 2->3 and 5->6 transitions blocked |
| Lab consecutiveness | Lab sessions must use consecutive periods (HC-08) |
| Minors/Honors slots | Restricted to WED/THU P7-P8 (HC-09) |
| 4th Year SL/EL | Restricted to P1-P2 MON-SAT (HC-10) |
| Live progress callback | LiveSolutionCallback streams solutions via WebSocket |
| Configurable timeout | Default 120s, max 8 workers |
| SolverConfig schema | Pydantic model for algorithm, scope, timeout, penalty weights |
| Preflight barrier | PreflightAnalyzer checks capacity/workload before launching |

---

### 5. Multi-Agent Scheduling System

**File:** `backend/app/services/multi_agent_scheduler.py` (684 LOC)

Four-agent specialised audit pipeline before any solver output is committed:

| Agent | Role | Veto Power |
|---|---|---|
| SectionCurriculumAgent | Section weekly quotas, library hours, cohort block protection | Hard veto if deviation >= 5 |
| FacultyWorkloadAgent | Faculty hour limits by rank (Prof=12h, Assoc=14h, Asst=16h) | Soft penalty |
| RoomCompatibilityAgent | Room type match, capacity, GPU lab preferences | Hard veto on type mismatch |
| HardConstraintAgent | HC-01/02/03/07 detection | VETO power (any violation = reject) |

Consensus voting sub-features:

| Sub-feature | Detail |
|---|---|
| APPROVE / REJECT votes | Each agent casts a typed vote with rationale |
| Veto power | HardConstraintAgent REJECT blocks any publish |
| AgentCritique objects | rule_id, severity, message, suggested_action, affected_slot |
| AgentVote objects | agent_name, vote, has_veto_power, violations_detected, rationale, metrics |
| Consensus threshold | Requires 3/4 APPROVE + zero hard vetoes |
| Multi-cycle repair | Agent iterates repair -> re-audit up to N cycles |

---

### 6. Autonomous Agent Console (`/agent`)

| Sub-feature | Detail |
|---|---|
| Session creation | POST /api/v1/agent/sessions with goal + priority list |
| WebSocket stream | Real-time event stream via useAgentStream hook |
| Decision trace | Chronological log of agent decisions with risk levels |
| Diff view | Before/after timetable comparison (original vs repaired) |
| Mission simulator UI | Trigger campus disruption scenarios |
| Multi-agent workspace | Full 755-line agent orchestration UI |
| Repair suggestions | POST /api/v1/agent/sessions/{id}/repair-suggestion |
| Consensus voting display | Per-agent vote cards with rationale |
| NLP command parser | Parse natural language into disruption triggers |
| Room failure simulation | POST /api/v1/agent/simulate-room-failure (1s cooldown) |
| Data integrity health | GET /api/v1/agent/health/data-integrity |
| Write tools | Every mutation gated by ConflictChecker, rolled back if violations increase |
| Approval gate | High-risk repairs require human approval before commit |

MissionSimulator scenarios:

- `room_failure` - Emergency room maintenance
- `gpu_lab_failure` - GPU lab outage (AFTF-12/13/14)
- `faculty_absence` - Faculty unavailable
- `capacity_surge` - Student count overflow
- `new_class_addition` - New section added mid-semester
- `priority_reroute` - Priority re-scheduling request
- `constraint_adjustment` / `constraint_modification` - Policy change

---

### 7. Wizard Solver (`/ai-scheduler`)

**API:** `POST /api/v1/solve/generate-from-wizard`

| Sub-feature | Detail |
|---|---|
| Section selector | Filter by Year (II/III/IV) and Branch (AIML/CS/DS/CSBS/IOT) |
| Course assignment builder | Per-subject: faculty, type, weekly hours, continuous slots |
| Wizard defaults API | GET /api/v1/configure/wizard-defaults |
| Seed cache | In-memory cache maps (section_norm, subject_norm) -> faculty pool |
| CP-SAT invocation | Directly calls CPSATSolver with wizard-derived section subjects |
| Real-time preview | Solver result rendered in TimetableGrid inline |
| Hard constraints display | HC-01 through HC-10 shown as badges |
| Algorithm toggle | CP-SAT or Genetic Algorithm selector |
| Config panel | Timeout, penalty weights (collapsible) |
| Success to export link | After generation, link to Export page |

---

### 8. Configure Page - Master Data CRUD (`/configure`)

Four-tab master data panel backed by ConfigureService:

**Faculty Tab:**

| Sub-feature | Detail |
|---|---|
| List / Search | Name search with designation filter |
| Create | Employee ID, designation, max weekly hours, contact |
| Update | Edit workload caps, rank, availability |
| Delete | Remove from master records |
| CSV bulk import | POST /api/v1/configure/faculty/csv-import |
| Faculty workload chart | Current vs max hours bar chart |
| FacultyMasterProfile | Detailed profile panel component |

**Rooms Tab:**

| Sub-feature | Detail |
|---|---|
| List / Search | Code, type (classroom/computer_lab/gpu_lab/project_lab), capacity |
| Create / Update / Delete | Full CRUD |
| Room type filter | Lab vs classroom segregation |
| VenueMasterProfile | Detailed venue panel |
| Building block chart | Room utilization heatmap |

**Subjects Tab:**

| Sub-feature | Detail |
|---|---|
| List | Code, title, L/T/P credits, room type requirement |
| Create / Update / Delete | Full CRUD |
| CurriculumMasterProfile | Detailed curriculum panel |

**Sections Tab:**

| Sub-feature | Detail |
|---|---|
| List with search | Paginated (10 per page) |
| Year/Branch metadata | Year level, branch, student strength |
| Create / Update / Delete | Full CRUD |
| Section subject mapping | POST /api/v1/configure/section-subjects |

---

### 9. Export Engine (`/export`)

**Service:** `backend/app/services/export_service.py` (674 LOC)
**Exporter:** `backend/parser/excel_exporter.py` (24K bytes)

| Export Type | API Endpoint | Detail |
|---|---|---|
| Full Excel | POST /api/v1/export/excel | All sections, section tabs, faculty legend, merged lab cells |
| Cohort Excel | POST /api/v1/export/excel/cohort/{key} | II_AIML, III_AIML, IV_AIML, CS_DS, CSBS_IOT, SPECIAL_PG |
| Minors/Honors Excel | POST /api/v1/export/excel/minors-honors | Global Minors/Honors master sheet |
| Section PDFs | POST /api/v1/export/pdf/sections | All sections, A4 printable via ReportLab |
| Faculty PDFs | POST /api/v1/export/pdf/faculty | All faculty weekly schedules |
| Single Faculty PDF | GET /api/v1/export/pdf/faculty/{id} | One faculty member schedule |
| JSON export | Frontend button | Raw timetable JSON |
| Room Utilization | Frontend button | Room occupancy statistics |
| SmartClass sync | POST /api/v1/timetable/sync-master | Push to SmartClass digital display |

All exports support `?version_id=5` (or 3) to export any historical version.

---

### 10. Testing Lab (`/testing`)

859-line testing page:

| Sub-feature | Detail |
|---|---|
| Dataset selector | 4th_year, multi_branch_e2e, v5_baseline, v5_ground_truth, e2e_test |
| Parse and display | GET /api/v1/testing/tested-data?dataset=X |
| TimetableGrid render | Renders selected section in grid component |
| Class teacher display | Name + phone parsed from Excel cell header |
| Clash detection report | Room, faculty, student clashes with details |
| Filter by year/section | Search and filter parsed sections |
| Export from lab | Download parsed data as Excel |
| Constraint badge list | HC badges displayed per section |
| Co-faculty display | Multi-faculty slot cards with phone numbers |

---

### 11. Settings and Telemetry (`/settings`)

Four-tab settings panel:

**Profile Tab:** Name, Employee ID, Designation, Department, Email, Phone, Office Location

**Academic Policy Tab:** Academic Year, Max Professor hours (12), Max Assoc. Prof hours (14), Max Asst. Prof hours (16), Max daily classes, max section slots per week

**Solver Engine Tab:** Algorithm (CP-SAT default), Timeout (120s), Search workers (8), Enable preflight barrier toggle, Hard penalty weight (10,000)

**Telemetry Tab** (live from GET /api/v1/telemetry/metrics):

| Metric | Detail |
|---|---|
| System | CPU %, Memory MB, Thread count, OS platform |
| Services | PostgreSQL, Redis, Celery workers, BTree-GiST extension |
| Database | 15 tables, Total sections, Faculty, Rooms, Entries |
| Containers | Status + uptime for all 5 Docker services |
| Python version | Runtime info |

---

### 12. AI Scheduler Page (`/ai-scheduler`)

Entry point to the **ScheduleSetupWizard** - a multi-step guided flow to generate a new clash-free timetable from scratch without needing to import an existing Excel file.

---

## Hard and Soft Constraints

### Hard Constraints (HC) - Never Violated in Valid Output

| ID | Constraint | Relaxable |
|---|---|---|
| HC-01 | Room conflict - no two sections in same room at same time | NEVER |
| HC-02 | Faculty double-booking - faculty in two places at once | NEVER |
| HC-03 | Student conflict - same section scheduled twice in one slot | NEVER |
| HC-04 | Subject weekly frequency - L/T/P hours per week match curriculum | NEVER |
| HC-05 | Room capacity - section student count <= room capacity | Last resort |
| HC-06 | Room type match - lab subjects must be in lab rooms | Last resort |
| HC-07 | Break/Lunch blocking - P2->P3 and P5->P6 transitions protected | NEVER |
| HC-08 | Lab consecutiveness - lab sessions span 2-3 consecutive periods | Relax for 3h if no room |
| HC-09 | Minors/Honors slot protection - WED/THU P7-P8 only | Cohort block only |
| HC-10 | 4th Year SL/EL block - P1-P2 MON-SAT, SAT P6-P8 afternoon | Block only |
| HC-11 | Section weekly quota - 2nd Yr: 36, 3rd Yr: 45, 4th Yr: 39 slots | |
| HC-12 | Library allocation - 1 Library hour for 2nd Year, 0 for 3rd/4th | |
| HC-13 | Valid lab start periods - {1, 3, 4, 6, 7} only | |

### Soft Constraints (SC) - Optimized, Not Enforced

| ID | Constraint | Default Penalty |
|---|---|---|
| SC-01 | Faculty preference (morning vs afternoon) | 50 |
| SC-02 | Minimize faculty travel between buildings | 30 |
| SC-03 | Spread subjects evenly across week | 10 |
| SC-04 | Avoid isolated single-period classes | 5 |
| SC-05 | Prefer GPU labs for DL/CV/MLOP subjects | 20 |
| SC-06 | Balance workload across days | 5 |
| SC-07 | Keep co-taught sections in compatible rooms | 100 |
| SC-08 | Minimize room switches for same section | 15 |
| SC-09 | Consecutive class preference for faculty | 10 |
| SC-10 | Compact scheduling (minimize gaps) | 5 |

---

## API Reference

All endpoints prefixed with `/api/v1`.

### Timetable

| Method | Endpoint | Description |
|---|---|---|
| GET | /timetable | Get timetable for version + optional section filter |
| GET | /timetable/versions | List all timetable versions |
| GET | /timetable/version/{version_id} | Get specific version |
| GET | /timetable/faculty/{faculty_id} | Faculty weekly timetable |
| GET | /timetable/room/{room_code} | Room weekly schedule |
| POST | /timetable/validate-move | O(1) drag-drop swap validation |
| POST | /timetable/sync-master | SmartClass digital display sync |

### Import

| Method | Endpoint | Description |
|---|---|---|
| POST | /import/excel | Upload Excel, parse, clash-detect |

### Solver

| Method | Endpoint | Description |
|---|---|---|
| POST | /solve | Trigger CP-SAT solver (Celery async) |
| POST | /solve/generate-from-wizard | Wizard-driven generation |
| GET | /solve/{run_id}/stream | WebSocket solver progress |

### Export

| Method | Endpoint | Description |
|---|---|---|
| POST | /export/excel | Full department Excel workbook |
| POST | /export/excel/cohort/{key} | Cohort-specific Excel |
| POST | /export/excel/minors-honors | Minors/Honors master sheet |
| GET | /export/excel/cohorts | List cohort group definitions |
| POST | /export/pdf | All section PDFs |
| POST | /export/pdf/faculty | All faculty PDFs |
| GET | /export/pdf/faculty/{id} | Single faculty PDF |

### Configure

| Method | Endpoint | Description |
|---|---|---|
| GET/POST | /configure/faculty | List / Create faculty |
| PUT/DELETE | /configure/faculty/{id} | Update / Delete faculty |
| POST | /configure/faculty/csv-import | Bulk CSV import |
| GET/POST | /configure/rooms | List / Create rooms |
| PUT/DELETE | /configure/rooms/{id} | Update / Delete room |
| GET/POST | /configure/subjects | List / Create subjects |
| PUT/DELETE | /configure/subjects/{id} | Update / Delete subject |
| GET/POST | /configure/sections | List / Create sections |
| PUT/DELETE | /configure/sections/{id} | Update / Delete section |
| POST | /configure/section-subjects | Map subjects to section |
| GET | /configure/wizard-defaults | Wizard seed data |

### Agent

| Method | Endpoint | Description |
|---|---|---|
| POST | /agent/sessions | Create agent session |
| GET | /agent/sessions/{id} | Get session state |
| POST | /agent/sessions/{id}/repair-suggestion | Generate repair |
| POST | /agent/sessions/{id}/consensus | Multi-agent consensus vote |
| POST | /agent/simulate-room-failure | Trigger room disruption |
| WS | /agent/sessions/{id}/stream | Real-time event stream |
| GET | /agent/health/data-integrity | FK vs raw-text audit |

### Utility

| Method | Endpoint | Description |
|---|---|---|
| GET | /validate | Full hard constraint validation |
| GET | /testing/tested-data | Parse + clash-check a dataset |
| GET | /telemetry/metrics | System + DB + Docker health |
| GET | /sections | List sections |
| GET | /faculty | List faculty |
| GET | /rooms | List rooms |
| GET | /health | FastAPI health check |

---

## Constraint Engine Details

### ConflictChecker - High-Performance Clash Detector

Location: `backend/solver/conflict_checker.py`

- **Single-pass indexing** into room_map, faculty_map, section_map buckets
- **Faculty identity key**: collapses name variants (e.g. "DR. P. KALPANA" == "Dr.P.Kalpana")
- **Joint-section transparency**: shared teaching slots flagged as is_violation=False
- **Ignored room codes**: LIBRARY, BREAK, LUNCH, SL/EL, MINORS/HONORS, ONLINE - no physical conflict
- **Returns ClashReport**: room_clashes, physical_room_clashes, joint_section_slots, faculty_clashes, student_clashes, break_clashes, total_hard_violations
- **Baseline**: V5 -> 51 room clashes, 0 faculty clashes (always verified in test suite)

### ScheduleIndexStore - O(1) Incremental Validator

Location: `backend/solver/incremental_validator.py`

- Builds inverted hash index on (day, period, room/fac/sec) -> entry
- validate_move() checks a proposed swap without CP-SAT re-solve
- Supports DragDropSwapRequest schema
- Enforced in POST /api/v1/timetable/validate-move

---

## Domain Knowledge

### Period to Time Mapping

| Period | Time |
|---|---|
| P1 | 08:15 - 09:05 |
| P2 | 09:05 - 09:55 |
| BREAK | 09:55 - 10:10 |
| P3 | 10:10 - 11:00 |
| P4 | 11:00 - 11:50 |
| P5 | 11:50 - 12:40 |
| LUNCH | 12:40 - 13:40 |
| P6 | 13:40 - 14:30 |
| P7 | 14:30 - 15:20 |
| P8 | 15:20 - 16:05 |

Days: MON, TUE, WED, THU, FRI, SAT (6-day week)

### Room Types

| Type | Codes |
|---|---|
| Computer Labs | 604, 605, 606, 611, 612, 615, 616, 617 |
| GPU Labs (DL/CV/MLOP preferred) | AFTF-12, AFTF-13, AFTF-14 |
| Project Rooms | AFF-09, AFF-10 |
| Classrooms | 601-603, 607-610, 613-614, 618-619, 215-218, 514-A, 514-B, 518, 401, 402, 418, 501 |

### Faculty Workload Limits

| Designation | Max Hours/Week |
|---|---|
| Professor | 12 |
| Associate Professor | 14 |
| Assistant Professor | 16 |

### Subject Code Conventions

| Suffix | Type |
|---|---|
| DS | Lecture |
| DS(T) | Tutorial |
| DS(P) | Practical/Lab |
| DS(T&P) | Combined Tutorial + Practical |

### Section Weekly Quotas

| Year | Teaching Slots | Library | IIC |
|---|---|---|---|
| 2nd Year | 36 | 1 | 1 |
| 3rd Year | 45 | 0 | 0 |
| 4th Year | 39 | 0 | 0 |

---

## Docker and Infrastructure

### Services

```yaml
postgres:   postgres:16-alpine   # Internal only (no host port)
redis:      redis:7-alpine        # Internal only (no host port)
backend:    ./backend             # Exposed on :8000 internally
celery:     ./backend             # Worker: concurrency=2, max-tasks=100
frontend:   ./frontend            # Exposed on :3000 internally
nginx:      nginx:alpine          # Public entrypoint on :80
```

### Nginx Features

- Rate limiting: 100 req/min for API, 1 req/min for solver endpoint
- Gzip compression (level 6, all text/JSON/JS types)
- WebSocket proxy (Upgrade / Connection headers)
- JSON-structured access logging
- Docker internal DNS resolver (127.0.0.11)
- server_tokens off (security hardening)
- Zero-trust: no service exposes host ports except Nginx on :80

### Security Hardening (all containers)

- security_opt: no-new-privileges:true
- cap_drop: ALL + minimal cap_add
- tmpfs for /tmp and /var/cache/nginx
- Read-only mounts for time_table/ and data/

---

## Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Required variables
DATABASE_URL=postgresql+asyncpg://vfstr:password@localhost:5432/timetable_db
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
SECRET_KEY=<openssl rand -hex 32>

# Optional
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
SOLVER_DEFAULT_TIMEOUT=120
SOLVER_MAX_WORKERS=8
MAX_UPLOAD_SIZE_BYTES=15728640
```

---

## Running the Project

### One-command Docker start

```bash
make up           # docker compose up -d (all 6 services)
make seed         # auto-seed DB from V5 Excel
make test         # pytest backend/tests/ -v --tb=short
make validate     # Parse V5 - expect: Room clashes: 51, Faculty clashes: 0
make lint         # ruff check backend/ && npm run lint
make type-check   # mypy backend/ --strict && npm run type-check
make down         # docker compose down
make clean        # remove __pycache__ and .pytest_cache
```

### Local development (without Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev   # http://localhost:3000

# Celery worker (separate terminal)
cd backend
celery -A tasks.celery_app worker --loglevel=info
```

---

## Test Suite

**35 test files** in `backend/tests/`:

| Test File | Coverage Area |
|---|---|
| test_constraints.py | All HC/SC constraint rule functions |
| test_solver.py | CP-SAT solver end-to-end |
| test_parser.py | Excel parser: section/slot/faculty extraction |
| test_e2e_timetable_suite.py | Full pipeline E2E (34K bytes) |
| test_multi_agent_scheduler.py | 4-agent audit pipeline |
| test_multi_agent_consensus.py | 3-role consensus voting |
| test_agent_phase1_models.py | Agent DB model structure |
| test_agent_phase2_consensus_approval.py | Consensus approval gate |
| test_agent_phase3_tools_quality.py | Tool registry quality |
| test_agent_phase4_fallback_diagnostics.py | Fallback and diagnostics |
| test_agent_phase5_mission_multicycle.py | Multi-cycle mission simulation |
| test_agent_phase6_celery_schema_audit.py | Celery schema audit |
| test_agent_phase7_nlp_notifications.py | NLP command parsing |
| test_agent_phase8_security_priority.py | Security and priority gating |
| test_agent_phase9_production_safeguards.py | Production safeguards |
| test_agent_phase10_resilience_locks.py | Resilience and session locks |
| test_agent_phase11_production_perfection.py | Production perfection audit |
| test_agent_api.py | Agent REST API routes |
| test_agent_websocket.py | Agent WebSocket stream |
| test_agent_orchestrator.py | Orchestrator integration |
| test_wizard_solve.py | Wizard-driven CP-SAT generation |
| test_configure_api.py | Configure CRUD routes |
| test_layered_api.py | API layering validation |
| test_services.py | Service layer unit tests |
| test_export.py | Excel/PDF export |
| test_export_devops.py | Export DevOps checks |
| test_incremental_validator.py | O(1) swap validator |
| test_mission_simulator.py | Campus disruption scenarios |
| test_stress_5d_audit.py | 5-day stress audit |
| test_unified_creation_lifecycle.py | Full create->solve->export lifecycle |
| test_api_routes.py | All API route smoke tests |
| test_api_import.py | Import API validation |
| test_ga_solver.py | Genetic algorithm solver |
| test_solver_benchmark.py | Solver performance benchmarks |
| test_layered_api.py | Layered architecture validation |

```bash
# Run all tests
pytest backend/tests/ -v --tb=short --cov=backend --cov-report=term-missing

# Baseline validation (must output: Room clashes: 51)
python backend/parser/excel_parser.py \
  --input "time_table/ACSE TIMETABLE (V5)  - W.e.f 15-7-2026.xlsx" \
  --validate-only
```

---

## Timetable Versions

| Version | Date | Slots | Key Change | Room Clashes |
|---|---|---|---|---|
| V1 | 10-Jul-2026 | 894 | Initial release | Unknown |
| V2 | 11-Jul-2026 | ~900 | Minor slot adjustments | Unknown |
| V3 | 13-Jul-2026 | ~950 | Significant room reassignments | 64 |
| V4 | 14-Jul-2026 | ~980 | Faculty allocation fixes | Unknown |
| V5 | 15-Jul-2026 | **1,000** | Added MINORHONORS sheet | **51** |

**V5 is the ground truth.** All parser tests, baseline clash counts (51 room clashes), and slot counts (1,000) are verified against V5. The solver goal is to generate a V6 with 0 hard violations.

---

## Contributing

This project follows the agent roles and conventions defined in `AGENTS.md`. Before contributing:

1. Read `AGENTS.md` in full
2. Declare your role (ARCHITECT / DESIGNER / SOLVER / VALIDATOR)
3. Run `make test` - all tests must pass before any commit
4. Use Conventional Commits: `feat(solver): implement HC-01`
5. Leave a handoff note in your PR if handing off to another role

---

*Built for VFSTR ACSE Department - Vignan Foundation for Science, Technology and Research, Vadlamudi, Guntur, Andhra Pradesh.*
