from fastapi import APIRouter, Depends
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.wizard_defaults_service import WizardDefaultsService

router = APIRouter()


@router.get("/wizard-defaults", response_model=Dict[str, Any])
async def get_wizard_defaults(db: AsyncSession = Depends(get_db)):
    """
    Returns live department defaults for the Timetable Creation Wizard:
    98 faculty members, 40 rooms, 44 sections, and standard year curricula.
    """
    return await WizardDefaultsService.get_wizard_defaults(db)
