from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.faculty import Faculty
from app.repositories.base_repository import BaseRepository


class FacultyRepository(BaseRepository[Faculty]):
    """Encapsulated database access repository for Faculty entities."""
    def __init__(self, db: AsyncSession):
        super().__init__(Faculty, db)

    async def find_by_filters(
        self,
        dept_id: Optional[int] = None,
        designation: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Faculty]:
        query = select(Faculty)
        if dept_id is not None:
            query = query.where(Faculty.dept_id == dept_id)
        if designation:
            query = query.where(Faculty.designation == designation)
        if search:
            query = query.where(Faculty.name.ilike(f"%{search}%"))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_employee_id(self, employee_id: str) -> Optional[Faculty]:
        query = select(Faculty).where(Faculty.employee_id == employee_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
