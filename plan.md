Yes. Based on your current implementation and the AGENTATHON rules, I would **not rebuild the project**. I would convert your existing timetable optimization platform into an **autonomous academic scheduling agent**.

## Detailed execution plan

### Phase 1 — Agent foundation
- Add persistent agent session and event tables.
- Create a tool registry for timetable state inspection, conflict detection, validation, repair, rollback, and publishing.
- Add deterministic orchestration loop: observe → plan → validate → apply → notify.
- Expose a minimal agent API layer for session creation and event handling.

### Phase 2 — Local adaptive repair
- Detect impacted timetable entries after a room or faculty outage.
- Freeze unaffected entries.
- Run a scoped CP-SAT repair around the impacted cells only.
- Validate the whole timetable before applying changes.
- Compare before/after metrics and change cost.

### Phase 3 — Approval and rollback safety
- Risk-scoring for changes.
- Human approval flow for high-risk changes.
- Versioned schedule rollback if the repair fails or is rejected.
- Audit trail for actions, events, decisions, and validations.

### Phase 4 — Event-driven mission simulator
- Add room unavailable, faculty unavailable, capacity change, and priority change scenarios.
- Trigger the agent automatically and capture the decision trace.
- Show before/after metrics for each scenario.

### Phase 5 — Agent console and presentation UI
- Build a dedicated agent dashboard with mission, actions, decision trace, event stream, and approval controls.
- Show the realtime activity and score comparison.
- Keep the UI aligned with the existing design system.

### Feature milestones
1. Agent session creation and event capture
2. Room outage simulation and repair recommendation
3. Validation gate before schedule publication
4. Approve/reject and rollback controls
5. Mission simulator with multiple scenarios
6. Presentation-ready agent dashboard

### Delivery order
- Start with one tightly scoped feature that works end-to-end.
- Once the backend API contract and UI are stable, move to the next feature.
- Avoid adding broad multi-agent complexity before the single-agent loop is proven.

Your current foundation is already substantial: Next.js + FastAPI + PostgreSQL/Redis, CP-SAT + GA, Excel import/export, conflict validation, Celery, Docker, 20 constraints, 29 tests, and a real V5 baseline containing 51 room conflicts.   

The missing part is the **autonomous control layer**.

# 1. Final system you should build

I would position it as:

# VFSTR Adaptive Academic Scheduling Agent

### Core mission

> Given an academic scheduling goal, the agent observes the current campus scheduling state, reasons about constraints and priorities, plans a solution, invokes optimization and validation tools, performs approved changes, monitors the result, and automatically replans when conditions change.

The important word is **Adaptive**.

Your final architecture should be:

```text
                    ┌──────────────────────┐
                    │       USER/ADMIN     │
                    │ "Schedule next week" │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │    AGENT ORCHESTRATOR │
                    │                      │
                    │ Goal Understanding  │
                    │ State Analysis      │
                    │ Planning            │
                    │ Decision Making     │
                    │ Policy/Safety       │
                    └──────────┬───────────┘
                               ↓
             ┌─────────────────┼─────────────────┐
             ↓                 ↓                 ↓
        State Tools       Planning Tools     Policy Tools
             ↓                 ↓                 ↓
        PostgreSQL        CP-SAT + GA       Constraints
             ↓                 ↓                 ↓
             └─────────────────┼─────────────────┘
                               ↓
                       Validation Engine
                               ↓
                         Action Manager
                               ↓
                   Notification / Approval
                               ↓
                          Environment
                               ↓
                         Feedback/Event
                               ↓
                      ┌─────────────────┐
                      │  RE-PLANNING    │
                      └─────────────────┘
```

That is the system you should demonstrate.

---

# 2. What you already have

Do **not** throw these away.

| Existing component      | Keep? | Why                                  |
| ----------------------- | ----- | ------------------------------------ |
| Next.js frontend        | ✅     | Excellent demo surface               |
| FastAPI                 | ✅     | Agent/tool APIs can live here        |
| PostgreSQL              | ✅     | Agent state + campus data            |
| Redis                   | ✅     | Queue/cache/event handling           |
| Celery                  | ✅     | Long-running solver jobs             |
| OR-Tools CP-SAT         | ✅     | Deterministic hard-constraint solver |
| Genetic Algorithm       | ✅     | Soft optimization                    |
| Excel import            | ✅     | Real-world input                     |
| Conflict validator      | ✅     | Agent feedback/ground truth          |
| Excel/PDF export        | ✅     | Final action/output                  |
| Docker Compose          | ✅     | Reproducible demo                    |
| Existing 20 constraints | ✅     | Core scheduling logic                |
| Existing tests          | ✅     | Regression protection                |
| Timetable grid          | ✅     | Visual proof                         |
| Drag/drop validation    | ✅     | Human override                       |

Your project already separates solver, backend, persistence, UI and deployment reasonably well. 

---

# 3. What is missing

You need to add these:

```text
1. Agent Orchestrator
2. Agent State
3. Tool Registry
4. Goal Interpreter
5. Planning/Decision Layer
6. Event Detector
7. Re-planning Engine
8. Action Manager
9. Human Approval Gate
10. Notification System
11. Agent Memory
12. Agent Audit Log
13. Agent Evaluation Metrics
14. Mystery Mission simulator
15. Agent Console UI
```

These are the **actual improvements**.

---

# 4. Most important architectural change

Your current architecture is roughly:

```text
Input
 ↓
Solver
 ↓
Timetable
```

Change it to:

```text
Goal
 ↓
Agent
 ↓
Observe
 ↓
Reason
 ↓
Plan
 ↓
Tools
 ↓
Solver
 ↓
Validate
 ↓
Act
 ↓
Observe result
 ↓
Adapt
 ↓
Re-plan
```

Your CP-SAT and GA should **not become the agent**.

They should become **tools used by the agent**.

That's a critical architectural distinction.

---

# 5. Exact Agent responsibilities

The agent should be responsible for:

### Understanding

Example:

> "Create next week's timetable and prioritize final-year students."

It needs to turn that into structured objectives:

```json
{
  "goal": "generate_timetable",
  "scope": "next_week",
  "priority": [
    "final_year",
    "hard_constraints",
    "faculty_availability"
  ]
}
```

### Perception

The agent reads:

* current timetable
* rooms
* faculty
* sections
* subjects
* availability
* constraints
* recent changes
* conflicts
* solver history
* pending incidents

### Reasoning

It determines:

* what is wrong
* what is affected
* what is possible
* what should be prioritized
* which tools should be used
* whether human approval is required

### Planning

It produces a structured plan:

```text
1. Load current timetable.
2. Identify unavailable rooms.
3. Find affected classes.
4. Search alternative rooms.
5. Run local repair.
6. Validate.
7. Compare with existing schedule.
8. Request approval if risk is high.
9. Publish.
10. Notify users.
```

### Tool use

It actually invokes APIs.

### Action

It modifies the schedule or creates an operational request.

### Feedback

It checks whether the change worked.

### Adaptation

It changes the plan when reality changes.

---

# 6. Tool layer you should build

This is one of the highest-priority pieces.

Create an internal tool registry.

## Tool category 1 — State tools

```text
get_current_timetable()
get_sections()
get_subjects()
get_faculty()
get_rooms()
get_faculty_availability()
get_room_availability()
get_constraints()
get_solver_history()
get_active_incidents()
```

---

