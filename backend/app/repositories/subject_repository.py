from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.subject import Subject
from app.repositories.base_repository import BaseRepository


class SubjectRepository(BaseRepository[Subject]):
    """Encapsulated database access repository for Curriculum Subject entities."""
    def __init__(self, db: AsyncSession):
        super().__init__(Subject, db)

    async def find_by_filters(
        self,
        slot_type: Optional[str] = None,
        is_lab: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[Subject]:
        query = select(Subject)
        if slot_type:
            query = query.where(Subject.slot_type == slot_type)
        if is_lab is not None:
            query = query.where(Subject.is_lab == is_lab)
        if search:
            query = query.where(
                (Subject.code.ilike(f"%{search}%")) | (Subject.full_name.ilike(f"%{search}%"))
            )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_code(self, code: str) -> Optional[Subject]:
        query = select(Subject).where(Subject.code == code)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
