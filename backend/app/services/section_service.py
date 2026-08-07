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
                    items = []
                    for s in db_sections:
                        s_name = s.name or ""
                        # Determine branch
                        if "AIML" in s_name:
                            b_code = "AIML"
                        elif "CSBS" in s_name:
                            b_code = "CSBS"
                        elif "CS" in s_name:
                            b_code = "CS"
                        elif "DS" in s_name:
                            b_code = "DS"
                        elif "IOT" in s_name:
                            b_code = "IOT"
                        else:
                            b_code = "AIML"
                        
                        # Determine year
                        if "II " in s_name or s_name.startswith("II"):
                            y_val = "II"
                        elif "III " in s_name or s_name.startswith("III"):
                            y_val = "III"
                        elif "IV " in s_name or s_name.startswith("IV"):
                            y_val = "IV"
                        else:
                            y_val = str(s.label if hasattr(s, "label") and s.label else "II")

                        items.append({
                            "id": s.id,
                            "name": s.name,
                            "branch": b_code,
                            "year": y_val,
                            "year_level": y_val,
                            "strength": getattr(s, "strength", 60)
                        })
            except Exception as ex:
                print(f"[SectionService DB Error] {ex}")

        filtered = items
        if branch and branch != "ALL":
            filtered = [s for s in filtered if branch in s["branch"] or s["branch"] in branch]
        if year and year != "ALL":
            filtered = [s for s in filtered if str(year) in str(s["year"]) or str(s["year"]) in str(year)]

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
