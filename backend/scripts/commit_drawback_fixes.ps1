# commit_drawback_fixes.ps1
# Staged Conventional Commits for Drawbacks Remediation

Set-Location "c:\Users\ggvfj\Downloads\All Projects\Time_Table"

Write-Host "Staging and committing drawback fixes..." -ForegroundColor Cyan

# Commit 1: Department cyclic FK
git add backend/app/models/department.py
git commit -m "fix(db): resolve cyclic foreign key dependency on departments head_faculty_id"

# Commit 2: Export service entry resolution
git add backend/app/services/export_service.py
git commit -m "fix(export): resolve timetable entries safely and eliminate raw_faculty_text attribute error"

# Commit 3: Wizard solve faculty associations
git add backend/app/api/v1/wizard_solve.py
git commit -m "fix(wizard): correctly populate faculty IDs and create timetable entry faculty associations"

# Commit 4: Substitute dispatcher co-instructor preservation
git add backend/app/services/substitute_dispatcher.py
git commit -m "fix(substitute): preserve lab co-instructors during faculty substitution dispatch"

# Commit 5: Multi-agent scheduler dispute repair context
git add backend/app/services/multi_agent_scheduler.py
git commit -m "fix(agent): propagate disrupted room and faculty context to local repair during multi-agent disputes"

# Commit 6: CSAT Solver and Hierarchical Decomposer collision avoidance
git add backend/solver/csat_solver.py backend/app/solver/hierarchical_decomposer.py
git commit -m "fix(solver): dynamic collision check for available rooms and cross-year decomposition isolation"

# Commit 7: Calendar Sync Service dynamic reference and UNTIL
git add backend/app/services/calendar_sync_service.py
git commit -m "fix(calendar): dynamic reference monday and academic semester UNTIL boundaries for RFC 5545 iCalendar"

# Commit 8: Solve service persistence and websocket streaming
git add backend/app/services/solve_service.py backend/app/api/v1/solve.py
git commit -m "fix(solve): remove section truncation, persist timetable versions via AsyncSessionLocal, and stream real progress"

# Commit 9: Conflict Checker extended rules
git add backend/solver/conflict_checker.py
git commit -m "feat(constraints): expand extended constraint checks with check_extended_rules while preserving V5 baseline"

# Commit 10: Auth router, login endpoints, CORS and test
git add backend/app/api/v1/auth.py backend/app/api/v1/router.py backend/main.py backend/tests/test_auth.py
git commit -m "feat(auth): implement JWT login, OAuth2 token endpoints, and verify role-based profile retrieval"

# Commit 11: Frontend dashboard stats and cell tooltip alignment
git add frontend/src/app/page.tsx frontend/src/components/timetable/TimetableGrid.tsx
git commit -m "fix(ui): align dashboard default statistics with canonical VFSTR baseline and enhance timetable cell tooltips"

Write-Host "All drawback fixes successfully committed!" -ForegroundColor Green
git status
