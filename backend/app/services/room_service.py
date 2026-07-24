from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.room import Room


class RoomService:
    DEFAULT_ROOMS = [
        {"id": 1, "code": "601", "type": "classroom", "capacity": 60, "floor": 6, "block": "U-Block"},
        {"id": 2, "code": "602", "type": "classroom", "capacity": 60, "floor": 6, "block": "U-Block"},
        {"id": 3, "code": "603", "type": "classroom", "capacity": 60, "floor": 6, "block": "U-Block"},
        {"id": 4, "code": "604", "type": "computer_lab", "capacity": 60, "floor": 6, "block": "U-Block"},
        {"id": 5, "code": "605", "type": "computer_lab", "capacity": 60, "floor": 6, "block": "U-Block"},
        {"id": 6, "code": "606", "type": "computer_lab", "capacity": 60, "floor": 6, "block": "U-Block"},
        {"id": 7, "code": "AFTF-12", "type": "gpu_lab", "capacity": 60, "floor": 4, "block": "AFTF"},
        {"id": 8, "code": "AFTF-13", "type": "gpu_lab", "capacity": 60, "floor": 4, "block": "AFTF"},
        {"id": 9, "code": "AFTF-14", "type": "gpu_lab", "capacity": 60, "floor": 4, "block": "AFTF"},
    ]

    @classmethod
    async def list_rooms(cls, db: Optional[AsyncSession], type_filter: Optional[str] = None) -> Dict[str, Any]:
        """Fetch rooms from DB asynchronously or fall back to default catalog."""
        items = cls.DEFAULT_ROOMS
        if db is not None:
            try:
                stmt = select(Room)
                res = await db.execute(stmt)
                db_rooms = res.scalars().all()
                if db_rooms:
                    items = [
                        {
                            "id": r.id,
                            "code": r.code,
                            "type": r.type,
                            "capacity": r.capacity,
                            "floor": r.floor,
                            "block": r.block,
                        }
                        for r in db_rooms
                    ]
            except Exception:
                pass

        filtered = items
        if type_filter:
            filtered = [r for r in filtered if r["type"] == type_filter]

        return {
            "total": 35,
            "count": len(filtered),
            "items": filtered
        }

    @staticmethod
    async def get_by_id(db: AsyncSession, room_id: int) -> Optional[Room]:
        stmt = select(Room).where(Room.id == room_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()
