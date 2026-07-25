import time
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, List
try:
    from app.schemas.wizard import TimetableGenerationRequest, WizardGenerationResponse
except ImportError:
    from backend.app.schemas.wizard import TimetableGenerationRequest, WizardGenerationResponse
from backend.solver.csat_solver import CPSATSolver, SolverConfig

router = APIRouter()


@router.post("/generate-from-wizard", response_model=WizardGenerationResponse)
async def generate_from_wizard(req: TimetableGenerationRequest):
    """
    Ingests wizard parameters, maps assigned courses and preferred building block rooms,
    and runs the CP-SAT solver to generate a 100% clash-free timetable matrix.
    """
    start_time = time.time()

    if not req.sections:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one target section must be selected."
        )

    if not req.assignments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one course assignment must be provided."
        )

    # 1. Build Section metadata
    sections_list = [{"id": sec_name, "student_count": 60} for sec_name in req.sections]

    # 2. Build Section Subject Quotas & Faculty map
    section_subjects = []
    faculty_map: Dict[str, List[str]] = {}

    for sec in req.sections:
        for idx, assign in enumerate(req.assignments, start=101):
            sub_id = f"{assign.subject_code}_{idx}"
            co_facs = [co.strip() for co in getattr(assign, "co_faculty", []) if co.strip()]
            c_slots = getattr(assign, "continuous_slots", 2 if assign.subject_type == "P" else 1)

            section_subjects.append({
                "section_id": sec,
                "subject_id": sub_id,
                "subject_code": assign.subject_code,
                "subject_type": assign.subject_type,
                "total_slots_needed": assign.weekly_hours,
                "faculty_name": assign.faculty_name.strip(),
                "co_faculty": co_facs,
                "continuous_slots": c_slots
            })

            # Add primary faculty to map
            fac = assign.faculty_name.strip()
            if fac:
                if fac not in faculty_map:
                    faculty_map[fac] = []
                if assign.subject_code not in faculty_map[fac]:
                    faculty_map[fac].append(assign.subject_code)

            # Add co-instructors to map
            for co in co_facs:
                if co not in faculty_map:
                    faculty_map[co] = []
                if assign.subject_code not in faculty_map[co]:
                    faculty_map[co].append(assign.subject_code)

    # 3. Dynamic Room Pool (allows custom rooms if supplied or filters block pools)
    custom_rooms = getattr(req, "rooms", None)
    if custom_rooms:
        rooms_list = custom_rooms
    else:
        block_clean = req.preferred_block.lower()
        if "aftf" in block_clean or "gpu" in block_clean:
            rooms_list = [
                {"id": "AFTF-12", "capacity": 72, "room_type": "gpu_lab"},
                {"id": "AFTF-13", "capacity": 72, "room_type": "gpu_lab"},
                {"id": "AFTF-14", "capacity": 72, "room_type": "gpu_lab"},
                {"id": "601", "capacity": 66, "room_type": "classroom"},
                {"id": "602", "capacity": 66, "room_type": "classroom"},
            ]
        elif "h-block" in block_clean or "divisional" in block_clean:
            rooms_list = [
                {"id": "514-A", "capacity": 66, "room_type": "classroom"},
                {"id": "514-B", "capacity": 66, "room_type": "classroom"},
                {"id": "518", "capacity": 66, "room_type": "classroom"},
                {"id": "604", "capacity": 60, "room_type": "computer_lab"},
                {"id": "605", "capacity": 60, "room_type": "computer_lab"},
            ]
        else:
            # Default U-BLOCK / Block-VI (Aryabhatta Bhavan)
            rooms_list = [
                {"id": "601", "capacity": 66, "room_type": "classroom"},
                {"id": "602", "capacity": 66, "room_type": "classroom"},
                {"id": "603", "capacity": 66, "room_type": "classroom"},
                {"id": "607", "capacity": 66, "room_type": "classroom"},
                {"id": "608", "capacity": 66, "room_type": "classroom"},
                {"id": "614", "capacity": 66, "room_type": "classroom"},
                {"id": "619", "capacity": 66, "room_type": "classroom"},
                {"id": "215", "capacity": 66, "room_type": "classroom"},
                {"id": "218", "capacity": 66, "room_type": "classroom"},
                {"id": "604", "capacity": 60, "room_type": "computer_lab"},
                {"id": "605", "capacity": 60, "room_type": "computer_lab"},
                {"id": "606", "capacity": 60, "room_type": "computer_lab"},
                {"id": "611", "capacity": 60, "room_type": "computer_lab"},
                {"id": "616", "capacity": 60, "room_type": "computer_lab"},
            ]

    # 4. Build Time Slots (MON..SAT, Periods 1..8)
    # Note: Short break (09:55-10:10) is between P2 & P3; Lunch (12:40-13:40) is between P5 & P6.
    # All periods 1..8 are valid teaching periods.
    time_slots = []
    for day in ["MON", "TUE", "WED", "THU", "FRI", "SAT"]:
        for period in range(1, 9):
            time_slots.append({
                "id": f"{day}_{period}",
                "day": day,
                "period": period,
                "is_blocked": False
            })

    # 5. Execute Solver Engine
    solver_cfg = SolverConfig(algorithm="CP-SAT", timeout_seconds=60)
    solver = CPSATSolver(solver_cfg)

    max_cap = getattr(req, "max_classes_per_teacher_per_day", req.max_daily_teaching_hours)

    result = solver.solve(
        sections=sections_list,
        section_subjects=section_subjects,
        rooms=rooms_list,
        time_slots=time_slots,
        faculty_subject_map=faculty_map,
        max_classes_per_teacher_per_day=max_cap
    )

    elapsed = round(time.time() - start_time, 2)
    is_ok = result["status"] in ("OPTIMAL", "FEASIBLE")

    return WizardGenerationResponse(
        status=result["status"],
        runtime_seconds=elapsed,
        entries_count=result.get("entries_count", 0),
        hard_violations=result.get("hard_violations", 0),
        soft_violations=result.get("soft_violations", 0),
        message="✓ 100% Clash-Free Timetable Generated Successfully via AI Wizard!" if is_ok else "Infeasible: Resource constraints over-subscribed.",
        entries=result.get("entries", [])
    )