## Tool category 2 — Analysis tools

```text
detect_conflicts()
calculate_room_utilization()
calculate_faculty_workload()
find_affected_classes()
calculate_student_gaps()
calculate_schedule_quality()
compare_timetables()
```

---

## Tool category 3 — Planning tools

```text
generate_candidate_plan()
find_alternative_room()
find_alternative_faculty()
find_alternative_timeslot()
build_repair_plan()
```

---

## Tool category 4 — Optimization tools

Your existing solver becomes:

```text
run_cpsat()
run_genetic_optimizer()
run_full_optimization()
run_local_repair()
```

---

## Tool category 5 — Validation

```text
validate_hard_constraints()
calculate_soft_penalty()
validate_room_capacity()
validate_faculty_schedule()
validate_section_schedule()
```

The validator becomes the **ground-truth authority**.

The LLM should never be allowed to declare:

> "The schedule looks valid."

Your validator must decide that.

---

## Tool category 6 — Actions

```text
apply_timetable_change()
save_schedule_version()
publish_schedule()
rollback_schedule()
create_admin_approval()
send_notification()
```

---

# 7. Build a real agent state

Your agent needs an explicit state object.

Something like:

```python
class AgentState:
    goal: str

    current_timetable_id: str

    affected_sections: list[str]
    affected_faculty: list[str]
    affected_rooms: list[str]

    active_constraints: dict
    priorities: dict

    current_plan: list
    completed_actions: list
    failed_actions: list

    candidate_solutions: list

    validation_result: dict

    approval_required: bool

    approval_status: str

    iteration: int
```

This makes the workflow traceable.

---

# 8. Agent memory

Your PostgreSQL database is already a good foundation.

Add explicit agent tables.

## `agent_sessions`

```text
id
goal
status
created_at
completed_at
current_plan
current_step
```

## `agent_events`

```text
id
session_id
event_type
source
payload
timestamp
```

Examples:

```text
ROOM_UNAVAILABLE
FACULTY_UNAVAILABLE
NEW_SECTION
TIMETABLE_CHANGE
USER_REQUEST
CONSTRAINT_CHANGE
SOLVER_FAILURE
VALIDATION_FAILURE
```

## `agent_actions`

```text
id
session_id
tool_name
arguments
result
status
timestamp
```

## `agent_decisions`

```text
id
session_id
decision_type
reason_code
selected_option
alternatives
timestamp
```

## `approval_requests`

```text
id
session_id
action
risk_level
reason
status
approved_by
timestamp
```

## `agent_runs`

```text
id
session_id
iteration
objective_score
hard_violations
soft_penalty
status
```

This gives you an actual **agent audit trail**.

---

# 9. Very important: don't store fake "chain of thought"

For your demo, don't try to expose hidden reasoning.

Instead expose **structured decision traces**:

```text
Goal:
Repair timetable after room U-204 became unavailable.

Observation:
7 timetable entries use U-204.

Decision:
Repair affected entries locally.

Constraint:
Room capacity must remain >= section strength.

Action:
Search 12 compatible rooms.

Result:
3 candidates available.

Next:
Run local CP-SAT repair.

Validation:
0 hard violations.

Status:
Awaiting approval.
```

That is transparent and useful without pretending to reveal private reasoning.

---

# 10. Create the event system

This is essential for the Mystery Mission.

Your system needs an event endpoint:

```http
POST /api/v1/events
```

Example:

```json
{
  "type": "ROOM_UNAVAILABLE",
  "room_id": "U204",
  "effective_from": "2026-08-22T08:00:00",
  "reason": "Maintenance"
}
```

The event goes:

```text
Event
 ↓
Event handler
 ↓
Agent
 ↓
Impact analysis
 ↓
Plan
 ↓
Repair
 ↓
Validate
```

---

# 11. Mystery Mission engine

I strongly recommend building a **simulation panel**.

This can be one of your best demo features.

Create:

```text
Agent Mission Simulator
```

Buttons:

```text
[Room unavailable]

[Faculty unavailable]

[Room capacity reduced]

[New section added]

[Class cancelled]

[Priority changed]

[Lab unavailable]

[Multiple rooms unavailable]

[Faculty workload limit changed]
```

When clicked, it modifies the environment.

Then the agent reacts automatically.

This makes your Round 2 preparation dramatically easier.

---

# 12. Your most important agent scenario

Build this first.

# Scenario: Room Failure

### Initial state

V6 timetable is valid.

```text
Hard violations = 0
```

Then:

```text
MYSTERY EVENT

Room: AFTF-GPU-01
Status: UNAVAILABLE
Affected classes: 6
```

Agent:

```text
Detect
 ↓
Find impact
 ↓
Classify severity
 ↓
Generate repair strategy
 ↓
Search rooms
 ↓
Run local optimization
 ↓
Validate
 ↓
Compare
 ↓
Approve/apply
 ↓
Notify
```

This alone can demonstrate almost the entire competition requirement.

---

# 13. Build at least 5 mystery scenarios

Don't stop at one.

### M1 — Room failure

```text
one room unavailable
```

### M2 — Faculty absence

```text
faculty unavailable for one day
```

### M3 — Multiple room failure

```text
3 rooms unavailable
```

### M4 — Priority change

```text
final year students get priority
```

### M5 — Capacity change

```text
section grows from 50 → 80
```

Optional:

### M6 — New class

```text
new course added
```

### M7 — Lab failure

```text
GPU lab unavailable
```

### M8 — Constraint modification

```text
maximum daily teaching = 3
```

---

# 14. Build "local repair", not only full regeneration

This is one of the improvements I would prioritize most.

Suppose:

```text
1000 timetable entries
```

and only:

```text
6 entries affected
```

Don't automatically regenerate everything.

The agent should ask:

> Can I repair the affected region while preserving the existing schedule?

Architecture:

```text
Current timetable
       ↓
Identify affected entries
       ↓
Freeze unaffected entries
       ↓
CP-SAT repairs affected region
       ↓
Validate entire timetable
```

This gives you a strong technical story:

> **Minimal-disruption schedule repair**

That's much more impressive than simply rerunning the solver.

---

# 15. Build a priority engine

Not all constraints have the same importance.

Create priority levels.

### Priority 1 — Safety / correctness

```text
room conflict
faculty double booking
section conflict
room capacity
faculty availability
```

### Priority 2 — Academic requirements

```text
required subject hours
lab continuity
exam-related constraints
```

### Priority 3 — Preferences

```text
faculty workload
student gaps
preferred rooms
morning labs
Saturday usage
```

Then let the agent reason:

> "I cannot satisfy every preference. I will preserve hard and academic constraints and sacrifice the lowest-priority preference."

That gives you real decision-making.

---

# 16. Add a schedule quality score

Don't only say:

> Valid / Invalid.

Create:

```text
Schedule Quality
```

For example:

```text
Hard violations:          0
Soft penalty:             342
Faculty overload:         0
Student gaps:             41
Room utilization:         82%
Preference satisfaction:  91%
Change cost:              12
```

Then calculate:

```text
overall_score
```

The agent can compare plans.

Example:

```text
Plan A
Hard = 0
Soft = 420
Changes = 12

Plan B
Hard = 0
Soft = 350
Changes = 27
```

The agent might select A or B depending on the user's objective.

This is real decision-making.

---

# 17. Add change cost

This is another excellent improvement.

If a generated repair changes 100 classes, that's disruptive.

