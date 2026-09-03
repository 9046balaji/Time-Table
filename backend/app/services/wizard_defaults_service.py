from typing import Dict, Any, List, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.faculty import Faculty
from app.models.room import Room
from app.models.section import Section
from app.core.seed_cache import get_seed_data


class WizardDefaultsService:
    @staticmethod
    async def get_wizard_defaults(db: Optional[AsyncSession] = None) -> Dict[str, Any]:
        """
        Dynamically extracts and structures real department faculty, rooms, sections,
        and standard branch/year curricula for the Timetable Creation Wizard.
        """
        seed = get_seed_data()
        
        # 1. Fetch Faculty Pool
        faculty_list = []
        if db is not None:
            try:
                res = await db.execute(select(Faculty).order_by(Faculty.name))
                fac_rows = res.scalars().all()
                if fac_rows:
                    faculty_list = [{"id": f.id, "name": f.name, "designation": f.designation or "Assistant Professor"} for f in fac_rows]
            except Exception as ex:
                print(f"[WizardDefaultsService DB Warning] {ex}")

        if not faculty_list:
            raw_facs = seed.get("faculty", [])
            seen_facs = set()
            for f in raw_facs:
                name = (f.get("name") if isinstance(f, dict) else str(f)).strip()
                if name.startswith("(P):") or name.startswith("(T):"):
                    name = name.split(":", 1)[1].strip()
                if name and name not in ["***", "undefined", "null"] and not name[0].isdigit() and name not in seen_facs:
                    seen_facs.add(name)
                    faculty_list.append({"id": len(faculty_list) + 1, "name": name, "designation": "Assistant Professor"})

        # 2. Fetch Room Pool
        rooms_list = []
        if db is not None:
            try:
                res = await db.execute(select(Room).order_by(Room.code))
                room_rows = res.scalars().all()
                if room_rows:
                    rooms_list = [{"id": r.code, "capacity": r.capacity or 60, "room_type": r.room_type or "classroom"} for r in room_rows]
            except Exception as ex:
                print(f"[WizardDefaultsService DB Warning] {ex}")

        if not rooms_list:
            raw_rooms = seed.get("rooms", [])
            if raw_rooms:
                rooms_list = [
                    {
                        "id": str(r.get("code") or r.get("id")),
                        "capacity": r.get("capacity", 66),
                        "room_type": r.get("room_type", "classroom")
                    }
                    for r in raw_rooms
                ]
            else:
                from app.services.room_service import RoomService
                rooms_list = RoomService._get_seed_rooms()

        # 3. Fetch Sections
        section_names = []
        if db is not None:
            try:
                res = await db.execute(select(Section).order_by(Section.name))
                sec_rows = res.scalars().all()
                if sec_rows:
                    section_names = [s.name for s in sec_rows]
            except Exception as ex:
                print(f"[WizardDefaultsService DB Warning] {ex}")

        if not section_names:
            from app.services.section_service import SectionService
            seed_secs = SectionService._get_seed_sections()
            section_names = [s["name"] for s in seed_secs]

        # 4. Standard Curricula dynamically generated from seed entries
        seed_entries = seed.get("entries", [])
        curricula_map: Dict[str, List[Dict[str, Any]]] = {"II Year": [], "III Year": [], "IV Year": []}
        seen_codes: Dict[str, Set[str]] = {"II Year": set(), "III Year": set(), "IV Year": set()}

        for e in seed_entries:
            sname = str(e.get("section") or "")
            code = str(e.get("subject") or "").strip()
            if not code or code in ("BREAK", "LUNCH"):
                continue

            year_key = "IV Year" if sname.startswith("IV") else ("III Year" if sname.startswith("III") else "II Year")
            if code not in seen_codes[year_key]:
                seen_codes[year_key].add(code)
                stype = str(e.get("entry_type") or "L").upper()
                fac = e.get("faculty")
                primary_fac = fac[0] if isinstance(fac, list) and fac else (str(fac) if fac else "Department Faculty")
                co_facs = fac[1:] if isinstance(fac, list) and len(fac) > 1 else []
                is_lab = "(P)" in code or stype == "P"

                curricula_map[year_key].append({
                    "subject_code": code,
                    "subject_name": str(e.get("raw_subject_text") or code),
                    "subject_type": "P" if is_lab else stype,
                    "faculty_name": primary_fac,
                    "co_faculty": co_facs,
                    "weekly_hours": 2 if is_lab else (4 if "MINOR" in code else 3),
                    "continuous_slots": 2 if is_lab else 1
                })

        # Ensure baseline fallback if seed entries uninitialized
        if not curricula_map["II Year"]:
            curricula_map = {
                "II Year": [
                    {"subject_code": "SFCDS", "subject_name": "Statistical Foundation for Computing", "subject_type": "L", "faculty_name": "DR. P. Kalpana", "co_faculty": [], "weekly_hours": 3, "continuous_slots": 1},
                    {"subject_code": "SFCDS(P)", "subject_name": "SFCDS Practical Lab", "subject_type": "P", "faculty_name": "DR. P. Kalpana", "co_faculty": ["DR. BANDI GURAVAIAH"], "weekly_hours": 2, "continuous_slots": 2},
                    {"subject_code": "DS", "subject_name": "Data Structures", "subject_type": "L", "faculty_name": "Dr. S. Srikantha Reddy", "co_faculty": [], "weekly_hours": 3, "continuous_slots": 1},
                    {"subject_code": "DS(P)", "subject_name": "Data Structures Lab", "subject_type": "P", "faculty_name": "Dr. S. Srikantha Reddy", "co_faculty": ["P. Girija"], "weekly_hours": 2, "continuous_slots": 2},
                    {"subject_code": "LIBRARY", "subject_name": "Central Library", "subject_type": "LIBRARY", "faculty_name": "Library Staff", "co_faculty": [], "weekly_hours": 1, "continuous_slots": 1},
                ],
                "III Year": [
                    {"subject_code": "DL", "subject_name": "Deep Learning", "subject_type": "L", "faculty_name": "Dr. Eva Patel", "co_faculty": [], "weekly_hours": 3, "continuous_slots": 1},
                    {"subject_code": "DL(P)", "subject_name": "Deep Learning GPU Lab", "subject_type": "P", "faculty_name": "Dr. Eva Patel", "co_faculty": ["V. Amarnath"], "weekly_hours": 2, "continuous_slots": 2},
                    {"subject_code": "MINORS/HONORS", "subject_name": "Minors / Honors Track", "subject_type": "MINORHONOR", "faculty_name": "A. Hruday Raj", "co_faculty": [], "weekly_hours": 4, "continuous_slots": 2},
                ],
                "IV Year": [
                    {"subject_code": "SL/EL", "subject_name": "Self Learning", "subject_type": "SL_EL", "faculty_name": "Self-Guided", "co_faculty": [], "weekly_hours": 12, "continuous_slots": 2},
                    {"subject_code": "GENAI(P)", "subject_name": "Generative AI Lab", "subject_type": "P", "faculty_name": "Kuchipudi. koushika", "co_faculty": [], "weekly_hours": 2, "continuous_slots": 2},
                ]
            }

        return {
            "faculty": faculty_list,
            "rooms": rooms_list,
            "sections": section_names,
            "curricula": curricula_map
        }
