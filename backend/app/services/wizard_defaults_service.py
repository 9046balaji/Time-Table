from typing import Dict, Any, List, Optional
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

            default_39 = [
                {"id": "601", "capacity": 66, "room_type": "classroom"},
                {"id": "602", "capacity": 66, "room_type": "classroom"},
                {"id": "603", "capacity": 66, "room_type": "classroom"},
                {"id": "607", "capacity": 66, "room_type": "classroom"},
                {"id": "608", "capacity": 66, "room_type": "classroom"},
                {"id": "609", "capacity": 66, "room_type": "classroom"},
                {"id": "610", "capacity": 66, "room_type": "classroom"},
                {"id": "613", "capacity": 66, "room_type": "classroom"},
                {"id": "614", "capacity": 66, "room_type": "classroom"},
                {"id": "618", "capacity": 66, "room_type": "classroom"},
                {"id": "619", "capacity": 66, "room_type": "classroom"},
                {"id": "215", "capacity": 66, "room_type": "classroom"},
                {"id": "216", "capacity": 66, "room_type": "classroom"},
                {"id": "217", "capacity": 66, "room_type": "classroom"},
                {"id": "218", "capacity": 66, "room_type": "classroom"},
                {"id": "514-A", "capacity": 66, "room_type": "classroom"},
                {"id": "514-B", "capacity": 66, "room_type": "classroom"},
                {"id": "518", "capacity": 66, "room_type": "classroom"},
                {"id": "401", "capacity": 66, "room_type": "classroom"},
                {"id": "402", "capacity": 66, "room_type": "classroom"},
                {"id": "418", "capacity": 66, "room_type": "classroom"},
                {"id": "501", "capacity": 66, "room_type": "classroom"},
                {"id": "201", "capacity": 66, "room_type": "classroom"},
                {"id": "202", "capacity": 66, "room_type": "classroom"},
                {"id": "301", "capacity": 66, "room_type": "classroom"},
                {"id": "302", "capacity": 66, "room_type": "classroom"},
                {"id": "303", "capacity": 66, "room_type": "classroom"},
                {"id": "304", "capacity": 66, "room_type": "classroom"},
                {"id": "604", "capacity": 60, "room_type": "computer_lab"},
                {"id": "605", "capacity": 60, "room_type": "computer_lab"},
                {"id": "606", "capacity": 60, "room_type": "computer_lab"},
                {"id": "611", "capacity": 60, "room_type": "computer_lab"},
                {"id": "612", "capacity": 60, "room_type": "computer_lab"},
                {"id": "615", "capacity": 60, "room_type": "computer_lab"},
                {"id": "616", "capacity": 60, "room_type": "computer_lab"},
                {"id": "617", "capacity": 60, "room_type": "computer_lab"},
                {"id": "AFTF-12", "capacity": 72, "room_type": "gpu_lab"},
                {"id": "AFTF-13", "capacity": 72, "room_type": "gpu_lab"},
                {"id": "AFTF-14", "capacity": 72, "room_type": "gpu_lab"}
            ]
            seen = {r["id"] for r in rooms_list}
            for r in default_39:
                if r["id"] not in seen:
                    rooms_list.append(r)



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
            sec_set = set(e.get("section") for e in seed.get("entries", []) if e.get("section"))
            section_names = sorted(list(sec_set)) if sec_set else [
                "II AIML-A", "II AIML-B", "II AIML-C", "II AIML-D", "II AIML-E", "II AIML-F", "II AIML-G", "II AIML-H", "II AIML-I", "II AIML-J", "II AIML-K", "II AIML-L",
                "III AIML-A", "III AIML-B", "III AIML-C", "III AIML-D", "III AIML-E", "III AIML-F", "III AIML-G",
                "IV AIML-A", "IV AIML-B", "IV AIML-C", "IV AIML-D", "IV AIML-E",
                "II CS-A", "II CS-B", "III CS", "IV CS", "II DS-A", "II DS-B", "III DS-A", "III DS-B", "IV DS", "II CSBS", "III CSBS", "IV CSBS", "II IOT", "III IOT"
            ]

        # 4. Standard Curricula
        curricula = {
            "II Year": [
                {"subject_code": "SFCDS", "subject_name": "Statistical Foundation for Computing & Data Science", "subject_type": "L", "faculty_name": "DR. P. Kalpana", "co_faculty": [], "weekly_hours": 3, "continuous_slots": 1},
                {"subject_code": "SFCDS(P)", "subject_name": "SFCDS Practical Lab", "subject_type": "P", "faculty_name": "DR. P. Kalpana", "co_faculty": ["DR. BANDI GURAVAIAH"], "weekly_hours": 2, "continuous_slots": 2},
                {"subject_code": "DMS", "subject_name": "Discrete Mathematical Structures", "subject_type": "L", "faculty_name": "DR. ANKAMMA RAO MALLELA", "co_faculty": [], "weekly_hours": 3, "continuous_slots": 1},
                {"subject_code": "DS", "subject_name": "Data Structures", "subject_type": "L", "faculty_name": "Dr. S. Srikantha Reddy", "co_faculty": [], "weekly_hours": 3, "continuous_slots": 1},
                {"subject_code": "DS(P)", "subject_name": "Data Structures Lab", "subject_type": "P", "faculty_name": "Dr. S. Srikantha Reddy", "co_faculty": ["P. Girija", "K. Nikhitha", "Mr. Mahendra Varma"], "weekly_hours": 2, "continuous_slots": 2},
                {"subject_code": "AI", "subject_name": "Artificial Intelligence Search Methods", "subject_type": "L", "faculty_name": "Dr. B. Sudha Rani", "co_faculty": [], "weekly_hours": 3, "continuous_slots": 1},
                {"subject_code": "AI(P)", "subject_name": "AI Search Methods Lab", "subject_type": "P", "faculty_name": "Dr. B. Sudha Rani", "co_faculty": ["V. Amarnath"], "weekly_hours": 2, "continuous_slots": 2},
                {"subject_code": "DBMS", "subject_name": "Database Management Systems", "subject_type": "L", "faculty_name": "Ms. P Seetha Lakshmi", "co_faculty": [], "weekly_hours": 3, "continuous_slots": 1},
                {"subject_code": "DBMS(P)", "subject_name": "DBMS Practical Lab", "subject_type": "P", "faculty_name": "Ms. P Seetha Lakshmi", "co_faculty": ["Mr. A.Siva Naga Rama Gopal"], "weekly_hours": 2, "continuous_slots": 2},
                {"subject_code": "OOPS", "subject_name": "Object Oriented Programming", "subject_type": "L", "faculty_name": "Ms. G. Mahalakshmi", "co_faculty": [], "weekly_hours": 3, "continuous_slots": 1},
                {"subject_code": "OOPS(P)", "subject_name": "OOPS Lab", "subject_type": "P", "faculty_name": "Ms. G. Mahalakshmi", "co_faculty": ["Mr. D. Pavan Kalyan"], "weekly_hours": 2, "continuous_slots": 2},
                {"subject_code": "IIC", "subject_name": "Agentic Tools (Industry-Integrated Course)", "subject_type": "IIC", "faculty_name": "Industry Specialist", "co_faculty": [], "weekly_hours": 1, "continuous_slots": 1},
            ],
            "III Year": [
                {"subject_code": "DL", "subject_name": "Deep Learning & Neural Networks", "subject_type": "L", "faculty_name": "Dr. Eva Patel", "co_faculty": [], "weekly_hours": 3, "continuous_slots": 1},
                {"subject_code": "DL(P)", "subject_name": "Deep Learning Practical GPU Lab", "subject_type": "P", "faculty_name": "Dr. Eva Patel", "co_faculty": ["V. Amarnath", "KANCHARLA KARUNA KUMARI"], "weekly_hours": 2, "continuous_slots": 2},
                {"subject_code": "WT", "subject_name": "Web Technologies", "subject_type": "L", "faculty_name": "Ms. S. Krishna Veni", "co_faculty": [], "weekly_hours": 3, "continuous_slots": 1},
                {"subject_code": "WT(P)", "subject_name": "Web Technologies Lab", "subject_type": "P", "faculty_name": "Ms. S. Krishna Veni", "co_faculty": ["Ms. M. YAMINI"], "weekly_hours": 2, "continuous_slots": 2},
                {"subject_code": "CV(P)", "subject_name": "Computer Vision Lab", "subject_type": "P", "faculty_name": "MAJETI LALITHA MAHA LAKSHMI", "co_faculty": ["Ms. K.Vyshnavi"], "weekly_hours": 2, "continuous_slots": 2},
                {"subject_code": "MINORHONOR", "subject_name": "Synchronized Minors / Honors", "subject_type": "P", "faculty_name": "A. Hruday Raj", "co_faculty": ["Ms. Attuluri Ramya"], "weekly_hours": 2, "continuous_slots": 2},
            ],
            "IV Year": [
                {"subject_code": "SL/EL", "subject_name": "Self Learning / Extra Learning", "subject_type": "SL_EL", "faculty_name": "Self-Guided", "co_faculty": [], "weekly_hours": 12, "continuous_slots": 2},
                {"subject_code": "CNS", "subject_name": "Cryptography & Network Security", "subject_type": "L", "faculty_name": "Dr. M. Vasudeva", "co_faculty": [], "weekly_hours": 3, "continuous_slots": 1},
                {"subject_code": "CNS(P)", "subject_name": "Cryptography Lab", "subject_type": "P", "faculty_name": "Dr. M. Vasudeva", "co_faculty": ["P. Girija"], "weekly_hours": 2, "continuous_slots": 2},
                {"subject_code": "GENAI(P)", "subject_name": "Generative AI Practical Lab", "subject_type": "P", "faculty_name": "V. Amarnath", "co_faculty": ["Mr. Mahendra Varma"], "weekly_hours": 2, "continuous_slots": 2},
                {"subject_code": "IOT", "subject_name": "Internet of Things", "subject_type": "L", "faculty_name": "Dr. A.V. Nageswara Rao", "co_faculty": [], "weekly_hours": 3, "continuous_slots": 1},
                {"subject_code": "MINORS/HONORS", "subject_name": "Synchronized Minors / Honors Track", "subject_type": "MINORHONOR", "faculty_name": "Department Faculty", "co_faculty": [], "weekly_hours": 2, "continuous_slots": 2},
            ],
        }

        return {
            "faculty": faculty_list,
            "rooms": rooms_list,
            "sections": section_names,
            "curricula": curricula
        }
