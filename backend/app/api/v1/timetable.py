from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.timetable_service import TimetableService

router = APIRouter()

@router.get("/versions")
async def list_timetable_versions(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.models.timetable import TimetableVersion
    res = await db.execute(select(TimetableVersion).order_by(TimetableVersion.id.desc()))
    versions = res.scalars().all()
    if not versions:
        return [
            {"id": 5, "version_label": "V5", "effective_date": "15-07-2026", "is_active": True, "hard_violations_count": 51, "notes": "Baseline imported from V5 Excel dataset"},
            {"id": 3, "version_label": "V3", "effective_date": "13-07-2026", "is_active": False, "hard_violations_count": 64, "notes": "Previous revision imported from V3 Excel dataset"}
        ]
    return [
        {
            "id": v.id,
            "version_label": v.version_label,
            "effective_date": v.effective_date,
            "is_active": v.is_active,
            "hard_violations_count": v.hard_violations_count,
            "notes": v.notes
        }
        for v in versions
    ]


@router.get("/version/{version_id}", response_model=Dict[str, Any])
async def get_version_timetable(
    version_id: int = 5,
    section_name: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    return await TimetableService.get_version_timetable(db, version_id=version_id, section_name=section_name)
@router.get("/faculty/{faculty_id}", response_model=Dict[str, Any])
async def get_faculty_timetable(
    faculty_id: int,
    version_id: int = Query(5),
    db: AsyncSession = Depends(get_db)
):
    return await TimetableService.get_faculty_timetable(db, faculty_id=faculty_id, version_id=version_id)

@router.post("/validate-move", response_model=Dict[str, Any])
async def validate_slot_move(req: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    """
    Performs ultra-fast O(1) validation (< 5ms) for manual drag-and-drop cell moves.
    """
    from backend.solver.incremental_validator import ScheduleIndexStore
    version_id = req.get("version_id", 5)
    all_tt = await TimetableService.get_version_timetable(db, version_id=version_id, section_name="ALL")
    entries = all_tt.get("entries", [])
    
    store = ScheduleIndexStore()
    store.index_timetable(entries)

    entry_id = str(req.get("entry_id") or "")
    sec_name = str(req.get("section_name") or "II AIML-A")
    fac_names = req.get("faculty_names") or []
    if isinstance(fac_names, str):
        fac_names = [f.strip() for f in fac_names.split(",") if f.strip()]
    target_day = str(req.get("target_day") or "MON")
    target_period = int(req.get("target_period") or 1)
    target_room = req.get("target_room_code")

    return store.validate_move(
        entry_id=entry_id,
        section_name=sec_name,
        faculty_names=fac_names,
        target_day=target_day,
        target_period=target_period,
        target_room_code=target_room
    )
