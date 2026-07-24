# 🎓 VFSTR ACSE Automated Timetable Scheduler
## Production Engineering Reference & Architecture Manual

> **Document Class:** Production Engineering Reference  
> **System:** VFSTR ACSE Automated Timetable Scheduler  
> **Institution:** Vignan's Foundation for Science, Technology & Research, Vadlamudi, Guntur  
> **Stack:** Next.js 14 (App Router) · FastAPI · PostgreSQL 16 · Celery · Redis · OR-Tools CP-SAT  
> **Scope:** 44 Sections · ~80 Faculty · 35 Rooms · 1,000 Slots/Week  
> **Authors:** Engineering Team — Backend, Frontend, Solver, QA  
> **Baseline:** V5 Excel (15-Jul-2026) · 51 Room Clashes Detected  
> **Build Status:** ✅ 29/29 Tests Passing · Docker Compose Production Ready

---

## Table of Contents

1. [System-Wide Architecture Topology](#1-system-wide-architecture-topology)
2. [Feature: Dashboard (`/`)](#2-feature-dashboard)
3. [Feature: Excel Import (`/import`)](#3-feature-excel-import)
4. [Feature: Master Data Configuration (`/configure`)](#4-feature-master-data-configuration)
5. [Feature: Schedule Workbench — Single Section Grid](#5-feature-schedule-workbench--single-section-grid)
6. [Feature: Schedule Workbench — Vertical Stack View](#6-feature-schedule-workbench--vertical-stack-view)
7. [Feature: Schedule Workbench — Faculty Schedules](#7-feature-schedule-workbench--faculty-schedules)
8. [Feature: Create Timetable Wizard](#8-feature-create-timetable-wizard)
9. [Feature: AI Solver Engine](#9-feature-ai-solver-engine)
10. [Feature: Export Engine](#10-feature-export-engine)
11. [Feature: Constraint System (HC + SC)](#11-feature-constraint-system)
12. [Database Schema & Entity Relationships](#12-database-schema--entity-relationships)
13. [API Contract Reference](#13-api-contract-reference)
14. [Test Architecture & Coverage Gates](#14-test-architecture--coverage-gates)
15. [Infrastructure & Deployment](#15-infrastructure--deployment)

---

## 1. System-Wide Architecture Topology

The platform separates UI, API, Solver, and Parser into strict layers. No solver logic enters API routes; no DB queries appear in React components.

### 1.1 End-to-End System Topology

```mermaid
graph TD
    subgraph "Browser Client — Next.js 14 App Router"
        UI_D["/ Dashboard"]
        UI_I["/import"]
        UI_C["/configure"]
        UI_S["/schedule Workbench"]
        UI_E["/export"]
    end

    subgraph "FastAPI Gateway — port 8000"
        GW_IMPORT["POST /api/v1/import/excel"]
        GW_CFG["CRUD /api/v1/configure/*"]
        GW_TT["GET /api/v1/timetable/*"]
        GW_SOLVE["POST /api/v1/solve"]
        GW_WS["WS /api/v1/solve/:id/stream"]
        GW_EXP["POST /api/v1/export/*"]
        GW_VAL["GET /api/v1/validate/:version"]
        GW_WIZ["POST /api/v1/solve/generate-from-wizard"]
    end

    subgraph "Celery Worker — Async Solver"
        CW_TASK["solver_tasks.run_solver_task()"]
        CW_WS_EMIT["WebSocket Progress Emitter"]
        CW_CSAT["CP-SAT Solver (OR-Tools)"]
        CW_GA["Genetic Algorithm"]
        CW_CC["Conflict Checker"]
    end

    subgraph "Parser / Exporter Layer"
        PAR["excel_parser.py — openpyxl"]
        EXP_XLSX["excel_exporter.py — openpyxl"]
        EXP_PDF["PDF Generator — reportlab"]
    end

    subgraph "PostgreSQL 16 — port 5432"
        DB_TT[("timetable_entries")]
        DB_FAC[("faculty")]
        DB_SEC[("sections")]
        DB_ROOM[("rooms")]
        DB_SUBJ[("subjects")]
        DB_SS[("section_subjects")]
        DB_MFA[("multi_faculty_assignments")]
        DB_SR[("solver_runs")]
        DB_CR[("clash_reports")]
    end

    subgraph "Redis 7 — port 6379"
        REDIS_BROKER["Celery Broker (DB 0)"]
        REDIS_RESULT["Celery Results (DB 1)"]
        REDIS_WS["WS Channel Pub/Sub"]
    end

    UI_I --> GW_IMPORT
    UI_C --> GW_CFG
    UI_S --> GW_TT
    UI_S --> GW_SOLVE
    UI_S --> GW_WS
    UI_S --> GW_WIZ
    UI_E --> GW_EXP
    UI_D --> GW_VAL

    GW_IMPORT --> PAR
    PAR --> DB_TT
    PAR --> DB_FAC
    PAR --> DB_ROOM
    PAR --> DB_SEC

    GW_SOLVE --> REDIS_BROKER
    REDIS_BROKER --> CW_TASK
    CW_TASK --> CW_CSAT
    CW_TASK --> CW_GA
    CW_TASK --> CW_CC
    CW_TASK --> DB_TT
    CW_TASK --> DB_SR
    CW_TASK --> REDIS_WS
    REDIS_WS --> GW_WS

    GW_EXP --> EXP_XLSX
    GW_EXP --> EXP_PDF
    EXP_XLSX --> DB_TT
    EXP_PDF --> DB_TT

    GW_CFG --> DB_FAC
    GW_CFG --> DB_ROOM
    GW_CFG --> DB_SUBJ
    GW_CFG --> DB_SS
    GW_CFG --> DB_MFA

    GW_TT --> DB_TT
    GW_VAL --> DB_CR
    GW_VAL --> CW_CC
```

### 1.2 Layer Responsibility Matrix

```mermaid
graph LR
    subgraph "UI Layer (React)"
        UI1["State Management\nuseState / useEffect"]
        UI2["API Calls\nAxios via timetableApi"]
        UI3["WebSocket\nuseSolver hook"]
        UI4["Rendering\nTimetableGrid / Wizard"]
    end

    subgraph "API Layer (FastAPI)"
        API1["Route Validation\nPydantic schemas"]
        API2["Auth Middleware\nJWT / CORS"]
        API3["Task Dispatch\nCelery .delay()"]
        API4["Response Shaping\nJSON serialization"]
    end

    subgraph "Service Layer (Python)"
        SVC1["timetable_service.py"]
        SVC2["faculty_service.py"]
        SVC3["export_service.py"]
        SVC4["solve_service.py"]
        SVC5["validate_service.py"]
    end

    subgraph "Solver Layer (OR-Tools)"
        SOL1["constraints.py\nHC-01..HC-10"]
        SOL2["csat_solver.py"]
        SOL3["genetic_algorithm.py"]
        SOL4["fitness.py"]
        SOL5["conflict_checker.py"]
        SOL6["incremental_validator.py"]
        SOL7["diagnostics.py"]
    end

    UI2 --> API1
    API1 --> SVC1
    SVC1 --> SOL1
    API3 --> SOL2
    API3 --> SOL3
```

---

## 2. Feature: Dashboard (`/`)

> Real-time system health dashboard for the ACSE department coordinator.

### 2.1 Dashboard Component Architecture

```mermaid
graph TD
    DASH["DashboardPage (app/page.tsx)"]

    subgraph "Data Sources"
        API_VER["GET /api/v1/timetable/versions"]
        API_VAL["GET /api/v1/validate/5"]
        API_FAC["GET /api/v1/faculty"]
        API_ROOM["GET /api/v1/rooms"]
        API_SEC["GET /api/v1/sections"]
    end

    subgraph "UI Panels"
        KPI["KPI Stats Row\n44 Sections · 80 Faculty · 35 Rooms · 1000 Slots"]
        CLASH["Clash Summary Card\n51 Hard Violations (V5)"]
        TIMELINE["Version Timeline\nV1 → V2 → V3 → V4 → V5"]
        ACTIONS["Quick Actions Grid\nImport · Schedule · Export · Validate"]
        SOLVER_CTA["AI Solver CTA Banner\nCP-SAT Engine Status"]
    end

    DASH --> API_VER
    DASH --> API_VAL
    DASH --> API_FAC
    DASH --> API_ROOM
    DASH --> API_SEC

    API_VAL --> CLASH
    API_VER --> TIMELINE
    API_FAC --> KPI
    API_ROOM --> KPI
    API_SEC --> KPI
```

### 2.2 Clash Summary State Machine

```mermaid
stateDiagram-v2
    [*] --> Loading : Component Mount
    Loading --> FetchingValidation : useEffect fires
    FetchingValidation --> ClashFound : violations > 0
    FetchingValidation --> ClashFree : violations == 0
    FetchingValidation --> APIError : Network failure

    ClashFound --> DisplayRed : Show red badge (51 clashes)
    ClashFree --> DisplayGreen : Show green badge (0 clashes)
    APIError --> DisplayFallback : Show V5 cached baseline

    ClashFound --> [*]
    ClashFree --> [*]
    DisplayFallback --> [*]
```

### 2.3 Version Timeline Data Flow

```mermaid
sequenceDiagram
    participant Browser
    participant FastAPI
    participant PostgreSQL

    Browser->>FastAPI: GET /api/v1/timetable/versions
    FastAPI->>PostgreSQL: SELECT * FROM solver_runs ORDER BY created_at
    PostgreSQL-->>FastAPI: [{id:5, label:"V5", date:"15-Jul", violations:51}, ...]
    FastAPI-->>Browser: JSON array of versions
    Browser->>Browser: Render horizontal timeline cards
    Browser->>Browser: Highlight V5 as "current baseline"
```

---

## 3. Feature: Excel Import (`/import`)

> Parse real VFSTR Excel timetable files (V3/V5 format) into the relational database.

### 3.1 Import Pipeline Architecture

```mermaid
graph TD
    UI["User uploads .xlsx file\n(Drag-and-drop zone)"]
    UI --> MULTI["FormData multipart POST\n/api/v1/import/excel"]

    subgraph "FastAPI Import Route"
        MULTI --> SAVE["Save temp file to disk"]
        SAVE --> PARSE["excel_parser.py"]
    end

    subgraph "Excel Parser Engine"
        PARSE --> DETECT["Sheet Detection\n(section sheets + MINORHONORS)"]
        DETECT --> CELL["Cell Anatomy Parser\nRow 7-12, Cols B-K"]
        CELL --> SUBJ["Subject Type Detector\nL / T / P / LIBRARY / BREAK"]
        CELL --> ROOM["Room Code Extractor\n(red font cells)"]
        CELL --> FAC["Faculty Legend Parser\nRows 14-22, 2-column"]
        SUBJ --> NORM["Normalizer\nStandardize codes & names"]
        ROOM --> NORM
        FAC --> NORM
    end

    subgraph "Conflict Checker"
        NORM --> CC["conflict_checker.py\ndetect_room_clashes()"]
        CC --> REPORT["Clash Report\n51 room clashes in V5"]
    end

    subgraph "Database Write"
        NORM --> DB_UPSERT["Upsert:\n- timetable_entries\n- faculty\n- rooms\n- sections\n- section_subjects\n- multi_faculty_assignments"]
        REPORT --> DB_CR["Insert: clash_reports"]
        DB_UPSERT --> DB_SR["Insert: solver_runs\n(version record)"]
    end

    DB_SR --> RESP["JSON Response\n{version_id, sections, slots, clashes}"]
    RESP --> UI_RESULT["UI: Clash Preview Table\n+ Confirm / Cancel"]
```

### 3.2 Cell Anatomy Parsing — Detailed Flow

```mermaid
graph TD
    SHEET["Excel Sheet (e.g. II AIML-A)"]

    subgraph "Header Zone"
        R2["Row 2: Academic Year Header\n'Academic year 2026-27 (I Semester)'"]
        R4["Row 4: Section Banner\n'II AIML-A' (purple fill #C084FC)"]
        R5["Row 5: Period Numbers 1-8"]
        R6["Row 6: Time Strings"]
    end

    subgraph "Grid Zone (Rows 7-12)"
        MON["Row 7: MON"]
        TUE["Row 8: TUE"]
        WED["Row 9: WED"]
        THU["Row 10: THU"]
        FRI["Row 11: FRI"]
        SAT["Row 12: SAT"]
    end

    subgraph "Cell Content"
        L1["Line 1: Subject Code (Black Bold)\nDS / AI(P) / DBMS(T)"]
        L2["Line 2: Room Code (Red font)\n619 / 604 / AFTF-12"]
        L3["Faculty name below grid\n(2-col legend rows 14-22)"]
        BREAK_COL["Column: BREAK\n09:55-10:10\n(merged all 6 rows)"]
        LUNCH_COL["Column: LUNCH\n12:40-1:40\n(merged all 6 rows)"]
    end

    subgraph "Faculty Legend Zone (Rows 14+)"
        LEG_L["Left Column:\nSubjectName(L): Dr. Lead Faculty"]
        LEG_P["Right Column:\nSubjectName(T&P): Lead, TA1, TA2, TA3"]
    end

    SHEET --> R2 & R4 & R5 & R6
    SHEET --> MON & TUE & WED & THU & FRI & SAT
    MON --> L1 & L2 & BREAK_COL & LUNCH_COL
    SHEET --> LEG_L & LEG_P
```

### 3.3 Subject Type Detection State Machine

```mermaid
stateDiagram-v2
    [*] --> ReadCell
    ReadCell --> IsEmpty : cell.value == None
    ReadCell --> CheckSuffix : cell has text

    IsEmpty --> EmptySlot : type = EMPTY
    CheckSuffix --> IsBreak : text == "BREAK"
    CheckSuffix --> IsLunch : text == "LUNCH"
    CheckSuffix --> IsLibrary : text == "LIBRARY"
    CheckSuffix --> IsLab : text ends with "(P)"
    CheckSuffix --> IsTutorial : text ends with "(T)"
    CheckSuffix --> IsCombined : text ends with "(T&P)"
    CheckSuffix --> IsMinors : text == "MINORHONORS"
    CheckSuffix --> IsLecture : none of the above

    IsBreak --> BlockedSlot : entry_type = BREAK
    IsLunch --> BlockedSlot : entry_type = LUNCH
    IsLibrary --> LibrarySlot : entry_type = LIBRARY
    IsLab --> LabSlot : entry_type = P, consecutive=2
    IsTutorial --> TutorialSlot : entry_type = T
    IsCombined --> CombinedSlot : entry_type = P, has T
    IsMinors --> MinorsSlot : entry_type = MINORS_HONORS
    IsLecture --> LectureSlot : entry_type = L

    EmptySlot --> [*]
    BlockedSlot --> [*]
    LibrarySlot --> [*]
    LabSlot --> [*]
    TutorialSlot --> [*]
    CombinedSlot --> [*]
    MinorsSlot --> [*]
    LectureSlot --> [*]
```

### 3.4 Import API Sequence Diagram

```mermaid
sequenceDiagram
    participant U as User Browser
    participant FE as Next.js Frontend
    participant API as FastAPI
    participant PAR as excel_parser.py
    participant CC as conflict_checker.py
    participant DB as PostgreSQL

    U->>FE: Drop .xlsx file
    FE->>FE: Show uploading spinner
    FE->>API: POST /api/v1/import/excel (multipart)
    API->>API: Validate file extension (.xlsx only)
    API->>PAR: parse_excel(file_path)
    PAR->>PAR: Detect section sheets
    PAR->>PAR: Parse each cell (day × period)
    PAR->>PAR: Extract faculty legends
    PAR-->>API: {sections:[], entries:[], faculty:[], rooms:[]}
    API->>CC: detect_room_clashes(entries)
    CC-->>API: [{day, period, room, section_a, section_b}] × 51
    API->>DB: UPSERT timetable_entries (1000 rows)
    API->>DB: UPSERT faculty, rooms, sections
    API->>DB: INSERT clash_reports (51 rows)
    API->>DB: INSERT solver_runs (version record)
    API-->>FE: {version_id:5, sections:44, slots:1000, clashes:51}
    FE->>FE: Render clash preview table
    FE->>U: Show "51 Room Clashes Found — Confirm Import?"
    U->>FE: Click Confirm
    FE-->>U: Redirect to /schedule
```

---

## 4. Feature: Master Data Configuration (`/configure`)

> CRUD management for all entities the solver depends on.

### 4.1 Configure Page Tab Architecture

```mermaid
graph LR
    TAB1["Tab 1\n👨‍🏫 Faculty\nWorkload Caps & Ranks"]
    TAB2["Tab 2\n🏢 Venues\nClassrooms & GPU Labs"]
    TAB3["Tab 3\n📚 Curriculum\nL-T-P Credit Hours"]
    TAB4["Tab 4\n🔗 Section Team Mapping\nMulti-Faculty Lab Teams"]

    TAB1 --> FAC_LIST["Faculty Table\n(searchable)"]
    TAB1 --> FAC_MODAL["Add/Edit Modal"]
    TAB1 --> FAC_AVAIL["Availability Grid\n6×8 Matrix"]
    TAB1 --> FAC_CSV["Bulk CSV Import"]

    TAB2 --> ROOM_LIST["Rooms Table\n(type badges)"]
    TAB2 --> ROOM_MODAL["Add/Edit Modal"]

    TAB3 --> SUBJ_LIST["Subjects Table\n(L-T-P split)"]
    TAB3 --> SUBJ_MODAL["Add/Edit Modal"]

    TAB4 --> SEC_SEL["Section Selector"]
    TAB4 --> SUBJ_SEL["Subject Selector"]
    TAB4 --> LTP_SLOTS["L-T-P Slot Numbers"]
    TAB4 --> THEORY_FAC["Theory Lead Faculty"]
    TAB4 --> LAB_LEAD["Lab Lead Faculty"]
    TAB4 --> TA_LIST["Lab TAs (checkbox multi)"]
    TAB4 --> SAVE_BTN["Save → POST /api/v1/section-subjects/batch-assign"]
```

### 4.2 Faculty CRUD State Machine

```mermaid
stateDiagram-v2
    [*] --> FacultyList : Page loads
    FacultyList --> AddModal : Click "+ Add Faculty"
    FacultyList --> EditModal : Click ✏️ on row
    FacultyList --> ConfirmDelete : Click 🗑️ on row
    FacultyList --> AvailabilityGrid : Click "View/Edit Matrix"

    AddModal --> Validating : Submit form
    EditModal --> Validating : Submit form
    Validating --> FacultyList : POST/PATCH success
    Validating --> ShowError : Validation fails

    ConfirmDelete --> FacultyList : User cancels
    ConfirmDelete --> DeleteAPI : User confirms
    DeleteAPI --> FacultyList : DELETE success

    AvailabilityGrid --> SaveAvailability : Toggle cells + Save
    SaveAvailability --> FacultyList : PATCH success
```

### 4.3 Faculty Availability Grid Data Model

```mermaid
graph TD
    FAC_DB["faculty.availability\nJSON column"]

    subgraph "Availability Matrix (6×8)"
        MON_P1["MON·P1 ✅"]
        MON_P2["MON·P2 ✅"]
        TUE_P3["TUE·P3 ❌ (Blocked)"]
        WED_P6["WED·P6 ❌ (Blocked)"]
        SAT_P8["SAT·P8 ✅"]
    end

    FAC_DB --> MON_P1
    FAC_DB --> TUE_P3
    FAC_DB --> WED_P6

    SOLVER["Solver HC-09\nFaculty Availability Constraint"]
    TUE_P3 --> SOLVER
    WED_P6 --> SOLVER
```

### 4.4 Section-Team Mapping Data Flow

```mermaid
graph TD
    FORM["Section-Team Mapping Form"]

    FORM --> SEC["selectedSectionId\n(e.g. II AIML-A)"]
    FORM --> SUBJ["selectedSubjectId\n(e.g. DS — Data Structures)"]
    FORM --> L_SLOTS["lectureSlots: 3\n(L hours/week)"]
    FORM --> T_SLOTS["tutorialSlots: 1\n(T hours/week)"]
    FORM --> P_SLOTS["labSlots: 2\n(P hours/week)"]
    FORM --> LEAD_FAC["lectureFacultyId\nDr. S. Srikantha Reddy"]
    FORM --> LAB_LEAD["labLeadFacultyId\nDr. S. Srikantha Reddy"]
    FORM --> CO_FAC["labCoFacultyIds[]\n[P.Girija, K.Nikhitha, Mahendra Varma]"]

    FORM --> API["POST /api/v1/section-subjects/batch-assign"]

    API --> SS_ROW["section_subjects row\n{section_id, subject_id, l_hours, t_hours, p_hours, lead_faculty_id}"]
    API --> MFA_ROW1["multi_faculty_assignments row\n{section_subject_id, faculty_id: P.Girija, role: TA}"]
    API --> MFA_ROW2["multi_faculty_assignments row\n{section_subject_id, faculty_id: K.Nikhitha, role: TA}"]
    API --> MFA_ROW3["multi_faculty_assignments row\n{section_subject_id, faculty_id: Mahendra Varma, role: TA}"]

    SS_ROW --> SOLVER_FEED["Solver Input\n(subject frequency + faculty constraints)"]
    MFA_ROW1 --> LEGEND["Faculty Legend\n(L column + P column below grid)"]
    MFA_ROW2 --> LEGEND
    MFA_ROW3 --> LEGEND
```

### 4.5 Faculty Grade → AICTE Workload Cap

```mermaid
graph LR
    PROF["Professor\nmax_hours_per_week: 12\nmax_daily_classes: 4"]
    ASSOC["Associate Professor\nmax_hours_per_week: 14\nmax_daily_classes: 5"]
    ASST["Assistant Professor\nmax_hours_per_week: 16\nmax_daily_classes: 5"]
    EXT["External / Industry\nmax_hours_per_week: 10\nmax_daily_classes: 3"]

    PROF --> HC10["HC-10: No 4-Consec Teaching"]
    ASSOC --> HC10
    ASST --> HC10
    EXT --> HC10

    PROF --> SC03["SC-03: Balance Daily Load"]
    ASSOC --> SC03
```

---

## 5. Feature: Schedule Workbench — Single Section Grid

> Interactive week-view timetable for one section at a time, with drag-and-drop editing.

### 5.1 Single Grid Component Architecture

```mermaid
graph TD
    PAGE["SchedulePage (mode='matrix')"]

    subgraph "Controls"
        SEC_SEL["Section Dropdown\n(44 sections grouped by cohort)"]
        VER_SEL["Version Selector\n(V3, V5, solver runs)"]
    end

    subgraph "TimetableGrid Component"
        BANNER["Section Banner\n(purple, Academic Year text)"]
        PERIOD_HDR["Period Header Row\n1-2-BREAK-3-4-5-LUNCH-6-7-8"]
        TIME_HDR["Time Header Row\n8:15-9:05 ... 3:20-4:05"]
        DAY_ROWS["MON-TUE-WED-THU-FRI-SAT rows"]
        CELLS["Slot Cells (3-line anatomy)"]
        BREAK_COL["BREAK column (merged 6 rows)\nvertical B-R-E-A-K text"]
        LUNCH_COL["LUNCH column (merged 6 rows)\nvertical L-U-N-C-H text"]
        LEGEND["2-Column Faculty Legend\nL col | P/T&P col"]
    end

    subgraph "Sidebar Panels"
        STATS["Section Stats Card\n(slots, labs, clashes, version)"]
        SOLVER_PANEL["AI Solver Panel\n(algorithm, run button, progress)"]
    end

    PAGE --> SEC_SEL & VER_SEL
    SEC_SEL --> API["GET /api/v1/timetable/version/:id?section_name=..."]
    API --> CELLS
    CELLS --> DAY_ROWS
    PAGE --> STATS & SOLVER_PANEL
```

### 5.2 Slot Cell Rendering Decision Tree

```mermaid
graph TD
    CELL_DATA["SlotEntry data for day×period"]

    CELL_DATA --> IS_EMPTY{"entry == null?"}
    IS_EMPTY --> |Yes| EMPTY_CELL["Show — (slate-300)"]
    IS_EMPTY --> |No| HAS_CLASH{"hasClash == true?"}

    HAS_CLASH --> |Yes| CLASH_STYLE["bg-red-100\nborder-l-4 border-red-600\nTooltip: clash reason"]
    HAS_CLASH --> |No| NORMAL_STYLE["bg-white hover:bg-purple-50"]

    CLASH_STYLE --> RENDER_CONTENT
    NORMAL_STYLE --> RENDER_CONTENT

    RENDER_CONTENT --> LINE1["Line 1: subjectCode\nfont-bold text-slate-900 text-11px"]
    RENDER_CONTENT --> LINE2{"roomCode != ''?"}
    LINE2 --> |Yes| LINE2_SHOW["Line 2: roomCode\ntext-red-600 font-extrabold"]
    LINE2 --> |No| SKIP2["(skip)"]
    RENDER_CONTENT --> LINE3{"facultyName != ''?"}
    LINE3 --> |Yes| LINE3_SHOW["Line 3: shortFacultyName\ntext-slate-500 italic text-9px truncate"]
    LINE3 --> |No| SKIP3["(skip)"]

    LINE3_SHOW --> SHORT["shortFaculty() helper\n'Dr. S. Srikantha Reddy' → 'Dr. Reddy'"]
```

### 5.3 Drag-and-Drop Slot Swap Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant GRID as TimetableGrid
    participant INC as incremental_validator.py
    participant DB as PostgreSQL

    U->>GRID: Drag slot (entryId=42) from MON·P1
    GRID->>GRID: onDragStart → store entryId in dataTransfer
    U->>GRID: Drop onto WED·P4 cell
    GRID->>GRID: onDrop → extract entryId
    GRID->>GRID: onSlotSwap(42, "WED", 4)
    GRID->>INC: POST /api/v1/timetable/validate-move\n{entry_id:42, new_day:"WED", new_period:4}
    INC->>INC: Load ScheduleIndex (O(1) lookup)
    INC->>INC: Check HC-01 Room conflict at WED·P4
    INC->>INC: Check HC-02 Faculty double-book at WED·P4
    INC->>INC: Check HC-03 Section overlap at WED·P4
    INC-->>GRID: {valid: true, violations: []}
    GRID->>DB: PATCH /api/v1/timetable/entries/42\n{new_time_slot_id: 28, new_room_id: null}
    DB-->>GRID: 200 OK
    GRID->>GRID: Re-render cell in new position
```

### 5.4 Faculty Name Shortening Algorithm

```mermaid
flowchart TD
    INPUT["Full name: 'Dr. S. Srikantha Reddy'"]
    SPLIT["Split by whitespace → ['Dr.', 'S.', 'Srikantha', 'Reddy']"]
    COUNT{"parts.length <= 2?"}
    COUNT --> |Yes| RETURN_FULL["Return full name"]
    COUNT --> |No| HAS_TITLE{"parts[0] matches\n/^(Dr|Mr|Ms|Prof)\\./i ?"}
    HAS_TITLE --> |Yes| WITH_TITLE["title = 'Dr. '"]
    HAS_TITLE --> |No| NO_TITLE["title = ''"]
    WITH_TITLE --> LAST_NAME["Append parts[last] = 'Reddy'"]
    NO_TITLE --> LAST_NAME
    LAST_NAME --> OUTPUT["Result: 'Dr. Reddy'"]
```

---

## 6. Feature: Schedule Workbench — Vertical Stack View

> All sections in a cohort rendered vertically, matching the exact format of the reference Excel screenshots.

### 6.1 Stack View Render Pipeline

```mermaid
graph TD
    VER_SEL["Version Selected (V5)"]
    COHORT_SEL["Cohort Selected\n(e.g. II_AIML → 12 sections A-L)"]

    VER_SEL --> LOAD["Load all slots for cohort\nGET /api/v1/timetable/version/5"]
    COHORT_SEL --> LOAD

    LOAD --> GROUP["Group entries by section_name"]
    GROUP --> LOOP["For each section in cohort order:"]

    LOOP --> BLOCK["Render Section Block"]

    subgraph "One Section Block Layout"
        ACAD_HDR["Academic Year Header\n'Academic year 2026-27 (I Semester)'"]
        SECT_BANNER["Purple Section Banner\n#C084FC bg, AIML-A text, uppercase"]
        PERIOD_ROW["Period Header: 1 | 2 | BREAK | 3 | 4 | 5 | LUNCH | 6 | 7 | 8"]
        TIME_ROW["Time Row: 8:15-9:05 ... 3:20-4:05"]
        GRID_ROWS["6 Day Rows: MON–SAT"]
        LEGEND["2-Col Faculty Legend"]
        SPACER["3 blank rows spacer"]
    end

    BLOCK --> ACAD_HDR
    ACAD_HDR --> SECT_BANNER
    SECT_BANNER --> PERIOD_ROW
    PERIOD_ROW --> TIME_ROW
    TIME_ROW --> GRID_ROWS
    GRID_ROWS --> LEGEND
    LEGEND --> SPACER
    SPACER --> LOOP
```

### 6.2 Excel Export — Cohort Stacking (Backend)

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant API as FastAPI
    participant SVC as ExportService
    participant EXP as excel_exporter.py
    participant DB as PostgreSQL

    FE->>API: POST /api/v1/export/excel/cohort/II_AIML?version_id=5
    API->>SVC: generate_cohort_excel_export("II_AIML", version_id=5)
    SVC->>DB: SELECT * FROM timetable_entries\nWHERE version_id=5 AND section IN (II AIML-A..L)
    DB-->>SVC: 600+ rows (12 sections × ~50 slots)
    SVC->>EXP: export_cohort_excel("II_AIML", entries)
    EXP->>EXP: Create openpyxl Workbook
    EXP->>EXP: Add single worksheet "II AIML — All Sections"
    loop For each section (A → L)
        EXP->>EXP: _write_section_block(ws, start_row, section_name, slots)
        EXP->>EXP: Row+0: Academic year header (centered)
        EXP->>EXP: Row+2: Purple banner #C084FC merged A:K
        EXP->>EXP: Row+3: Period headers 1-8 + BREAK/LUNCH merged
        EXP->>EXP: Row+4: Time strings
        EXP->>EXP: Rows+5-10: MON-SAT grid (red font for rooms)
        EXP->>EXP: Rows+12+: 2-col faculty legend
        EXP->>EXP: start_row += block_height + 3 (spacer)
    end
    EXP-->>SVC: bytes (Excel file in memory)
    SVC-->>API: bytes
    API-->>FE: StreamingResponse(bytes, content-type=xlsx)
    FE->>FE: trigger browser download
```

### 6.3 Cohort Section Mapping

```mermaid
graph LR
    subgraph "II_AIML Cohort (12 sections)"
        A["II AIML-A"] --> B["II AIML-B"] --> C["II AIML-C"] --> D["II AIML-D"]
        D --> E["II AIML-E"] --> F["II AIML-F"] --> G["II AIML-G"] --> H["II AIML-H"]
        H --> I["II AIML-I"] --> J["II AIML-J"] --> K["II AIML-K"] --> L["II AIML-L"]
    end
    subgraph "III_AIML Cohort (7 sections)"
        A3["III AIML-A"] --> B3["III AIML-B"] --> C3["III AIML-C"]
        C3 --> D3["III AIML-D"] --> E3["III AIML-E"] --> F3["III AIML-F"] --> G3["III AIML-G"]
    end
    subgraph "IV_AIML Cohort (5 sections)"
        A4["IV AIML-A"] --> B4["IV AIML-B"] --> C4["IV AIML-C"] --> D4["IV AIML-D"] --> E4["IV AIML-E"]
    end
    subgraph "CS_DS Cohort (9 sections)"
        CS2A["II CS-A"] --> CS2B["II CS-B"] --> CS3["III CS"] --> CS4["IV CS"]
        DS2A["II DS-A"] --> DS2B["II DS-B"] --> DS3A["III DS-A"] --> DS3B["III DS-B"] --> DS4["IV DS"]
    end
    subgraph "CSBS_IOT Cohort (5 sections)"
        CSBS2["II CSBS"] --> CSBS3["III CSBS"] --> CSBS4["IV - CSBS"]
        IOT2["II IOT"] --> IOT3["III IOT"]
    end
```

---

## 7. Feature: Schedule Workbench — Faculty Schedules

> Individual weekly teaching schedule for any faculty member.

### 7.1 Faculty Schedule Data Flow

```mermaid
graph TD
    FAC_SEL["Faculty Selector Dropdown\n~80 faculty members"]
    VER_SEL["Version Selector\n(V5 default)"]

    FAC_SEL --> API["GET /api/v1/timetable/faculty/:id?version_id=5"]
    VER_SEL --> API

    API --> SVC["timetable_service.get_faculty_timetable()"]
    SVC --> DB["SELECT te.*, s.name as section\nFROM timetable_entries te\nJOIN section_subjects ss ON te.section_subject_id = ss.id\nWHERE ss.faculty_id = :faculty_id\nAND te.version_id = :version_id"]

    DB --> RESP["{faculty_name, designation,\ntotal_hours, max_hours,\nentries: [{day, period, subject, room, section}]}"]

    RESP --> HEADER_CARD["Faculty Header Card\nName · Designation · Weekly Load"]
    RESP --> GRID["TimetableGrid\n(section name in Line 3\ninstead of faculty name)"]
    RESP --> DL_BTN["Download PDF Button"]
```

### 7.2 Faculty PDF Generation Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant API as FastAPI
    participant SVC as ExportService
    participant PDF as PDF Generator
    participant DB as PostgreSQL

    U->>FE: Click "Download Faculty PDF"
    FE->>API: GET /api/v1/export/pdf/faculty/1?version_id=5
    API->>SVC: generate_single_faculty_pdf(faculty_id=1, version_id=5)
    SVC->>DB: SELECT faculty name, designation, max_hours
    SVC->>DB: SELECT all timetable entries for faculty_id=1, version_id=5
    DB-->>SVC: {name: "Dr. Reddy", entries: [...]}
    SVC->>PDF: build_faculty_pdf(faculty_data, entries)
    PDF->>PDF: A4 Portrait canvas
    PDF->>PDF: Header: Name + Designation + Dept + Weekly Load
    PDF->>PDF: 6×8 week grid with subject/room/section in cells
    PDF->>PDF: Footer: VFSTR logo + academic year
    PDF-->>SVC: bytes
    SVC-->>API: bytes
    API-->>FE: StreamingResponse (application/pdf)
    FE->>FE: window.URL.createObjectURL(blob)
    FE->>FE: <a> click → download VFSTR_V5_Schedule_Dr_Reddy.pdf
    FE-->>U: File downloaded
```

### 7.3 Teaching Load Calculation

```mermaid
graph TD
    ENTRIES["timetable_entries for faculty"]

    ENTRIES --> FILTER_BLOCKED["Filter out BREAK, LUNCH, LIBRARY slots"]
    FILTER_BLOCKED --> COUNT["Count remaining slots → total_hours"]

    COUNT --> COMPARE{"total_hours vs max_hours?"}
    COMPARE --> |"<= max_hours"| GREEN["Show load bar: green\n(within AICTE cap)"]
    COMPARE --> |"> max_hours"| RED["Show load bar: red\n(HC violation — over cap)"]

    GRADE["Faculty Grade"] --> MAX_H["max_hours:\nProfessor=12\nAssociate=14\nAssistant=16\nExternal=10"]
    MAX_H --> COMPARE
```

---

## 8. Feature: Create Timetable Wizard

> 4-step guided workflow to configure and generate a new timetable from scratch.

### 8.1 Wizard Step Flow

```mermaid
stateDiagram-v2
    [*] --> Step1 : Click "Create Timetable" button

    Step1 : Step 1 — Academic Scope & Workload Cap
    Step1 : Branch / Year / Sections / Max Daily Hours

    Step1 --> Step2 : Click "Next"

    Step2 : Step 2 — Multi-Faculty Lab Teams
    Step2 : Subject rows with Lead + Co-Faculty + Hours

    Step2 --> Step1 : Click "Back"
    Step2 --> Step3 : Click "Next"

    Step3 : Step 3 — Venue Matrix & Period Locks
    Step3 : Preferred block / room type / pin slots

    Step3 --> Step2 : Click "Back"
    Step3 --> Step4 : Click "Next"

    Step4 : Step 4 — 0-Clash AI Solve
    Step4 : Review summary → Generate

    Step4 --> Step3 : Click "Back"
    Step4 --> Generating : Click "Generate Clash-Free Timetable"

    Generating --> Success : API returns timetable
    Generating --> INFEASIBLE : CP-SAT returns INFEASIBLE
    INFEASIBLE --> DiagMessage : Show human-readable fix suggestions
    DiagMessage --> Step1 : User adjusts params

    Success --> GridView : mode = 'matrix' with new data
```

### 8.2 Wizard API Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant WIZ as ScheduleSetupWizard
    participant API as FastAPI (wizard_solve.py)
    participant CSAT as CP-SAT Solver
    participant DIAG as diagnostics.py
    participant DB as PostgreSQL

    U->>WIZ: Complete all 4 steps
    U->>WIZ: Click "Generate Clash-Free Timetable"
    WIZ->>WIZ: setLoading(true)
    WIZ->>API: POST /api/v1/solve/generate-from-wizard\n{branch, year, sections, assignments, preferred_block, max_daily_hours}

    API->>API: Validate payload (Pydantic)
    API->>CSAT: build_model(sections, assignments, rooms)
    CSAT->>CSAT: Create 591,360 binary variables
    CSAT->>CSAT: Add HC-01..HC-10 constraints
    CSAT->>CSAT: Add SC-01..SC-10 objective terms
    CSAT->>CSAT: model.Solve(timeout=120s)

    alt Solver finds solution
        CSAT-->>API: SolverStatus.OPTIMAL or FEASIBLE
        API->>DB: INSERT timetable_entries (new version)
        API->>DB: INSERT solver_runs (run record)
        API-->>WIZ: {status:"OK", version_id:6, hard_violations:0}
        WIZ->>WIZ: onSuccess(response) → setMode('matrix')
    else Solver infeasible
        CSAT-->>API: SolverStatus.INFEASIBLE
        API->>DIAG: analyze_infeasibility(sections, assignments)
        DIAG-->>API: ["Over-subscribed: Dr. Reddy has 18h/week (max 14)", "Lab room 604 unavailable on SAT"]
        API-->>WIZ: {status:"INFEASIBLE", suggestions:[...]}
        WIZ->>WIZ: setError("...suggestions...")
        WIZ-->>U: Show error with fixes
    end
```

### 8.3 Subject Assignment Form Data Model

```mermaid
graph TD
    subgraph "CourseAssignmentInput (per subject row)"
        SC["subject_code: 'DS'"]
        SN["subject_name: 'Data Structures'"]
        ST["subject_type: 'L' | 'P' | 'T'"]
        FN["faculty_name: 'Dr. S. Srikantha Reddy'"]
        CF["co_faculty: ['P. Girija', 'K. Nikhitha', 'Mahendra Varma']"]
        WH["weekly_hours: 3"]
        CS["continuous_slots: 1 (L) or 2 (P)"]
    end

    subgraph "Year Curriculum Templates"
        Y2["II Year: DS, DS(P), AI, AI(P), DBMS, SFCDS"]
        Y3["III Year: DL(P), WT, CV(P), MINORHONOR"]
        Y4["IV Year: CNS(P), GENAI(P), IOT"]
    end

    Y2 --> SC
    Y3 --> SC
    Y4 --> SC
```

---

## 9. Feature: AI Solver Engine

> Multi-algorithm constraint solver that eliminates timetable clashes.

### 9.1 Solver Algorithm Selection Flow

```mermaid
graph TD
    TRIGGER["Solver Triggered\n(POST /api/v1/solve or wizard)"]
    ALGO_SEL{"Algorithm?"}

    TRIGGER --> ALGO_SEL
    ALGO_SEL --> |"CP-SAT"| CSAT["csat_solver.py\nGoogle OR-Tools CP-SAT"]
    ALGO_SEL --> |"GA"| GA["genetic_algorithm.py\nEvolutionary Search"]
    ALGO_SEL --> |"Hybrid"| HYBRID["Phase 1: GA finds feasible\nPhase 2: CP-SAT polishes"]

    CSAT --> CSAT_BUILD["Build CP model:\n591,360 binary vars\n10 HC + 10 SC constraints"]
    CSAT_BUILD --> CSAT_SOLVE["model.Solve(timeout=120s)"]
    CSAT_SOLVE --> CSAT_OUT{"Status?"}
    CSAT_OUT --> |"OPTIMAL"| EMIT_COMPLETE["Emit: complete (0 violations)"]
    CSAT_OUT --> |"FEASIBLE"| EMIT_FEASIBLE["Emit: feasible (some soft violations)"]
    CSAT_OUT --> |"INFEASIBLE"| DIAG["diagnostics.py\nReturn fix suggestions"]

    GA --> GA_INIT["Init population\n200 random chromosomes"]
    GA_INIT --> GA_EVAL["Evaluate fitness\n-(HC×10000 + ΣSC×weight)"]
    GA_EVAL --> GA_SELECT["Tournament selection\nElitism: keep top 10"]
    GA_SELECT --> GA_CROSS["Uniform crossover\n(day-period genes)"]
    GA_CROSS --> GA_MUTATE["Mutation (5%)\nRandom slot reassignment"]
    GA_MUTATE --> GA_CHECK{"Generations = 1000\nor violations = 0?"}
    GA_CHECK --> |No| GA_EVAL
    GA_CHECK --> |Yes| GA_OUT["Best chromosome → timetable"]

    HYBRID --> GA
    GA_OUT --> CSAT
```

### 9.2 CP-SAT Variable & Constraint Model

```mermaid
graph TD
    subgraph "Decision Variables"
        VAR["x[section_id][subject_id][day][period][room_id]\n∈ {0, 1}\n591,360 total binary variables"]
    end

    subgraph "Hard Constraints (NEVER relaxed)"
        HC01["HC-01: Room Conflict\nΣ x[s][*][d][p][r] ≤ 1 for all d,p,r"]
        HC02["HC-02: Faculty Double-Book\nΣ x[s][j][d][p][*] ≤ 1 per faculty"]
        HC03["HC-03: Student Conflict\nx[s1][*][d][p][*] + x[s2][*][d][p][*] ≤ 1\nif sections share students"]
        HC04["HC-04: Subject Frequency\nΣ x[s][j][*][*][*] = weekly_hours[j]"]
        HC05["HC-05: Room Capacity\nroom.capacity ≥ section.strength"]
        HC06["HC-06: Room Type\nLab subjects → lab rooms only\nGPU subjects → GPU rooms only"]
        HC07["HC-07: Break/Lunch\nx[*][*][*][BREAK][*] = 0\nx[*][*][*][LUNCH][*] = 0"]
        HC08["HC-08: Consecutiveness\nLab x[s][j][d][p][r]=1 → x[s][j][d][p+1][r]=1"]
        HC09["HC-09: Faculty Availability\nx[s][j][d][p][*] = 0\nif faculty blocked at d,p"]
        HC10["HC-10: No 4-Consec Teaching\nΣ x[*][j][d][p..p+3][*] ≤ 3 per faculty"]
    end

    subgraph "Soft Constraints (Minimized)"
        SC01["SC-01 w=50: Morning theory preference"]
        SC07["SC-07 w=100: Faculty preference days"]
        SC02["SC-02 w=30: Spread lab slots"]
        SC05["SC-05 w=20: Same-subject on diff days"]
    end

    VAR --> HC01 & HC02 & HC03 & HC04 & HC05 & HC06 & HC07 & HC08 & HC09 & HC10
    VAR --> SC01 & SC07 & SC02 & SC05
```

### 9.3 Real-Time WebSocket Progress Protocol

```mermaid
sequenceDiagram
    participant FE as Frontend (useSolver hook)
    participant API as FastAPI
    participant REDIS as Redis Pub/Sub
    participant CELERY as Celery Worker

    FE->>API: POST /api/v1/solve {algorithm: "CP-SAT"}
    API->>REDIS: Push task to broker queue
    API-->>FE: {run_id: "run_abc123"}
    FE->>API: WS CONNECT /api/v1/solve/run_abc123/stream

    CELERY->>CELERY: Task starts, loads solver
    loop Every 5 seconds / per generation
        CELERY->>REDIS: PUBLISH run_abc123 {type:"progress", generation:150, hard_violations:12, fitness:-120450, runtime_seconds:23}
        REDIS->>API: forward message
        API->>FE: WS message {type:"progress",...}
        FE->>FE: Update progress bar\nUpdate violation counter\nAdd to history chart
    end

    CELERY->>CELERY: Solver finds 0-clash solution
    CELERY->>REDIS: PUBLISH run_abc123 {type:"complete", hard_violations:0, timetable_version_id:7}
    REDIS->>API: forward message
    API->>FE: WS message {type:"complete",...}
    FE->>FE: isSolving=false, isComplete=true
    FE->>FE: Show "100% Clash-Free!" badge
    FE->>API: WS CLOSE
```

### 9.4 Incremental Validator (Drag-Drop O(1) Check)

```mermaid
graph TD
    DRAG["User drags slot\nentryId=42 → WED·P4"]

    DRAG --> LOAD_IDX["Load ScheduleIndex\n(built once on import)"]

    subgraph "ScheduleIndex (O1 lookups)"
        IDX_ROOM["room_slot_map\n{room_id: {day: {period: entry_id}}}"]
        IDX_FAC["faculty_slot_map\n{faculty_id: {day: {period: entry_id}}}"]
        IDX_SEC["section_slot_map\n{section_id: {day: {period: entry_id}}}"]
    end

    LOAD_IDX --> CHECK_HC01["HC-01: room_slot_map[room][WED][4] == null?"]
    LOAD_IDX --> CHECK_HC02["HC-02: faculty_slot_map[faculty][WED][4] == null?"]
    LOAD_IDX --> CHECK_HC03["HC-03: section_slot_map[section][WED][4] == null?"]

    CHECK_HC01 --> |"Occupied"| REJECT["Return {valid:false, reason:'Room 604 busy WED·P4'}"]
    CHECK_HC02 --> |"Occupied"| REJECT
    CHECK_HC03 --> |"Occupied"| REJECT

    CHECK_HC01 --> |"Free"| PASS["All checks pass"]
    CHECK_HC02 --> |"Free"| PASS
    CHECK_HC03 --> |"Free"| PASS

    PASS --> APPLY["PATCH /api/v1/timetable/entries/42\n{new_time_slot_id, new_room_id}"]
    APPLY --> RE_RENDER["Grid re-renders with updated slot"]
```

### 9.5 Fitness Function

```mermaid
graph TD
    SOL_OUT["Chromosome / Timetable State"]

    SOL_OUT --> HC_EVAL["Count Hard Violations\nHC_violations = 0..N"]
    SOL_OUT --> SC_EVAL["Count Soft Violations per SC-01..SC-10"]

    HC_EVAL --> FITNESS["fitness = -(HC_violations × 10,000)\n        - Σ(SC_weight_i × SC_violations_i)"]
    SC_EVAL --> FITNESS

    FITNESS --> TARGET{"fitness == 0?"}
    TARGET --> |"Yes"| OPTIMAL["🎉 Perfect timetable\n(no violations of any kind)"]
    TARGET --> |"HC=51, SC=0"| V5_BASELINE["V5 baseline\nfitness = -510,000"]
    TARGET --> |"Continue"| NEXT_GEN["Next GA generation\nor CP-SAT branch"]
```

---

## 10. Feature: Export Engine

> Download timetable data in Excel and PDF formats with exact visual matching of reference screenshots.

### 10.1 Export Options Architecture

```mermaid
graph TD
    EXP_PAGE["Export Page (/export)"]

    subgraph "Excel Downloads"
        EXP_FULL["Full Version Excel\nAll 44 sections, separate tabs\nPOST /export/excel?version_id=5"]
        EXP_COHORT["Cohort Excel\nSections stacked vertically, 1 sheet\nPOST /export/excel/cohort/:key"]
        EXP_MH["Minors/Honors Master Sheet\nYellow dept headers\nPOST /export/excel/minors-honors"]
    end

    subgraph "PDF Downloads"
        EXP_SEC_PDF["All Sections PDF Bundle\n44 sections, 1 per page\nPOST /export/pdf/sections"]
        EXP_FAC_PDF["All Faculty PDF Bundle\nAll faculty individual grids\nPOST /export/pdf/faculty"]
        EXP_FAC1_PDF["Single Faculty PDF\nIndividual download from /schedule\nGET /export/pdf/faculty/:id"]
    end

    EXP_PAGE --> EXP_FULL & EXP_COHORT & EXP_MH
    EXP_PAGE --> EXP_SEC_PDF & EXP_FAC_PDF & EXP_FAC1_PDF
```

### 10.2 Excel Export Styling Layer

```mermaid
graph TD
    EXP_FN["_write_section_block(ws, start_row, sec_name, slots)"]

    EXP_FN --> ROW1["Row+0: Academic Year Header\nFont: bold, center across A:K"]
    EXP_FN --> ROW2["Row+2: Section Banner\nFill: #C084FC (purple)\nFont: bold, uppercase, center\nMerged A:K"]
    EXP_FN --> ROW3["Row+3: Period Numbers 1-8\nFill: slate-100\nBREAK/LUNCH: merged, slate-200 bg"]
    EXP_FN --> ROW4["Row+4: Time Strings\n8:15-9:05 ... 3:20-4:05"]

    EXP_FN --> GRID_ROWS["Rows+5 to +10: MON-SAT"]
    GRID_ROWS --> CELL_STYLE["Each Cell:\nLine 1: subject code (Black Bold)\nLine 2: room code (Red, font color=FF0000)\nClash cell: red fill #FEE2E2"]

    EXP_FN --> LEGEND_ROWS["Rows+12+: Faculty Legend\nLeft col: Subject(L): Dr. Name\nRight col: Subject(T&P): Lead, TA1, TA2"]
    EXP_FN --> BORDERS["All cells: thin black border\nOuter: medium border"]
```

### 10.3 PDF Generation Pipeline

```mermaid
sequenceDiagram
    participant API as FastAPI
    participant SVC as export_service.py
    participant DB as PostgreSQL
    participant PDF as PDF Generator

    API->>SVC: generate_section_pdfs_export(version_id=5)
    SVC->>DB: SELECT DISTINCT section_name FROM timetable_entries WHERE version_id=5
    DB-->>SVC: [44 section names]

    loop For each section
        SVC->>DB: SELECT * FROM timetable_entries\nWHERE version_id=5 AND section=:name
        DB-->>SVC: ~22 slot rows per section
        SVC->>PDF: add_section_page(canvas, section_name, slots)
        PDF->>PDF: Draw purple banner
        PDF->>PDF: Draw 6×10 grid (periods + BREAK + LUNCH)
        PDF->>PDF: Fill cells (subject, room, faculty)
        PDF->>PDF: Draw 2-col legend below grid
        PDF->>PDF: canvas.showPage()
    end

    PDF-->>SVC: bytes (44-page PDF)
    SVC-->>API: bytes
    API-->>FE: StreamingResponse
```

---

## 11. Feature: Constraint System

> 20 named constraints (10 Hard + 10 Soft) that govern all solver behavior.

### 11.1 Hard Constraint Priority Hierarchy

```mermaid
graph TD
    SOLVER["Solver Output"]

    HC01["HC-01 Room Conflict\n🔴 NEVER RELAX\nRoom double-booking = total failure"]
    HC02["HC-02 Faculty Double-Book\n🔴 NEVER RELAX\nFaculty two-sections = impossible"]
    HC03["HC-03 Student Conflict\n🔴 NEVER RELAX\nShared students = schedule collapse"]
    HC07["HC-07 Break/Lunch Block\n🔴 NEVER RELAX\nFixed university policy"]
    HC04["HC-04 Subject Frequency\n🔴 NEVER RELAX\nCredit hours must be exact"]
    HC05["HC-05 Room Capacity\n🟡 Last resort only\n(Relax if no room available)"]
    HC06["HC-06 Room Type\n🟡 Last resort only\n(Relax if no lab available)"]
    HC08["HC-08 Consecutiveness\n🟠 Relax only for 3hr labs\n(if no room available)"]
    HC09["HC-09 Faculty Availability\n🟢 Soft in Phase 1\nHard in Phase 2"]
    HC10["HC-10 No 4-Consec Teaching\n🟢 Soft in Phase 1\nHard in Phase 2"]

    SOLVER --> HC01 & HC02 & HC03 & HC07
    HC01 --> HC04
    HC04 --> HC05 & HC06 & HC08
    HC08 --> HC09 & HC10
```

### 11.2 Soft Constraint Weights & Objectives

```mermaid
graph LR
    OBJ["Minimization Objective"]

    SC07["SC-07\nFaculty preference days\nweight=100"]
    SC01["SC-01\nMorning theory preference\nweight=50"]
    SC02["SC-02\nSpread lab slots across week\nweight=30"]
    SC05["SC-05\nSame-subject on different days\nweight=20"]
    SC03["SC-03\nBalance faculty daily load\nweight=15"]
    SC08["SC-08\nMinimize room changes per section/day\nweight=15"]
    SC09["SC-09\nTutorial after lecture\nweight=10"]
    SC04["SC-04\nAvoid first/last period for seniors\nweight=10"]
    SC06["SC-06\nPrefer same block for section\nweight=5"]
    SC10["SC-10\nBalance load across rooms\nweight=5"]

    OBJ --> SC07 & SC01 & SC02 & SC05 & SC03 & SC08 & SC09 & SC04 & SC06 & SC10
```

### 11.3 Constraint Validation Flow (Baseline Check)

```mermaid
sequenceDiagram
    participant CLI as make validate
    participant CC as conflict_checker.py
    participant DB as PostgreSQL

    CLI->>CC: validate_timetable(version_id=5)
    CC->>DB: SELECT all timetable_entries WHERE version_id=5
    DB-->>CC: 1000 rows

    CC->>CC: Build room_slot_map: {room: {day: {period: [sections]}}}
    CC->>CC: For each room×day×period with >1 section → CLASH
    CC-->>CLI: room_clashes: 51

    CC->>CC: Build faculty_slot_map: {faculty: {day: {period: [sections]}}}
    CC->>CC: For each faculty×day×period with >1 section → CLASH
    CC-->>CLI: faculty_clashes: 0

    CLI->>CLI: Assert room_clashes == 51 ✅
    CLI->>CLI: Assert faculty_clashes == 0 ✅
    CLI-->>CLI: "V5 Baseline VALIDATED"
```

---

## 12. Database Schema & Entity Relationships

### 12.1 Core Entity ER Diagram

```mermaid
erDiagram
    DEPARTMENTS {
        int id PK
        string name
        string code
    }
    BRANCHES {
        int id PK
        string name
        string code
        int department_id FK
    }
    SECTIONS {
        int id PK
        string name
        string label
        int year_level
        int strength
        int branch_id FK
        bool is_active
    }
    FACULTY {
        int id PK
        string name
        string employee_id
        string designation
        int max_hours_per_week
        int max_daily_classes
        bool is_external
        json availability
        int department_id FK
    }
    ROOMS {
        int id PK
        string code
        string room_type
        int capacity
        string floor
        string block
        bool gpu_capable
        bool is_available
    }
    SUBJECTS {
        int id PK
        string code
        string full_name
        int lecture_hours
        int tutorial_hours
        int lab_hours
        bool is_lab
        bool gpu_required
        string slot_type
        int requires_consecutive
    }
    TIME_SLOTS {
        int id PK
        string day
        int period_number
        string start_time
        string end_time
        bool is_blocked
    }

    DEPARTMENTS ||--o{ BRANCHES : "has"
    BRANCHES ||--o{ SECTIONS : "groups"
    DEPARTMENTS ||--o{ FACULTY : "employs"
```

### 12.2 Assignment & Timetable ER Diagram

```mermaid
erDiagram
    SECTION_SUBJECTS {
        int id PK
        int section_id FK
        int subject_id FK
        int lecture_faculty_id FK
        int lab_lead_faculty_id FK
        int lecture_slots_needed
        int tutorial_slots_needed
        int lab_slots_needed
    }
    MULTI_FACULTY_ASSIGNMENTS {
        int id PK
        int section_subject_id FK
        int faculty_id FK
        string role
    }
    SOLVER_RUNS {
        int id PK
        string version_label
        string algorithm
        string status
        datetime started_at
        datetime ended_at
        int hard_violations_count
        int soft_violations_count
        json config
        string notes
    }
    TIMETABLE_ENTRIES {
        int id PK
        int version_id FK
        int section_id FK
        int subject_id FK
        int faculty_id FK
        int room_id FK
        int time_slot_id FK
        string entry_type
        bool is_clash
        string clash_reason
        int span_periods
    }
    CLASH_REPORTS {
        int id PK
        int version_id FK
        string clash_type
        int room_id FK
        int time_slot_id FK
        int section_a_id FK
        int section_b_id FK
        string description
    }

    SECTIONS ||--o{ SECTION_SUBJECTS : "assigned"
    SUBJECTS ||--o{ SECTION_SUBJECTS : "teaches"
    SECTION_SUBJECTS ||--o{ MULTI_FACULTY_ASSIGNMENTS : "has TAs"
    SOLVER_RUNS ||--o{ TIMETABLE_ENTRIES : "version"
    SOLVER_RUNS ||--o{ CLASH_REPORTS : "reports"
```

---

## 13. API Contract Reference

### 13.1 Timetable & Versions API

| Method | Endpoint | Request | Response |
|---|---|---|---|
| GET | `/api/v1/timetable/versions` | — | `[{id, version_label, effective_date, hard_violations_count}]` |
| GET | `/api/v1/timetable/version/:id` | `?section_name=II AIML-A` | `{slots: [SlotEntry]}` |
| GET | `/api/v1/timetable/faculty/:id` | `?version_id=5` | `{faculty_name, total_hours, entries}` |
| PATCH | `/api/v1/timetable/entries/:id` | `{new_time_slot_id, new_room_id}` | `200 OK` |
| POST | `/api/v1/timetable/validate-move` | `{entry_id, new_day, new_period}` | `{valid, violations}` |
| GET | `/api/v1/validate/:version_id` | — | `{hard_violations, soft_violations, clashes:[]}` |

### 13.2 Import / Solver API

| Method | Endpoint | Request | Response |
|---|---|---|---|
| POST | `/api/v1/import/excel` | `multipart file` | `{version_id, sections, slots, clashes}` |
| POST | `/api/v1/solve` | `{algorithm}` | `{run_id, status}` |
| WS | `/api/v1/solve/:run_id/stream` | — | `SolverMessage stream` |
| POST | `/api/v1/solve/generate-from-wizard` | `TimetableGenerationRequest` | `{status, version_id, violations}` |

### 13.3 Configure API

| Method | Endpoint | Body | Response |
|---|---|---|---|
| GET | `/api/v1/faculty` | — | `[Faculty]` |
| POST | `/api/v1/configure/faculty` | `{name, designation, ...}` | `Faculty` |
| PATCH | `/api/v1/configure/faculty/:id` | `Partial<Faculty>` | `Faculty` |
| DELETE | `/api/v1/configure/faculty/:id` | — | `204` |
| GET | `/api/v1/rooms` | — | `[Room]` |
| POST | `/api/v1/configure/rooms` | `{code, room_type, capacity, ...}` | `Room` |
| GET | `/api/v1/subjects` | — | `[Subject]` |
| POST | `/api/v1/configure/subjects` | `{code, full_name, lecture_hours, ...}` | `Subject` |
| POST | `/api/v1/section-subjects/batch-assign` | `BatchAssignRequest` | `{mapping_id}` |

### 13.4 Export API

| Method | Endpoint | Params | Response |
|---|---|---|---|
| POST | `/api/v1/export/excel` | `?version_id=5` | `.xlsx blob` |
| GET | `/api/v1/export/excel/cohorts` | — | `[{key, label, sections:[]}]` |
| POST | `/api/v1/export/excel/cohort/:key` | `?version_id=5` | `.xlsx blob` |
| POST | `/api/v1/export/excel/minors-honors` | `?version_id=5` | `.xlsx blob` |
| POST | `/api/v1/export/pdf/sections` | `?version_id=5` | `.pdf blob` |
| POST | `/api/v1/export/pdf/faculty` | `?version_id=5` | `.pdf blob` |
| GET | `/api/v1/export/pdf/faculty/:id` | `?version_id=5` | `.pdf blob` |

---

## 14. Test Architecture & Coverage Gates

### 14.1 Test Pyramid

```mermaid
graph TD
    subgraph "Unit Tests"
        UT1["test_ga_solver.py\nFitness function, GA optimizer"]
        UT2["test_incremental_validator.py\nO(1) move validation, room conflict"]
        UT3["test_parser.py\nV5 baseline: exactly 51 room clashes"]
        UT4["test_solver.py\nCP-SAT basic constraint solve"]
    end

    subgraph "Service Layer Tests"
        ST1["test_services.py (7 tests)\nFaculty, Room, Section, Timetable,\nValidate, Export, IncrementalValidator,\nInfeasibility Diagnostics"]
    end

    subgraph "Integration / API Tests"
        IT1["test_api_routes.py (6 tests)\nHealth, list faculty/rooms/sections,\nvalidate, trigger solve"]
        IT2["test_api_import.py\nEnd-to-end Excel import"]
        IT3["test_configure_api.py\nFull CRUD via HTTP"]
        IT4["test_export.py (3 tests)\nExcel, PDF, SmartClass sync"]
    end

    subgraph "Wizard E2E Tests"
        E2E1["test_wizard_solve.py (3 tests)\nBasic wizard solve\nMulti-faculty lab solve\nIII-year minor honors solve"]
    end

    UT1 & UT2 & UT3 & UT4 --> ST1
    ST1 --> IT1 & IT2 & IT3 & IT4
    IT1 --> E2E1
```

### 14.2 Coverage Gate Requirements

| Layer | Min Coverage | Current |
|---|---|---|
| Constraint tests | 100% (20/20 rules) | ✅ |
| Parser tests | 90% | ✅ V5 baseline verified |
| API endpoint tests | 80% | ✅ all routes smoke-tested |
| Solver output tests | 100% | ✅ output validated before DB write |
| Total suite | — | ✅ 29/29 PASSED |

---

## 15. Infrastructure & Deployment

### 15.1 Docker Compose Service Topology

```mermaid
graph TD
    subgraph "Docker Compose Network: time_table_default"
        PG["vfstr_postgres\npostgres:16-alpine\nport 5432\nVolume: postgres_data"]
        REDIS["vfstr_redis\nredis:7-alpine\nport 6379"]
        BE["vfstr_backend\nFastAPI / Python 3.13\nport 8000\nDepends: postgres, redis"]
        FE["vfstr_frontend\nNext.js 14 / Node 20\nport 3000\nDepends: backend"]
        CW["vfstr_celery_worker\nSame image as backend\nDepends: postgres, redis\ncommand: celery -A tasks.celery_app worker"]
    end

    PG --> BE
    REDIS --> BE
    REDIS --> CW
    PG --> CW
    BE --> FE
```

### 15.2 Container Build Pipeline

```mermaid
sequenceDiagram
    participant DEV as Developer
    participant DC as Docker Compose
    participant BLD as Docker BuildKit

    DEV->>DC: docker compose up -d --build
    DC->>BLD: Build backend image (Python 3.13 + OR-Tools)
    BLD->>BLD: pip install -r requirements.txt\n(FastAPI, SQLAlchemy, Celery, ortools, openpyxl)
    BLD-->>DC: time_table-backend:latest

    DC->>BLD: Build frontend image (Node 20 multi-stage)
    BLD->>BLD: Stage 1 (deps): npm ci --legacy-peer-deps
    BLD->>BLD: Stage 2 (builder): npm run build → .next/standalone
    BLD->>BLD: Stage 3 (runner): minimal runtime image
    BLD-->>DC: time_table-frontend:latest

    DC->>DC: Start postgres → redis → backend → celery → frontend
    DC-->>DEV: All 5 containers healthy
```

### 15.3 Environment Variables Reference

| Variable | Service | Value |
|---|---|---|
| `DATABASE_URL` | backend, celery | `postgresql://vfstr:password@vfstr_postgres:5432/timetable_db` |
| `REDIS_URL` | backend | `redis://vfstr_redis:6379/0` |
| `CELERY_BROKER_URL` | celery | `redis://vfstr_redis:6379/0` |
| `CELERY_RESULT_BACKEND` | celery | `redis://vfstr_redis:6379/1` |
| `NEXT_PUBLIC_API_URL` | frontend | `http://localhost:8000` |
| `NEXT_PUBLIC_WS_URL` | frontend | `ws://localhost:8000` |
| `SOLVER_DEFAULT_TIMEOUT` | backend | `120` |
| `SOLVER_MAX_WORKERS` | backend | `8` |

### 15.4 Makefile Quick Commands

```mermaid
graph LR
    MAKE_UP["make up\ndocker compose up -d"]
    MAKE_SEED["make seed\nImport V5 Excel into DB"]
    MAKE_TEST["make test\npytest backend/tests/ -v"]
    MAKE_VAL["make validate\nV5 baseline: expect 51 clashes"]
    MAKE_DOWN["make down\ndocker compose down"]
    MAKE_LOGS["make logs\ndocker compose logs -f"]

    MAKE_UP --> MAKE_SEED
    MAKE_SEED --> MAKE_VAL
    MAKE_VAL --> MAKE_TEST
```

---

*End of VFSTR ACSE Timetable Scheduler — Production Engineering Reference & Architecture Manual*