Therefore introduce:

```text
change_cost
```

For example:

```text
no change = 0
same room/time = 0
time changed = 1
room changed = 1
faculty changed = 5
multiple related changes = higher cost
```

Now the agent optimizes:

```text
schedule quality
+
minimal disruption
```

This is very useful for live adaptation.

---

# 18. Add human approval

The competition explicitly asks for human intervention for critical actions.

You can implement:

```text
Risk = LOW
    ↓
Auto-apply

Risk = MEDIUM
    ↓
Admin review

Risk = HIGH
    ↓
Mandatory approval
```

Example:

### Low risk

Move one normal class to another equivalent room.

### High risk

Change:

* many faculty assignments
* final-year classes
* examination periods
* critical labs

Then:

```text
Agent recommendation
        ↓
Human approval
        ↓
Action
```

---

# 19. Rollback is mandatory for a strong demo

Every agent action that changes the schedule should create a version.

Your project already has `solver_runs` and version history, so extend that concept. 

Implement:

```text
Version 1
Version 2
Version 3
```

Then:

```text
[Apply]
[Reject]
[Rollback]
[Compare]
```

Mystery mission:

> Agent changes timetable.

Judge:

> "No, that's worse."

You can show:

```text
Rollback → previous valid state
```

Very strong for reliability.

---

# 20. Notification/action system

The agent needs to do something outside the solver.

Create a notification abstraction:

```text
notify_student()
notify_faculty()
notify_admin()
```

For the competition, you don't need actual WhatsApp integration.

You can make a simulated notification center:

```text
Notifications

09:45
Room U204 unavailable.

09:46
Agent identified 7 affected classes.

09:47
New timetable proposed.

09:47
3 faculty members affected.

09:48
Schedule published after approval.
```

This is enough to demonstrate action.

---

# 21. Add natural-language commands

This is where your agent becomes very easy to demo.

Admin should be able to write:

> "Generate the timetable for II AIML, but prioritize GPU labs in the morning."

Agent translates this into structured parameters.

Or:

> "Professor Rao is unavailable on Thursday afternoon."

Agent:

```text
parse
 ↓
find faculty
 ↓
find affected classes
 ↓
repair
```

Or:

> "Make sure final-year classes don't have more than one gap."

Agent changes optimization objectives.

---

# 22. Agent shouldn't be able to arbitrarily modify constraints

Create a policy layer.

For example:

```text
Allowed automatically:
- room substitution
- normal elective rescheduling

Require approval:
- faculty reassignment
- major timetable change
- exam-related change
- policy modification
```

This prevents the LLM from making dangerous changes.

---

# 23. Agent failure handling

The competition explicitly requires error handling/recovery.

Build these cases:

### Solver timeout

```text
CP-SAT timeout
 ↓
Agent detects failure
 ↓
Try reduced scope
 ↓
Relax lowest priority soft constraint
 ↓
Retry
```

### No room available

```text
No compatible room
 ↓
Agent searches alternatives
 ↓
Check time relocation
 ↓
Try another room type
 ↓
Escalate if impossible
```

### Impossible constraints

```text
No feasible schedule
 ↓
Explain conflicting constraints
 ↓
Identify minimal relaxation
 ↓
Ask human approval
```

This is excellent Agentic AI behavior.

---

# 24. This should be your recovery strategy

For example:

```text
Attempt 1
Full constraints
      ↓
FAIL

Attempt 2
Same hard constraints
+ relaxed low-priority preferences
      ↓
FAIL

Attempt 3
Freeze less important entries
+ local repair
      ↓
SUCCESS

If still FAIL
      ↓
Human approval
```

This is far better than:

```text
solver failed → error
```

---

# 25. Build "why impossible?" capability

This is very valuable.

Suppose there are:

* 3 labs
* 8 lab courses
* only 2 morning slots
* faculty availability restrictions

The agent should say:

> "A conflict-free schedule is impossible under the current constraints because 8 required lab sessions need 8 lab-slot assignments, while only 6 compatible lab slots are available."

You can expose the underlying solver evidence.

This will impress judges more than vague LLM explanations.

---

# 26. Agent UI you should add

Your current pages are already strong. 

Add one:

# `/agent`

### Section 1 — Mission

```text
Current Mission

Generate clash-free timetable for
III AIML + II AIML
```

### Section 2 — Current State

```text
44 sections
80 faculty
35 rooms

0 hard conflicts
342 soft penalty
```

### Section 3 — Agent activity

```text
✓ Inspected timetable
✓ Found affected room
✓ Calculated impact
✓ Generated repair plan
✓ Called local solver
✓ Validation passed
```

### Section 4 — Current decision

```text
Agent proposes:

Move:
AIML-III → Room A203
Period 4 → Period 6

Reason code:
Room failure / minimum disruption
```

### Section 5

```text
[Approve]
[Reject]
[Rollback]
```

### Section 6

```text
Mystery Mission
[Room unavailable]
[Faculty unavailable]
[New event]
[Capacity change]
```

This will become the center of the live presentation.

---

# 27. Agent architecture inside FastAPI

Your existing `/api/v1/` structure can be extended.

Current project already has areas for configuration, import, solving, timetable, export and telemetry. 

Add:

```text
/api/v1/agent/
```

For example:

```text
POST /agent/sessions
GET  /agent/sessions/{id}

POST /agent/observe
POST /agent/plan
POST /agent/execute
POST /agent/events
POST /agent/approve
POST /agent/reject
POST /agent/rollback

GET  /agent/actions
GET  /agent/events
GET  /agent/decisions
GET  /agent/metrics

POST /agent/simulate/room-failure
POST /agent/simulate/faculty-failure
POST /agent/simulate/capacity-change
```

You don't necessarily need every endpoint separately; the key is to keep the agent's responsibilities explicit.

---

# 28. State-machine design

For reliability, I strongly recommend a state machine.

```text
IDLE
 ↓
UNDERSTANDING_GOAL
 ↓
OBSERVING
 ↓
ANALYZING
 ↓
PLANNING
 ↓
EXECUTING
 ↓
VALIDATING
 ↓
    ┌───────────────┐
    │               │
 SUCCESS          FAILURE
    │               │
    ↓               ↓
REVIEW          RECOVERY
    │               │
    ↓               ↓
APPROVAL ←────── REPLAN
    │
    ↓
APPLY
    ↓
NOTIFY
    ↓
MONITOR
```

This gives you a deterministic agent loop while allowing an LLM to make higher-level decisions.

---

# 29. What model should do what?

Don't let the model solve everything.

### LLM/Agent model

Use for:

* interpreting user goal
* selecting tools
* understanding natural language changes
* selecting priorities
* deciding between strategies
* generating human-readable explanations

### CP-SAT

Use for:

* hard constraint feasibility
* schedule assignment
* constraint satisfaction

### GA

Use for:

* soft optimization

### Python deterministic functions

Use for:

* metrics
* validation
* calculations
* conflict detection

### PostgreSQL

Use for:

* persistent state

This separation is one of the strongest technical aspects of the project.

---

# 30. Data you must have

Your current database already contains the core entities. 

For the agent, make sure you have:

```text
Department
Branch
Year
Section
Subject
Subject requirement
Faculty
Faculty availability
Faculty workload
Room
Room type
Room capacity
Time slot
Timetable entry
Constraint
Schedule version
Solver run
Agent session
Agent event
Agent action
Agent decision
Approval request
Notification
```

