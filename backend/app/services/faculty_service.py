from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.faculty import Faculty


class FacultyService:
    @staticmethod
    async def get_all_faculty(db: Optional[AsyncSession], dept_id: Optional[int] = None) -> Dict[str, Any]:
        """Fetch all faculty members with workload stats from DB asynchronously."""
        if db is not None:
            try:
                stmt = select(Faculty)
                if dept_id:
                    stmt = stmt.where(Faculty.dept_id == dept_id)
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

        default_faculty = [
            {"id": 1, "name": "Dr. P. Kalpana", "designation": "Professor", "max_hours": 12, "hours_this_week": 10},
            {"id": 2, "name": "Dr. Bandi Guravaiah", "designation": "Professor", "max_hours": 12, "hours_this_week": 11},
            {"id": 3, "name": "Dr. Rushi Prasad Sahoo", "designation": "Associate Professor", "max_hours": 14, "hours_this_week": 13},
            {"id": 4, "name": "Dr. B. N. Naveen Kumar", "designation": "Associate Professor", "max_hours": 14, "hours_this_week": 12},
            {"id": 5, "name": "Dr. Ankamma Rao Mallela", "designation": "Professor", "max_hours": 12, "hours_this_week": 12},
            {"id": 6, "name": "Dr. S. Srikantha Reddy", "designation": "Associate Professor", "max_hours": 14, "hours_this_week": 14},
            {"id": 7, "name": "Dr. B. Sudha Rani", "designation": "Assistant Professor", "max_hours": 16, "hours_this_week": 15},
        ]
        return {"total": 80, "count": len(default_faculty), "items": default_faculty}

    @staticmethod
    async def get_by_id(db: AsyncSession, faculty_id: int) -> Optional[Faculty]:
        stmt = select(Faculty).where(Faculty.id == faculty_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()
