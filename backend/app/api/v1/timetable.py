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

@router.get("/{version_id}/section/{section_id}", response_model=Dict[str, Any])
async def get_section_timetable(version_id: int, section_id: int):
    return {
        "version_id": version_id,
        "section_id": section_id,
        "section_name": "II AIML-A",
        "entries": [
            {"day": "MON", "period": 1, "subject": "DS", "room": "619", "faculty": "Dr. S.Srikantha Reddy", "type": "L"},
            {"day": "MON", "period": 2, "subject": "DBMS", "room": "619", "faculty": "Ms. P Seetha Lakshmi", "type": "L"},
            {"day": "MON", "period": 3, "subject": "BREAK", "room": "", "faculty": "", "type": "BREAK"},
            {"day": "MON", "period": 4, "subject": "AI", "room": "607", "faculty": "Dr. B. Sudha Rani", "type": "L"},
            {"day": "MON", "period": 5, "subject": "OOPS", "room": "607", "faculty": "Ms. G. Mahalakshmi", "type": "L"},
            {"day": "MON", "period": 6, "subject": "LUNCH", "room": "", "faculty": "", "type": "LUNCH"},
            {"day": "MON", "period": 7, "subject": "SFCDS", "room": "215", "faculty": "Dr. P. Kalpana", "type": "L"},
        ]
    }