---

# 31. One important improvement to the current project

Your documentation lists:

> hardcoded room lists in wizard

as a known issue. 

Fix this before the Agentathon.

The agent must query:

```text
get_rooms()
```

rather than depend on hardcoded UI data.

Otherwise you will create a fake agent where the database says one thing but the agent UI says another.

---

# 32. Also fix constraint-data inconsistencies

Your documentation already mentions:

> minor break period mapping inconsistencies

and soft-constraint weighting needing tuning. 

These become **more important** once you add an agent.

The agent relies on the solver and validator as truth.

So:

> **Data correctness > LLM intelligence.**

Fix those first.

---

# 33. Your test strategy must grow

You currently document 29 passing tests. 

Add tests for the agent.

### Unit tests

```text
goal parsing
tool selection
priority calculation
risk classification
event parsing
```

### Integration tests

```text
room failure → repair
faculty failure → repair
capacity change → repair
```

### Safety tests

```text
high-risk change → approval
unauthorized action → blocked
```

### Failure tests

```text
solver timeout
no room available
invalid input
database unavailable
```

### Regression tests

```text
agent repair must keep hard constraints at 0
```

---

# 34. Exact success metrics

You need measurable metrics for your final presentation.

## Metric 1

```text
Hard Constraint Violations
Before = 51 baseline room conflicts
After = 0
```

Your current project already documents the V5 baseline of 51 and the V6 goal of zero hard conflicts. 

## Metric 2

```text
Repair time
```

Example:

> Room failure → new valid timetable in X seconds.

Measure it honestly after implementation.

## Metric 3

```text
Number of affected entries
```

Example:

> 7 entries affected → 7-entry repair instead of rebuilding 1,000+ entries.

## Metric 4

```text
Change cost
```

How disruptive was the repair?

## Metric 5

```text
Adaptation success rate
```

For your predefined Mystery Missions:

```text
M1 ✅
M2 ✅
M3 ✅
M4 ✅
M5 ✅
```

## Metric 6

```text
Human intervention rate
```

How many decisions were automatically resolved vs requiring approval?

---

# 35. The final demo should look like this

This is the sequence I would rehearse.

## 0:00–0:40 — Explain problem

> "V5 was manually maintained and contained 51 room conflicts."

Show actual data.

---

## 0:40–1:10 — Start mission

You type:

> "Generate a conflict-free schedule for the selected academic scope, minimizing faculty overload and student gaps."

Agent:

```text
Observe
Plan
Execute
Validate
```

Show live activity.

---

## 1:10–2:00 — Show result

```text
Hard conflicts: 0
Soft score: ...
Schedule generated
```

Show timetable.

---

## 2:00–2:30 — Introduce Mystery Mission

Judge:

> "Room U204 is unavailable."

You click the simulated event.

---

## 2:30–3:30 — Agent adapts

```text
Room failure detected
 ↓
7 classes affected
 ↓
3 alternatives found
 ↓
Local repair selected
 ↓
CP-SAT
 ↓
Validation
 ↓
0 hard conflicts
```

---

## 3:30–4:00 — Show decision

Agent says:

> "Plan B provides the lowest disruption while preserving all hard constraints."

Show:

```text
Before
After
Changed classes
Quality score
Change cost
```

---

## 4:00–4:30 — Human approval

Agent says:

> "2 faculty assignments change. Approval required."

Click:

**Approve**

---

## 4:30–5:00 — Action

```text
Schedule updated
Version V7 created
Notifications generated
```

---

## 5:00–5:30 — Second unexpected event

For example:

> "Professor X becomes unavailable."

Agent handles it.

Now the judges have seen **two adaptation cycles**.

---

# 36. The exact development priority

Do **not** develop everything simultaneously.

I would use this order.

## Phase 1 — Stabilize existing system

Fix:

* hardcoded room list
* break mapping
* soft-constraint weights
* database/UI consistency
* any remaining solver edge cases

Your own project documentation already identifies these issues. 

---

# Phase 2 — Extract existing functionality into tools

Turn current backend operations into:

```text
get_state
detect_conflicts
run_solver
repair_schedule
validate
publish
rollback
```

This is foundational.

---

# Phase 3 — Build Agent Orchestrator

Implement:

```text
Goal
 ↓
Observe
 ↓
Plan
 ↓
Tool execution
 ↓
Validate
 ↓
Decision
```

Start with a deterministic state machine.

Then add the LLM layer for natural-language goal interpretation and strategy selection.

---

# Phase 4 — Build adaptation

Implement events:

```text
room failure
faculty failure
capacity change
new class
priority change
```

Then:

```text
event
 ↓
impact analysis
 ↓
local repair
 ↓
validation
```

---

# Phase 5 — Add human approval

Implement:

```text
risk classification
approval request
approve/reject
rollback
```

---

# Phase 6 — Build Agent Console

Add:

```text
mission
state
events
agent activity
plan
proposed action
approval
metrics
```

---

# Phase 7 — Build Mystery Mission Simulator

Create the buttons/scenarios.

This will allow you to rehearse Round 2 repeatedly.

---

# Phase 8 — Evaluation

Run 20–50 randomized disruption scenarios.

Measure:

```text
success rate
repair time
hard violations
soft penalty
change cost
number of affected entries
recovery attempts
human escalation
```

Then your presentation contains **real experimental evidence**, rather than claims.

---

# 37. What is absolutely mandatory

If your time is limited, these are the non-negotiable items:

```text
✅ Existing CP-SAT + GA
✅ Agent orchestrator
✅ Tool layer
✅ Persistent agent state
✅ Event handling
✅ Local timetable repair
✅ Validation feedback
✅ Automatic re-planning
✅ At least 3 Mystery Missions
✅ Human approval
✅ Rollback
✅ Agent activity UI
✅ Measurable before/after metrics
```

---

# 38. What is nice but not necessary

These can wait:

```text
🟡 voice interface
🟡 mobile app
🟡 actual WhatsApp integration
🟡 advanced analytics
🟡 predictive room demand
🟡 IoT sensor integration
🟡 multi-agent architecture
🟡 fancy animations
```

Don't waste your AGENTATHON build time on them.

---

# 39. Should you use multi-agent?

Not initially.

Your competition says multi-agent systems are a possible theme, but it does **not** require multiple agents.

A strong single agent is better than five fake agents.

Your architecture can later be:

```text
Supervisor Agent

├── Scheduling Agent
├── Conflict Agent
├── Resource Agent
└── Notification Agent
```

But I'd only do this if the single-agent system is already working.

---

# 40. If you want the multi-agent version later

A sensible version would be:

```text
                   Supervisor
                       │
       ┌───────────────┼────────────────┐
       ↓               ↓                ↓
 Resource Agent   Schedule Agent   Policy Agent
       │               │                │
       └───────────────┼────────────────┘
                       ↓
                 Validation Agent
```

But don't make multi-agent architecture the selling point.

Your selling point should be:

# **Autonomous adaptation under changing campus constraints.**

---

# 41. What makes this better than a normal timetable project?

A normal timetable system:

```text
Input
 ↓
Generate
 ↓
Done
```

Your final system:

