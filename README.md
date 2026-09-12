<div align="center">

# 🎓 VFSTR ACSE Automated Timetable Scheduler

### Enterprise Constraint-Solving & Autonomous Multi-Agent Scheduling Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![OR-Tools](https://img.shields.io/badge/Google%20OR--Tools-CP--SAT-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://developers.google.com/optimization)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)

<p align="center">
  <b>Designed for Vignan's Foundation for Science, Technology & Research (VFSTR)</b><br>
  Department of Applied Computer Science & Engineering (ACSE) · Vadlamudi, Guntur
</p>

[Key Features](#-key-features) •
[System Architecture](#-system-architecture) •
[Constraints Engine](#-constraints-engine) •
[Quick Start](#-quick-start) •
[API Reference](#-api-reference) •
[Test Suite](#-test-suite--verification)

</div>

---

## 📌 The Problem

Prior to automation, the ACSE department timetable was manually drafted using complex Microsoft Excel workbooks. Due to the scale of the department, human scheduling led to recurring conflicts and unsustainable revision cycles:

| Dimension | Manual Baseline (V5) | Automated Scheduler Target |
|---|---|---|
| **Department Scale** | 44–60 Sections · ~80–160 Faculty · 35–45 Rooms | Full Department Scope Handled Concurrently |
| **Weekly Slots** | 1,000+ Teaching & Lab Slots / Week | 1,000+ Synchronized Slots |
| **Room Clashes** | **51 Room Clashes** in V5 Baseline | **0 Clashes** (Mathematically Guaranteed) |
| **Faculty Conflicts** | Double-booking risks during room swaps | **0 Double-Bookings** via Normalized Identity Keys |
| **Turnaround Time** | 5 manual revisions in 5 days | Instant Validation (<5ms) & Automated Solve (<120s) |

---

## ✨ Key Features

### 🧠 1. Dual Optimization Engines (CP-SAT & Genetic Algorithm)
- **Google OR-Tools CP-SAT**: Industrial-grade constraint programming guaranteeing zero hard constraint violations (HC-01 through HC-13).
- **Genetic Algorithm (GA)**: Heuristic population-based evolutionary solver for soft-constraint optimization and multi-objective Pareto scoring.
- **O(1) Incremental Swap Validator**: Live drag-and-drop validation in under 5ms without requiring expensive full-schedule re-computations.

### 🤖 2. Autonomous Multi-Agent Consensus & Disruption Simulator
- **4-Agent Audit Pipeline**: Specialised autonomous agents (`SectionCurriculumAgent`, `FacultyWorkloadAgent`, `RoomCompatibilityAgent`, and `HardConstraintAgent`) inspect proposed changes before publication.
- **Consensus Voting Gate**: Requires a 3/4 supermajority with strict veto power on hard violations.
- **Disaster Simulator**: Real-time stress testing for campus disruptions (emergency room failures, GPU lab outages, faculty absence, capacity surges, and priority rerouting) with built-in production rate limiters.
- **Candidate Substitute Dispatcher**: Ranks substitute instructors by fatigue levels, subject domain compatibility, and slot availability.

### 📅 3. Autonomous Examination Timetabler
- Enforces institutional exam constraints (**EC-01 to EC-05**):
  - Maximum 1 exam per student cohort per day.
  - Strict morning (09:30–12:30) and afternoon (14:00–17:00) session splits.
  - 50% examination room capacity spacing for cheating prevention.
  - Non-clashing invigilator assignment with balanced duty rotation.

### 🎨 4. Rich Interactive Timetable Viewer (`/schedule`)
- **6-Day × 8-Period Matrix**: Complete view of weekly schedules (MON–SAT, P1–P8) with break and lunch block protection.
- **Visual Clash Highlighting**: Immediate visual indicators with clash reason diagnostics.
- **Multi-Period Lab Spanning**: Horizontal cell merging for 2–3 period practical lab blocks.
- **Perspective Filters**: Switch seamlessly between Section, Faculty Member, Venue, or Cohort views.

### 📤 5. Enterprise Multi-Format Export Hub (`/export`)
- **Excel (.xlsx)**: Exact replication of institutional workbooks (individual section tabs, faculty legends, merged lab cells).
- **Printable PDFs**: Publication-ready A4 PDFs for individual sections, faculty members, and consolidated departmental booklets.
- **ZIP Bundles**: Streaming .zip archive containing all section timetable PDFs.
- **iCalendar (.ics)**: Standard RFC-5545 feeds for Google Calendar, Apple Calendar, and Outlook.
- **SmartClassroom Sync**: REST sync hook for digital signage and electronic lecterns.

### ⚙️ 6. Master Data CRUD & Guided Setup Wizard (`/configure` & `/ai-scheduler`)
- 5 comprehensive management tabs: **Faculty**, **Venues**, **Subjects**, **Sections**, and **Curriculum Assignments**.
- Step-by-step guided wizard for generating clash-free timetables from scratch with seed caching.

---

## 🏛️ System Architecture

The application is structured into strict, decoupled layers:

```
┌─────────────────────────────────────────────────────────┐
│              Browser / Client Applications              │
│       Next.js 14 App Router · React 18 · TypeScript     │
└────────────────────────────┬────────────────────────────┘
                             │ HTTP / WebSocket
┌────────────────────────────▼────────────────────────────┐
│                    Nginx Reverse Proxy                  │
│       Port 80 · Rate Limiting · Compression · SSL       │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│                   FastAPI Application                   │
│   REST API Routes (v1) · JWT Auth · RFC 7807 Errors     │
├────────────────────────────┬────────────────────────────┤
│       Service Layer        │       Multi-Agent System   │
│   Business Logic & CRUD    │   Consensus · Disruption   │
├────────────────────────────┴────────────────────────────┤
│                     Solver Engine                       │
│    OR-Tools CP-SAT · Genetic Algorithm · Clash Checker  │
└─────────────┬─────────────────────────────┬─────────────┘
              │                             │
┌─────────────▼─────────────┐ ┌─────────────▼─────────────┐
│    PostgreSQL Database    │ │    Redis & Celery Queue   │
│  Asyncpg · Relational DB  │ │  Async Workers · Pub/Sub  │
└───────────────────────────┘ └───────────────────────────┘
```

---

## ⚖️ Constraints Engine

### Hard Constraints (HC) — Zero Tolerance (100% Enforced)
| ID | Rule | Description |
|---|---|---|
| **HC-01** | Room Conflict | No two classes may occupy the same venue at the same time. |
| **HC-02** | Faculty Double-Booking | An instructor cannot be assigned to multiple sessions simultaneously. |
| **HC-03** | Section Conflict | A student cohort cannot have more than one subject scheduled in any single slot. |
| **HC-04** | Curriculum Quota | Total weekly hours for lectures, tutorials, and practicals must strictly match syllabus. |
| **HC-05** | Venue Capacity | Student strength must not exceed room seating capacity. |
| **HC-06** | Venue Type Compatibility | Practical lab subjects require designated computer, project, or GPU labs. |
| **HC-07** | Break & Lunch Guard | Morning break (09:55–10:10) and lunch (12:40–13:40) transitions remain inviolable. |
| **HC-08** | Lab Consecutiveness | Practical labs must run in contiguous 2-to-3 period blocks starting only in valid periods. |
| **HC-09** | Faculty Daily Cap | Faculty teaching limit capped at a maximum of 5 hours per day. |
| **HC-10** | Continuous Teaching Limit | Faculty cannot teach more than 3 consecutive hours without a rest break. |
| **HC-11** | Workload Limit by Rank | Professor: 12h/wk · Associate Professor: 14h/wk · Assistant Professor: 16h/wk. |
| **HC-12** | Self-Directed Slots | 2nd Year receives 1 Library & 1 IIC slot; 3rd/4th Year receive 0. |
| **HC-13** | Protected Cohort Blocks | Minors/Honors locked to WED/THU P7-P8; 4th Year SL/EL locked to MON-SAT P1-P2. |

### Soft Constraints (SC) — Optimized via Multi-Objective Scoring
- **SC-01**: Preferred teaching slots (morning vs. afternoon preferences).
- **SC-02**: Minimizing physical transit between campus building blocks.
- **SC-03**: Uniform curriculum distribution across weekdays.
- **SC-04**: Elimination of isolated, non-contiguous single-hour gaps.
- **SC-05**: Prioritizing NVIDIA GPU Labs (`AFTF-12/13/14`) for DL, CV, and GenAI courses.

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

Run the complete platform with a single command:

```bash
# 1. Clone the repository
git clone https://github.com/9046balaji/Time-Table.git
cd Time-Table

# 2. Configure environment variables
cp .env.example .env

# 3. Launch all 6 services
docker compose up -d

# 4. Access the web platform
# Frontend & API Gateway: http://localhost
# Interactive API Docs:   http://localhost/docs
```

### Option 2: Local Development

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Start PostgreSQL and Redis locally, then run:
uvicorn main:app --reload --port 8000
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev  # Running on http://localhost:3000
```

---

## 📡 API Reference Overview

The backend exposes an interactive OpenAPI specification available at `/docs` (or `/redoc`). Core endpoint groups include:

| Route Group | Base Path | Description |
|---|---|---|
| **Timetable** | `/api/v1/timetable` | Fetch weekly timetables by section, faculty, or room; transactional slot upserts & moves. |
| **Validation** | `/api/v1/validate` | On-demand constraint violation checks and baseline clash reporting. |
| **Solver** | `/api/v1/solve` | Trigger Celery async CP-SAT solves and monitor real-time solution streams. |
| **Autonomous Agent** | `/api/v1/agent` | Autonomous consensus voting, campus disruption simulations, and substitute dispatcher. |
| **Master Data** | `/api/v1/configure` | CRUD APIs for Sections, Faculty, Venues, Subjects, and Section-Subject Assignments. |
| **Export Hub** | `/api/v1/export` | Download schedules in Excel (.xlsx), PDF, ZIP bundles, or iCal (.ics). |
| **Testing Lab** | `/api/v1/testing` | Benchmark solver performance across historical baseline workbooks. |
| **System Telemetry**| `/api/v1/telemetry` | Host CPU, RAM, Docker service health, and PostgreSQL connection pool stats. |

---

## 🧪 Test Suite & Verification

The project includes an exhaustive suite of **43 automated test modules** covering unit, integration, and end-to-end scenarios:

```bash
# Run the complete test suite inside the backend container
docker exec -it vfstr_backend pytest /app/tests/ -v --tb=short

# Verify V5 baseline conflict detection (must detect exactly 51 room clashes)
docker exec -it vfstr_backend python -m parser.excel_parser --validate-only
```

**Quality Gates:**
- ✅ **104/104 Passed** across all constraint definitions, solvers, and parsers.
- ✅ **100% Pass Rate** on the 30-endpoint integration verification suite.
- ✅ **Zero Clashes** generated on full CP-SAT solver runs.

---

## 👥 Authors & Institutional Context

Developed for **Vignan's Foundation for Science, Technology & Research (VFSTR)**  
*Department of Applied Computer Science & Engineering (ACSE)*  
Vadlamudi, Guntur District, Andhra Pradesh, India — 522213.
