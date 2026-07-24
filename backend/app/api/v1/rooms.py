from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.room_service import RoomService

router = APIRouter()


@router.get("", response_model=Dict[str, Any])
async def list_rooms(
    type: Optional[str] = Query(None, description="Filter by room type (classroom, computer_lab, gpu_lab)"),
    db: AsyncSession = Depends(get_db)
):
    return await RoomService.list_rooms(db=db, type_filter=type)