```text
Goal
 ↓
Understand
 ↓
Observe current campus state
 ↓
Reason
 ↓
Plan
 ↓
Select tools
 ↓
Optimize
 ↓
Validate
 ↓
Act
 ↓
Monitor
 ↓
Detect environmental change
 ↓
Re-plan
 ↓
Repair with minimal disruption
 ↓
Request approval when required
 ↓
Publish
 ↓
Rollback if necessary
```

That's a genuine Agentic AI story.

---

# 42. Final target architecture

This is the architecture I would aim to reach:

```text
                         ┌──────────────────┐
                         │      ADMIN       │
                         │ Natural Language │
                         └────────┬─────────┘
                                  ↓
                    ┌───────────────────────────┐
                    │     AGENT ORCHESTRATOR    │
                    │                           │
                    │ Goal Interpreter          │
                    │ State Manager             │
                    │ Planner                   │
                    │ Policy Engine             │
                    │ Risk Manager              │
                    └─────────────┬─────────────┘
                                  ↓
                    ┌───────────────────────────┐
                    │       TOOL REGISTRY       │
                    └─────────────┬─────────────┘
                                  │
        ┌──────────┬──────────────┼───────────────┬──────────┐
        ↓          ↓              ↓               ↓          ↓
     Database   Analyzer      CP-SAT/GA      Validator   Notifier
        │          │              │               │          │
        └──────────┴──────────────┼───────────────┴──────────┘
                                  ↓
                            ACTION MANAGER
                                  ↓
                         Human Approval Gate
                                  ↓
                              PostgreSQL
                                  ↓
                            New Schedule
                                  ↓
                              FEEDBACK
                                  ↓
                           EVENT DETECTOR
                                  ↓
                           AGENT RE-PLAN
```

---

# 43. The final product in one sentence

Your project should evolve from:

> **"A system that automatically generates timetables."**

to:

> **"An autonomous academic scheduling agent that continuously manages, repairs, validates and adapts university timetables in response to changing resources, constraints and priorities."**

That is the transformation I would make.

And importantly, **your current implementation gives you most of the hard deterministic infrastructure already**: the real dataset/problem, constraint model, CP-SAT/GA engine, validation, persistence, UI and deployment.  

The work ahead is therefore primarily **agent orchestration + environmental events + adaptive repair + safety/approval + a convincing live demonstration**, rather than rebuilding your scheduler.











Viewed plan.md:1-200
Viewed reccomended_plan.md:1-329

Here is an in-depth analysis of **`plan.md`**, **`reccomended_plan.md`**, and **`problems.md`**, mapped directly against our codebase implementation and architectural reality.

---

# 🏛️ In-Depth Architectural & Feature Review

## 1. Executive Summary & Core Philosophy

The fundamental shift across all three documents is moving from a **Static Solver Generator** (*Input → CP-SAT → Output*) to an **Adaptive Autonomous Agent Platform**:

```
Goal / Disruption Event
         ↓
  AGENT ORCHESTRATOR  ──►  Observe State (DB / Schedule / Rooms)
         ↓
    Reason & Plan     ──►  Select Repair Strategy (Local Scoped CP-SAT)
         ↓
   Execute Tools      ──►  Tool Registry (get_rooms, run_local_repair)
         ↓
  Validation Gate     ──►  ConflictChecker (Zero Hard Clashes Required)
         ↓
Multi-Agent Consensus ──►  3 Roles (VALIDATOR [Veto], ARCHITECT, SOLVER)
         ↓
 Human Approval Gate  ──►  Risk Score, Diff View, Approve or 1-Click Rollback
```

> **The Golden Rule (from `reccomended_plan.md`):**
> *"Do not make the LLM or Solver the authority on validity. The Agent decides what to do, Tool calls execute, the Validator decides if it is valid (0 hard clashes), and only then apply/publish."*

---

## 2. In-Depth Breakdown of the 3 Blueprint Documents

### 📄 Document A: `plan.md` (Master Agent Blueprint)
* **Objective:** Upgrade the existing timetable optimization engine into an **Autonomous Adaptive Scheduling Agent**.
* **Key Concept:** **Minimal Disruption Principle** — When a room breaks or a professor is absent, do **not** re-solve the entire 1,000-slot university schedule. Freeze 99% of unaffected entries and run a scoped CP-SAT repair only around the impacted cells.
* **5 Key Phases Defined:**
  1. *Agent Foundation:* Persistent DB state (`agent_sessions`, `agent_events`, `agent_actions`, `agent_decisions`, `agent_runs`).
  2. *Local Adaptive Repair:* Freeze unaffected cells, run scoped CP-SAT local repair.
  3. *Approval & Rollback Safety:* Risk-scoring, human approval gate, versioned schedule rollback.
  4. *Event-Driven Mission Simulator:* Real-world campus disruption scenarios (`room_failure`, `gpu_lab_failure`, `faculty_absence`, `capacity_surge`, `priority_reroute`, `constraint_modification`).
  5. *Agent Mission Console UI:* Dedicated `/agent` dashboard with decision trace telemetry, event stream, and diff view.

---

### 📄 Document B: `reccomended_plan.md` (Execution Strategy & Gap Analysis)
* **Objective:** Reuse 100% of the solid existing foundation (FastAPI, Next.js, CP-SAT, PostgreSQL, Redis, Celery, 20 Constraints, V5 Baseline) rather than rebuilding.
* **Key Guidance:**
  - **Tool Registry:** The agent calls specialized tools (`get_rooms()`, `detect_conflicts()`, `run_local_repair()`, `rollback_schedule()`) instead of querying raw DB tables directly.
  - **State Machine:** Enforce strict status loops: `OBSERVE` → `PLAN` → `VALIDATE` → `HUMAN_APPROVAL` → `APPLY`.

---

### 📄 Document C: `problems.md` (13-Point Risk & Reliability Audit)
Surfaces critical production risks and technical safeguards:

