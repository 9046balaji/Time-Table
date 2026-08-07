from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.section import Section
from app.repositories.base_repository import BaseRepository


class SectionRepository(BaseRepository[Section]):
    """Encapsulated database access repository for Section entities."""
    def __init__(self, db: AsyncSession):
        super().__init__(Section, db)

    async def find_by_filters(
        self,
        year_level: Optional[int] = None,
        branch_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[Section]:
        query = select(Section)
        if year_level is not None:
            query = query.where(Section.year_level == year_level)
        if branch_id is not None:
            query = query.where(Section.branch_id == branch_id)
        if search:
            query = query.where(Section.name.ilike(f"%{search}%"))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> Optional[Section]:
        query = select(Section).where(Section.name == name)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
