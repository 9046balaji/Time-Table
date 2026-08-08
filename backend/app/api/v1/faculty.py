from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.faculty_service import FacultyService

router = APIRouter()


@router.get("", response_model=Dict[str, Any])
async def list_faculty(
    dept_id: Optional[int] = Query(None, description="Filter by department ID"),
    designation: Optional[str] = Query(None, description="Filter by rank/designation"),
    search: Optional[str] = Query(None, description="Search by faculty name"),
    db: AsyncSession = Depends(get_db)
):
    return await FacultyService.get_all_faculty(db=db, dept_id=dept_id, designation=designation, search=search)