| Risk / Bottleneck | Identified Issue | Codebase Solution Implemented |
|---|---|---|
| **Risk G (Data Integrity)** | Raw text string mismatch vs DB foreign keys | Added `GET /api/v1/agent/health/data-integrity` to audit raw text resolution to FKs |
| **Risk F (DoS Rate Limit)** | Rapid simulation calls exhausting CPU/RAM | Enforced 1-second simulation cooldown per session in [agent.py](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/backend/app/api/v1/agent.py#L57) |
| **Bottleneck 2.2 (Cell Overrides)** | Concurrent manual slot edits creating room clashes | Integrated `ConflictChecker` inside `update_timetable_slot()` transaction in [timetable.py](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/backend/app/api/v1/timetable.py#L188) |
| **Bottleneck 1.1 (CP-SAT Scale)** | `UNKNOWN` (timeout) vs `INFEASIBLE` (no solution) | Distinguish timeout retry vs `explain_infeasibility()` diagnostic |
| **Risk E (Event Ordering)** | Near-simultaneous disruption ordering | Monotonically increasing `sequence_number` on `agent_events` |
| **Risk A (State Corruption)** | Agent stuck in `REPAIRING` state | `session_timeout_at` detection and auto-recovery |

---

## 3. What Our Agents Do (Complete Feature Inventory)

Here is the exact feature capability matrix built into the Agent platform:

### 1. 🚨 Campus Disruption Perception & Local Repair
* **Room / Infrastructure Failure (`room_failure`):** Detects emergency room lockouts (e.g., Room `604`) and automatically re-routes affected classes to open replacement rooms in the same time slot while maintaining 97%+ schedule stability.
* **GPU High-Performance Lab Outage (`gpu_lab_failure`):** Re-routes AI/ML/DL practical sessions from an offline GPU lab (e.g., `AFTF-12`) to alternate GPU-capable lab blocks.
* **Faculty Unplanned Absence (`faculty_absence`):** Re-allocates assigned slots when an instructor reports leave.
* **Capacity Surge (`capacity_surge`):** Audits section enrollment surges exceeding room capacity (e.g., Room `601` with 95 students) and bumps the section to a larger venue.
* **Cohort Priority Reroute (`priority_reroute`):** Re-aligns morning slot preferences for final-year cohorts.
* **Global Constraint Shift (`constraint_adjustment`):** Dynamically applies or relaxes global constraint rules (e.g., `HC-08` lab consecutiveness).

---

### 2. 🏛️ Multi-Agent Consensus Protocol (3 Specialized Roles)
When evaluating any schedule modification, 3 sub-agents vote:
- **🧪 VALIDATOR (VETO Power):** Runs ground-truth constraint detection. Vetoes any candidate schedule with `> 0` hard violations (room clashes, faculty double-booking, section overlaps).
- **🏗️ ARCHITECT:** Queries DB room metadata to verify capacity requirements and lab equipment compatibility.
- **⚙️ SOLVER:** Evaluates soft constraint optimization (e.g., minimizing late P7-P8 period fatigue and faculty gap hours).

---

### 3. 📡 Live Telemetry & Real-Time Decision Trace
- **WebSocket Streaming (`ws://.../api/v1/agent/stream/{session_id}`):** Pushes live incident events, repair progress, and status updates directly to connected frontend clients without manual page refreshes.
- **Natural Language Directive Parser:** Converts natural admin text (e.g., `"Room 604 is closed for maintenance"`) into structured scenario parameters.

---

### 4. 🛡️ Human-in-the-Loop Approval & 1-Click Rollback
- **Schedule Diff View:** Highlights exact slot movements (original vs. repaired room and time slot), weighted change costs, and affected sections.
- **Human Gate:** Requires explicit coordinator approval (`Approve Local Repair`) before changes are committed to the master database.
- **1-Click Rollback:** Instantly restores the pre-disruption timetable snapshot if a repair is rejected.

---

## 4. Codebase Mapping Reference

| Architectural Component | Backend Implementation File | Frontend UI Component |
|---|---|---|
| **Agent State & Persistence** | [backend/app/models/agent.py](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/backend/app/models/agent.py) | [Active Session Telemetry Card](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/frontend/src/app/agent/page.tsx#L282) |
| **Agent Service & Commands** | [backend/app/services/agent_service.py](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/backend/app/services/agent_service.py) | [Console Actions Header](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/frontend/src/app/agent/page.tsx#L213) |
| **Disruption Simulator** | [backend/app/services/mission_simulator.py](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/backend/app/services/mission_simulator.py) | [MissionSimulator.tsx](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/frontend/src/components/agent/MissionSimulator.tsx) |
| **Multi-Agent Consensus** | [backend/app/services/multi_agent_consensus.py](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/backend/app/services/multi_agent_consensus.py) | [DecisionTrace.tsx](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/frontend/src/components/agent/DecisionTrace.tsx) |
| **Tool Registry & Local Repair** | [backend/app/services/tool_registry.py](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/backend/app/services/tool_registry.py) | [DiffView.tsx](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/frontend/src/components/agent/DiffView.tsx) |
| **WebSocket Streaming** | [backend/app/services/agent_websocket_manager.py](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/backend/app/services/agent_websocket_manager.py) | `useEffect` WebSocket Stream in [page.tsx](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/frontend/src/app/agent/page.tsx#L205) |

---

## 5. Summary & Next Steps

Our system fully implements the 5-phase roadmap from `plan.md`, the authoritative validation loop from `reccomended_plan.md`, and the technical safeguards from `problems.md`.

All 6 Docker containers are **up and healthy**, and the Agent Mission Console (`/agent`) is live and operational.



For an **Adaptive Academic Scheduling Agent** to operate reliably in a **real-world production environment** (managing ~2,360 students, ~80 faculty, 35+ venues, and 48 weekly slots across 44 sections), it cannot be a simple script or an unvalidated LLM wrapper. 

It must act as an **autonomous, self-healing, human-gated co-pilot** that continuously perceives campus events, reasons about constraints, executes scoped repairs, verifies validity, and protects schedule stability.

Here is the **complete, end-to-end production specification** of what our agent does, its core capabilities, and every feature required for enterprise deployment:

---

# 🤖 Production-Grade Agent Architecture & Capabilities

```
                  ┌──────────────────────────────────────────────┐
                  │          CAMPUS DISRUPTION EVENTS            │
                  │ (Room Outage, Faculty Leave, Enrollment)    │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                           1. PERCEPTION & EVENT RADAR                             │
│ • Natural Language Command Parser ("Room 604 is closed for repairs")              │
│ • Monotonic Sequence Numbering & DoS Cooldown Protection                          │
└────────────────────────────────────────┬──────────────────────────────────────────┘
                                         │
                                         ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                  2. AUTONOMOUS REASONING & LOCAL REPAIR ENGINE                    │
│ • Minimal Disruption Principle: Freeze 99% of unaffected schedule                  │
│ • Multi-Stage CP-SAT Repair: Same-Slot Swap ➔ Slot Relaxation ➔ Safe Fallback    │
└────────────────────────────────────────┬──────────────────────────────────────────┘
                                         │
                                         ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│               3. MULTI-AGENT CONSENSUS PROTOCOL (3 SPECIALIZED ROLES)             │
│ 🧪 VALIDATOR (VETO Power): Ground-truth 0 Hard Violation Check                    │
│ 🏗️ ARCHITECT: Capacity Audit, GPU/Computer Lab Equipment Matching                │
│ ⚙️ SOLVER: Soft Constraint Optimization (SC-01..SC-10, Late Slot Penalties)       │
└────────────────────────────────────────┬──────────────────────────────────────────┘
                                         │
                                         ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│               4. RISK SCORING & HUMAN-IN-THE-LOOP APPROVAL GATE                   │
│ • Risk Level Engine: Low / Medium / High (Weighted Change Cost Model)             │
│ • Schedule Diff View: Interactive Before vs. After Cell Comparison                │
│ • Human Gate: Coordinator Approval ➔ DB Publication | Rejection ➔ 1-Click Rollback│
└────────────────────────────────────────┬──────────────────────────────────────────┘
                                         │
                                         ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                   5. LIVE TELEMETRY & WEBSOCKET STREAMING                         │
│ • Live WebSocket Broadcasts (ws://.../api/v1/agent/stream/{session_id})           │
│ • Audit Log Persistence (agent_sessions, agent_events, agent_actions, agent_runs) │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏛️ The 6 Core Production Pillars & Functionalities

### Pillar 1: Perception & Disruption Ingestion (The Event Radar)
In production, a schedule changes constantly throughout the semester. The agent must perceive and process 6 core disruption scenarios:
1. **Emergency Room Lockouts (`room_failure`):** e.g., Room `604` undergoes urgent maintenance.
2. **Hardware & GPU Outages (`gpu_lab_failure`):** e.g., Lab `AFTF-12` suffers a power failure; AI/ML sessions must move to GPU-capable replacement rooms.
3. **Faculty Absences (`faculty_absence`):** e.g., An instructor takes sudden medical leave.
4. **Student Capacity Surges (`capacity_surge`):** e.g., Section enrollment overflows room seating limits.
5. **Cohort Priority Preference Realignment (`priority_reroute`):** e.g., Granting morning slot preference to final-year cohorts (`IV AIML-A`).
6. **Global Constraint Shifts (`constraint_adjustment`):** Dynamically enforcing/relaxing constraint rules (e.g., `HC-08` lab consecutiveness).

* **Natural Language Command Processing:** Administrators can type directives into the console (e.g., *"Room 604 is closed today"*), and the agent parses intent into structured parameters.

---

### Pillar 2: Scoped Minimal-Disruption Repair Engine
* **The Minimal Disruption Principle:** Instead of re-solving the entire 1,000-slot university timetable (which would scramble everyone's schedule), the agent **freezes 99%+ of unaffected entries**.
* **Multi-Stage CP-SAT Repair Search:**
  - **Stage 1 (Strict Same-Slot Swap):** Re-allocates displaced classes to open rooms in the exact same time slot matching room type requirements.
  - **Stage 2 (Time Slot Relaxation):** Searches adjacent period slots on the same day if no same-slot room is available.
  - **Stage 3 (Safe Fallback Venue):** Assigns designated overflow venues if high congestion occurs.

---

### Pillar 3: Multi-Agent Consensus Protocol (Role-Based Voting)
Before any schedule change is published, **3 specialized sub-agent roles** evaluate the candidate repair:

1. **🧪 VALIDATOR Sub-Agent (Holds VETO Power):**
   - Executes ground-truth hard conflict detection across all 10 Hard Constraints (`HC-01` to `HC-10`).
   - **Veto Rule:** If `hard_violations > 0` (room clash, faculty double-booking, section conflict), the Validator immediately **VETOES** the repair.
2. **🏗️ ARCHITECT Sub-Agent:**
   - Queries PostgreSQL room metadata to verify seat capacity, floor accessibility, and specialized equipment (e.g., GPU support for AI labs).
3. **⚙️ SOLVER Sub-Agent:**
   - Evaluates soft constraint optimization (`SC-01` to `SC-10`), minimizing faculty gap hours and late-period (`P7-P8`) student fatigue.

---

### Pillar 4: Risk Scoring, Diff View & Human Approval Gate
Production systems must protect against accidental or bad AI decisions:
* **Weighted Change Cost Model & Risk Scoring:**
  - Time slot change = `1.0` point
  - Room change = `1.0` point
  - Faculty reassignment = `5.0` points
  - Multi-entry cascade = `1.5x` multiplier
  - Classifies change risk as **LOW**, **MEDIUM**, or **HIGH**.
* **Schedule Diff View:** Highlights exact slot movements (original vs. repaired room and time slot), showing stability percentage and displaced sections.
* **Human Approval Gate:** High-risk repairs require explicit admin sign-off (**Approve Local Repair**) before writing to the database.
* **1-Click Rollback:** Allows admins to instantly revert to the pre-disruption snapshot if a repair is rejected.

---

### Pillar 5: Production Reliability & Self-Healing Safeguards
* **Startup Data Integrity Audit (`GET /api/v1/agent/health/data-integrity`):** Audits raw text strings (`raw_faculty_text`, `raw_room_text`) against database Foreign Key records to prevent silent parsing bugs.
* **Transactional Conflict Validation:** When an admin performs a manual drag-and-drop cell edit, `ConflictChecker` runs within the same database transaction. If the move creates a clash, the transaction rolls back automatically.
* **Dead Session Recovery:** Detects sessions stuck in `REPAIRING` state past timeout thresholds and auto-recovers them.
* **DoS Cooldown Protection:** Enforces rate-limiting on simulation endpoints to prevent solver memory exhaustion.

---

### Pillar 6: Live Telemetry & Mission Control UI (`/agent`)
* **Real-Time WebSocket Streaming (`ws://.../api/v1/agent/stream/{session_id}`):** Streams decision logs, solver progress, and incident alerts live to the browser.
* **State Machine Telemetry:** Tracks the orchestration lifecycle: `OBSERVE` → `PLAN` → `VALIDATE` → `HUMAN_APPROVAL` → `APPLY`.
* **Persistent Audit Trail:** Logs all events, actions, decisions, and validations in dedicated database tables (`agent_sessions`, `agent_events`, `agent_actions`, `agent_decisions`, `agent_runs`).

---

## 📊 Complete Production Feature Summary Table

| Feature Domain | Production Functionality | Codebase File Location |
|---|---|---|
| **Disruption Ingestion** | Perception loop for room failures, lab outages, faculty leave & capacity surges | [mission_simulator.py](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/backend/app/services/mission_simulator.py) |
| **Local Repair Engine** | Minimal disruption CP-SAT solver freezing unaffected cells | [csat_solver.py](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/backend/solver/csat_solver.py) |
| **Multi-Agent Consensus** | 3-role voting (Validator [Veto], Architect, Solver) | [multi_agent_consensus.py](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/backend/app/services/multi_agent_consensus.py) |
| **Tool Registry** | Decoupled state inspection, conflict checking & repair tools | [tool_registry.py](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/backend/app/services/tool_registry.py) |
| **Human Approval & Rollback** | Risk classification, Diff View, 1-Click Rollback to pre-incident snapshot | [agent_service.py](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/backend/app/services/agent_service.py) |
| **Data Integrity Audit** | Raw text → FK resolution health endpoint | [timetable_service.py](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/backend/app/services/timetable_service.py) |
| **WebSocket Streaming** | Real-time event broadcasting to agent console | [agent_websocket_manager.py](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/backend/app/services/agent_websocket_manager.py) |
| **Mission Control Dashboard** | Next.js frontend with Decision Trace, Simulator & Diff View | [page.tsx](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/frontend/src/app/agent/page.tsx) |

---

## 🎯 Why This Architecture Wins Competitions & Enterprise Audits

1. **It is Authoritative, Not Probabilistic:** Hard constraint validation is determined by deterministic algorithms (`ConflictChecker`), not LLM text generation.
2. **It Preserves Schedule Stability:** University operations do not collapse when one room fails because 99% of the timetable remains frozen.
3. **It Keeps Humans in Control:** High-impact changes require explicit approval, backed by a 1-click safety rollback mechanism.
4. **It is Fully Auditable:** Every event, decision, tool invocation, and validation result is recorded in PostgreSQL.

In AI Agent architecture, **Memory** is what separates a simple "one-off solver script" from a **true autonomous production agent**. 

For a production agent in an enterprise environment (like university academic scheduling), the agent requires **4 distinct types of memory systems**, plus **memory retention and performance safeguards**.

Here is the complete breakdown of what memory an agent should have in production:

---

# 🧠 Production Agent Memory Architecture

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                              AGENT MEMORY ARCHITECTURE                            │
├───────────────────────────────────────────────────────────────────────────────────┤
│ 1. WORKING MEMORY (Short-Term State)                                              │
│    • Active Session Context, Goal, Current Step (OBSERVE ➔ PLAN ➔ VALIDATE ➔ APPLY)   │
│    • Live Disruption Parameters & Candidate Repair Entries                        │
├───────────────────────────────────────────────────────────────────────────────────┤
│ 2. EPISODIC MEMORY (Event & Action History)                                       │
│    • Sequential Disruption Event Log (agent_events with sequence_number)          │
│    • Tool Execution Audit Trail (agent_actions: tool_name, args, time_ms, status) │
│    • Decision Log (agent_decisions: rationale, consensus votes, risk score)       │
├───────────────────────────────────────────────────────────────────────────────────┤
│ 3. INSTITUTIONAL & SEMANTIC MEMORY (Long-Term Knowledge)                          │
│    • Campus Entity Graph: Rooms (type, capacity, GPU), Faculty (max hours, rank)  │
│    • Constraint Rules Engine: Hard Constraints (HC-01..HC-10) & Soft (SC-01..SC-10)│
│    • Versioned Snapshot Store: Historical pre-disruption timetable checkpoints    │
├───────────────────────────────────────────────────────────────────────────────────┤
│ 4. PROCEDURAL MEMORY (Repair Policies & Heuristics)                               │
│    • Minimal Disruption Policy (Freeze 99% of entries, repair affected 1%)        │
│    • Multi-stage venue search (Same-slot swap ➔ Slot relaxation ➔ Overflow venue) │
│    • Consensus Voting Rules (Validator VETO power, Architect capacity check)      │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. ⚡ Working Memory (Short-Term / Active Session State)

**What it is:** The agent's immediate scratchpad for the current mission or disruption cycle.

* **Session Context Object (`session.context`):**
  - **Goal & Priority:** e.g., `"Goal: Repair Room 604 failure | Priority: [hard_constraints, minimal_disruption]"`
  - **Active Step:** Current state in the state machine (`OBSERVE`, `PLAN`, `VALIDATE`, `HUMAN_APPROVAL`, `APPLY`).
  - **Active Disruption Parameters:** Affected room/faculty target, severity, and impacted sections list.
  - **Transient Candidate Entries:** The candidate timetable entries generated by the local solver before human approval.
* **Database Representation:** Stored in `agent_sessions.context` (JSONB) in PostgreSQL for real-time querying.

---

## 2. 📜 Episodic Memory (Event, Action & Decision Audit Trail)

**What it is:** A complete, chronological history of everything that happened during a session. This makes the agent **100% auditable and reproducible**.

* **Event Log (`agent_events`):**
  - Records every perception event with a monotonically increasing `sequence_number` (e.g., `MISSION_STARTED`, `ROOM_UNAVAILABLE`, `LOCAL_REPAIR_PROPOSED`, `CONSENSUS_APPROVED`).
* **Tool Execution Audit (`agent_actions`):**
  - Records every tool function called by the agent (e.g., `get_rooms`, `detect_conflicts`, `run_local_repair`, `rollback_schedule`).
  - Stores: `tool_name`, `arguments`, `execution_time_ms`, `status` (`success`/`failed`), and `result_payload`.
* **Decision History (`agent_decisions`):**
  - Stores the rationale behind actions, multi-agent consensus votes, risk levels, and human approval/rejection outcomes.

---

## 3. 📚 Institutional & Semantic Memory (Long-Term Knowledge)

**What it is:** The permanent knowledge base about the campus environment, domain rules, and historical schedule checkpoints.

* **Campus Infrastructure Graph:**
  - **Room Capabilities:** Capacities, floor levels, building blocks (`U-Block`, `Block-VI`), and hardware profiles (standard classroom vs computer lab vs high-performance GPU lab `AFTF-12`).
  - **Faculty Profiles:** Designation max weekly teaching hours (Prof: 12h, Assoc Prof: 14h, Asst Prof: 16h) and subject specializations.
  - **Section Cohorts:** Department sections, student counts, and special cohort restrictions (e.g., 4th Year `SL/EL` blocks, `MINORS/HONORS` global slots).
* **Constraint Knowledge Base:**
  - Hard Constraints (`HC-01` to `HC-10`: room conflicts, faculty double-booking, capacity limits, break times).
  - Soft Constraints (`SC-01` to `SC-10`: faculty gap hours, daily workload balance, late period `P7-P8` penalties).
* **Versioned Snapshot Store:**
  - Stores complete JSON snapshots of past valid schedules (`V1` through `V5` baselines and `pre_incident` checkpoints) enabling **1-Click Safety Rollback**.

---

## 4. ⚙️ Procedural Memory (Policies & Solver Heuristics)

**What it is:** The "how-to" knowledge — embedded algorithms and decision rules that tell the agent how to solve problems efficiently.

* **Minimal Disruption Policy:** Rule stating: *"When repairing an outage, freeze 99% of unaffected timetable entries and re-allocate only impacted cells."*
* **Multi-Stage Repair Search Heuristic:**
  - *Stage 1 (Strict Same-Slot Swap):* Look for open rooms of identical type in the exact same day/period.
  - *Stage 2 (Time Slot Relaxation):* Look for open rooms in adjacent periods on the same day.
  - *Stage 3 (Overflow Venue Fallback):* Move to designated fallback venues if high room saturation exists.
* **Multi-Agent Consensus Voting Rules:**
  - `VALIDATOR` holds **VETO** power (0 hard violations required).
  - `ARCHITECT` enforces capacity and equipment matching.
  - `SOLVER` enforces soft constraint thresholds (e.g., SC-07 late period fatigue $\le 40\%$).

---

## 🛡️ Memory Governance, Pruning & Performance Safeguards

In production, unmanaged memory causes database bloat, slow queries, and memory leaks. The agent implements 4 critical safeguards:

1. **Snapshot Retention Policy:**
   - Keeps only the last **10 candidate snapshots** per session in `session.context`. Older snapshots are automatically pruned to prevent database bloat.
2. **Session Timeouts & Dead Session Recovery (`session_timeout_at`):**
   - If an agent session crashes or gets stuck in `REPAIRING` state longer than 300 seconds, a background recovery process automatically marks the session `FAILED` and restores the last clean snapshot.
3. **DoS Cooldown & Rate Limiting:**
   - Enforces a 1-second cooldown per session on simulation triggers to prevent memory exhaustion from rapid API calls.
4. **Data Integrity Audit (`/health/data-integrity`):**
   - Startup health check auditing raw text entries vs database Foreign Key relations, ensuring memory references resolve accurately.

---

## 📊 Summary of Agent Memory Implementation in Our Codebase

| Memory Type | What it Stores | Implementation File |
|---|---|---|
| **Working Memory** | Active session goal, step, active disruption parameters, candidate repair | [backend/app/models/agent.py](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/backend/app/models/agent.py#L7) (`AgentSession`) |
| **Episodic Memory** | Monotonic event log, tool audit trail, consensus decision votes | [backend/app/models/agent.py](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/backend/app/models/agent.py#L33-L75) (`AgentEvent`, `AgentAction`, `AgentDecision`) |
| **Semantic Memory** | Room capacities, faculty max hours, versioned schedule snapshots | [backend/app/services/tool_registry.py](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/backend/app/services/tool_registry.py#L367) (`save_schedule_snapshot`) |
| **Procedural Memory** | Minimal disruption CP-SAT solver heuristics & multi-stage fallback | [backend/solver/csat_solver.py](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/backend/solver/csat_solver.py#L558) (`solve_local_repair`) |
| **Memory Safeguards** | Snapshot retention pruning, data integrity health audit, session timeouts | [backend/app/services/timetable_service.py](file:///c:/Users/ggvfj/Downloads/All%20Projects/Time_Table/backend/app/services/timetable_service.py#L231) (`check_data_integrity`) |