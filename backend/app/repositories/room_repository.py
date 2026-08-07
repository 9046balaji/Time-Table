from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.room import Room
from app.repositories.base_repository import BaseRepository


class RoomRepository(BaseRepository[Room]):
    """Encapsulated database access repository for Room & Venue entities."""
    def __init__(self, db: AsyncSession):
        super().__init__(Room, db)

    async def find_by_filters(
        self,
        room_type: Optional[str] = None,
        block: Optional[str] = None,
        gpu_capable: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[Room]:
        query = select(Room)
        if room_type:
            query = query.where(Room.room_type == room_type)
        if block:
            query = query.where(Room.block == block)
        if gpu_capable is not None:
            query = query.where(Room.gpu_capable == gpu_capable)
        if search:
            query = query.where(Room.code.ilike(f"%{search}%"))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_code(self, code: str) -> Optional[Room]:
        query = select(Room).where(Room.code == code)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
