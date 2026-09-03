from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.room import Room
from app.core.seed_cache import get_seed_data


class RoomService:
    @classmethod
    def _get_seed_rooms(cls) -> List[Dict[str, Any]]:
        seed = get_seed_data()
        rooms = seed.get("rooms", [])
        if rooms:
            return [
                {
                    "id": idx + 1,
                    "code": str(r.get("code") or r.get("id")),
                    "type": r.get("room_type", "classroom"),
                    "room_type": r.get("room_type", "classroom"),
                    "capacity": r.get("capacity", 60),
                    "floor": r.get("floor", "6"),
                    "block": r.get("block", "U-Block"),
                    "gpu_capable": r.get("gpu_capable", False),
                    "is_available": True,
                }
                for idx, r in enumerate(rooms)
            ]
        return []

    @classmethod
    async def list_rooms(cls, db: Optional[AsyncSession], type_filter: Optional[str] = None) -> Dict[str, Any]:
        """Fetch rooms from DB asynchronously or fall back to seed catalog."""
        items: List[Dict[str, Any]] = []
        if db is not None:
            try:
                stmt = select(Room)
                if type_filter:
                    stmt = stmt.where(Room.room_type == type_filter)
                res = await db.execute(stmt)
                db_rooms = res.scalars().all()
                if db_rooms:
                    items = [
                        {
                            "id": r.id,
                            "code": r.code,
                            "type": r.room_type,
                            "room_type": r.room_type,
                            "capacity": r.capacity,
                            "floor": r.floor,
                            "block": r.block,
                            "gpu_capable": r.gpu_capable,
                            "is_available": r.is_available,
                        }
                        for r in db_rooms
                    ]
            except Exception as ex:
                print(f"[RoomService Warning] DB fetch error: {ex}")

        if not items:
            items = cls._get_seed_rooms()

        if type_filter:
            items = [r for r in items if r.get("type") == type_filter or r.get("room_type") == type_filter]

        return {
            "total": len(items),
            "count": len(items),
            "items": items
        }



    @staticmethod
    async def get_by_id(db: AsyncSession, room_id: int) -> Optional[Room]:
        stmt = select(Room).where(Room.id == room_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()
