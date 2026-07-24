from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.section import Section


class SectionService:
    DEFAULT_SECTIONS = [
        {"id": 1, "name": "II AIML-A", "branch": "AIML", "year": 2, "strength": 60},
        {"id": 2, "name": "II AIML-B", "branch": "AIML", "year": 2, "strength": 60},
        {"id": 3, "name": "II AIML-C", "branch": "AIML", "year": 2, "strength": 60},
        {"id": 4, "name": "II AIML-D", "branch": "AIML", "year": 2, "strength": 60},
        {"id": 5, "name": "II AIML-E", "branch": "AIML", "year": 2, "strength": 60},
        {"id": 6, "name": "II AIML-F", "branch": "AIML", "year": 2, "strength": 60},
        {"id": 7, "name": "II AIML-G", "branch": "AIML", "year": 2, "strength": 60},
        {"id": 8, "name": "II AIML-H", "branch": "AIML", "year": 2, "strength": 60},
        {"id": 9, "name": "II AIML-I", "branch": "AIML", "year": 2, "strength": 60},
        {"id": 10, "name": "II AIML-J", "branch": "AIML", "year": 2, "strength": 60},
        {"id": 11, "name": "II AIML-K", "branch": "AIML", "year": 2, "strength": 60},
        {"id": 12, "name": "II AIML-L", "branch": "AIML", "year": 2, "strength": 60},
        {"id": 13, "name": "III AIML-A", "branch": "AIML", "year": 3, "strength": 60},
        {"id": 14, "name": "III AIML-B", "branch": "AIML", "year": 3, "strength": 60},
        {"id": 15, "name": "III AIML-C", "branch": "AIML", "year": 3, "strength": 60},
        {"id": 16, "name": "III AIML-D", "branch": "AIML", "year": 3, "strength": 60},
        {"id": 17, "name": "III AIML-E", "branch": "AIML", "year": 3, "strength": 60},
        {"id": 18, "name": "III AIML-F", "branch": "AIML", "year": 3, "strength": 60},
        {"id": 19, "name": "III AIML-G", "branch": "AIML", "year": 3, "strength": 60},
        {"id": 20, "name": "IV AIML-A", "branch": "AIML", "year": 4, "strength": 60},
        {"id": 21, "name": "IV AIML-B", "branch": "AIML", "year": 4, "strength": 60},
        {"id": 22, "name": "IV AIML-C", "branch": "AIML", "year": 4, "strength": 60},
        {"id": 23, "name": "IV AIML-D", "branch": "AIML", "year": 4, "strength": 60},
        {"id": 24, "name": "IV AIML-E", "branch": "AIML", "year": 4, "strength": 60},
        {"id": 25, "name": "II CS-A", "branch": "CS", "year": 2, "strength": 60},
        {"id": 26, "name": "II CS-B", "branch": "CS", "year": 2, "strength": 60},
        {"id": 27, "name": "III CS", "branch": "CS", "year": 3, "strength": 60},
        {"id": 28, "name": "IV CS", "branch": "CS", "year": 4, "strength": 60},
        {"id": 29, "name": "II DS-A", "branch": "DS", "year": 2, "strength": 60},
        {"id": 30, "name": "II DS-B", "branch": "DS", "year": 2, "strength": 60},
        {"id": 31, "name": "III DS-A", "branch": "DS", "year": 3, "strength": 60},
        {"id": 32, "name": "III DS-B", "branch": "DS", "year": 3, "strength": 60},
        {"id": 33, "name": "IV DS", "branch": "DS", "year": 4, "strength": 60},
        {"id": 34, "name": "II CSBS", "branch": "CSBS", "year": 2, "strength": 60},
        {"id": 35, "name": "III CSBS", "branch": "CSBS", "year": 3, "strength": 60},
        {"id": 36, "name": "IV CSBS", "branch": "CSBS", "year": 4, "strength": 60},
        {"id": 37, "name": "II IOT", "branch": "IOT", "year": 2, "strength": 60},
        {"id": 38, "name": "III IOT", "branch": "IOT", "year": 3, "strength": 60},
        {"id": 39, "name": "II BS(DS)", "branch": "BS(DS)", "year": 2, "strength": 60},
        {"id": 40, "name": "III BS(DS)", "branch": "BS(DS)", "year": 3, "strength": 60},
        {"id": 41, "name": "II MSC(DS)", "branch": "MSC(DS)", "year": 2, "strength": 30},
        {"id": 42, "name": "II MTECH(DS)", "branch": "MTECH", "year": 2, "strength": 20},
        {"id": 43, "name": "MINOR/HONORS 1", "branch": "SPECIAL", "year": 3, "strength": 60},
        {"id": 44, "name": "MINOR/HONORS 2", "branch": "SPECIAL", "year": 4, "strength": 60},
    ]

    @classmethod
    async def list_sections(cls, db: Optional[AsyncSession], branch: Optional[str] = None, year: Optional[int] = None) -> Dict[str, Any]:
        """Fetch section records from DB asynchronously or fall back to default catalog."""
        items = cls.DEFAULT_SECTIONS
        if db is not None:
            try:
                stmt = select(Section)
                res = await db.execute(stmt)
                db_sections = res.scalars().all()
                if db_sections:
                    items = [
                        {
                            "id": s.id,
                            "name": s.name,
                            "branch": "AIML",
                            "year": s.label,
                            "strength": s.strength
                        }
                        for s in db_sections
                    ]
            except Exception:
                pass

        filtered = items
        if branch:
            filtered = [s for s in filtered if s["branch"] == branch]
        if year:
            filtered = [s for s in filtered if str(s["year"]) == str(year) or s.get("year") == year]

        return {
            "total": len(items),
            "count": len(filtered),
            "items": filtered
        }

    @staticmethod
    async def get_by_id(db: AsyncSession, section_id: int) -> Optional[Section]:
        stmt = select(Section).where(Section.id == section_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()
