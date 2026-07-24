from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.section_service import SectionService

router = APIRouter()


@router.get("", response_model=Dict[str, Any])
async def list_sections(
    branch: Optional[str] = Query(None, description="Filter by branch code (e.g. AIML, CS)"),
    year: Optional[int] = Query(None, description="Filter by year (2, 3, 4)"),
    db: AsyncSession = Depends(get_db)
):
    return await SectionService.list_sections(db=db, branch=branch, year=year)
