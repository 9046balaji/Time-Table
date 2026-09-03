from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.section import Section
from app.models.branch import Branch
from app.core.seed_cache import get_seed_data


class SectionService:
    @classmethod
    def _get_seed_sections(cls) -> List[Dict[str, Any]]:
        seed = get_seed_data()
        sec_list = seed.get("sections", [])
        if sec_list:
            res = []
            for idx, s in enumerate(sec_list, start=1):
                sname = str(s.get("name") or s.get("id"))
                y_val = int(s.get("year_level", 2))
                bcode = "CSBS" if "CSBS" in sname else ("IOT" if "IOT" in sname else ("DS" if "DS" in sname else ("CS" if "CS" in sname else "AIML")))
                res.append({
                    "id": s.get("id", idx),
                    "name": sname,
                    "branch": bcode,
                    "year": y_val,
                    "year_level": f"{y_val}nd Year" if y_val == 2 else (f"{y_val}rd Year" if y_val == 3 else f"{y_val}th Year"),
                    "strength": int(s.get("strength", 60))
                })
            return res
        return []

    @classmethod
    async def list_sections(cls, db: Optional[AsyncSession], branch: Optional[str] = None, year: Optional[int] = None) -> Dict[str, Any]:
        """Fetch section records from DB asynchronously or fall back to seed catalog."""
        items: List[Dict[str, Any]] = []
        if db is not None:
            try:
                stmt = select(Section)
                res = await db.execute(stmt)
                db_sections = res.scalars().all()
                if db_sections:
                    items = []
                    for s in db_sections:
                        s_name = s.name or ""
                        b_code = s.branch.code if getattr(s, "branch", None) else ("CSBS" if "CSBS" in s_name else ("IOT" if "IOT" in s_name else ("DS" if "DS" in s_name else ("CS" if "CS" in s_name else "AIML"))))
                        y_num = getattr(s, "year_level", 2) or 2

                        items.append({
                            "id": s.id,
                            "name": s.name,
                            "branch": b_code,
                            "year": y_num,
                            "year_level": f"{y_num}nd Year" if y_num == 2 else (f"{y_num}rd Year" if y_num == 3 else f"{y_num}th Year"),
                            "strength": getattr(s, "strength", 60)
                        })
            except Exception as ex:
                print(f"[SectionService DB Error] {ex}")

        if not items:
            items = cls._get_seed_sections()

        filtered = items
        if branch and branch != "ALL":
            filtered = [s for s in filtered if branch in str(s["branch"]) or str(s["branch"]) in branch]
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
