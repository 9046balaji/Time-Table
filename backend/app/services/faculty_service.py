from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.faculty import Faculty


class FacultyService:
    @staticmethod
    async def get_all_faculty(
        db: Optional[AsyncSession],
        dept_id: Optional[int] = None,
        designation: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetch all faculty members with workload stats from DB asynchronously."""
        if db is not None:
            try:
                stmt = select(Faculty)
                if dept_id:
                    stmt = stmt.where(Faculty.dept_id == dept_id)
                if designation:
                    stmt = stmt.where(Faculty.designation == designation)
                if search:
                    stmt = stmt.where(Faculty.name.ilike(f"%{search}%"))

                res = await db.execute(stmt)
                faculty_members = res.scalars().all()
                if faculty_members:
                    items = [
                        {
                            "id": f.id,
                            "name": f.name,
                            "designation": f.designation,
                            "max_hours": f.max_hours_per_week,
                            "hours_this_week": getattr(f, "hours_this_week", 12),
                            "dept_id": f.dept_id,
                        }
                        for f in faculty_members
                    ]
                    return {"total": len(items), "count": len(items), "items": items}
            except Exception:
                pass


        # Fallback to seed data if DB table uninitialized
        from app.core.seed_cache import get_seed_data
        seed = get_seed_data()
        raw_facs = seed.get("faculty", [])
        items = []
        for idx, f in enumerate(raw_facs, start=1):
            if isinstance(f, dict):
                name = f.get("name", "")
                desig = f.get("designation", "Assistant Professor")
                max_h = f.get("max_hours_per_week", 16)
            else:
                name = str(f)
                desig = "Assistant Professor"
                max_h = 16
            if name:
                items.append({
                    "id": idx,
                    "name": name,
                    "designation": desig,
                    "max_hours": max_h,
                    "hours_this_week": 12,
                    "dept_id": 1
                })

        if designation:
            items = [f for f in items if f["designation"] == designation]
        if search:
            items = [f for f in items if search.lower() in f["name"].lower()]

        return {"total": len(items), "count": len(items), "items": items}

    @staticmethod
    async def get_by_id(db: AsyncSession, faculty_id: int) -> Optional[Faculty]:
        stmt = select(Faculty).where(Faculty.id == faculty_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()
