import os
import sys
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.department import Department
from app.models.academic_year import AcademicYear
from app.models.branch import Branch
from app.models.section import Section
from app.models.faculty import Faculty
from app.models.room import Room
from app.models.subject import Subject
from app.models.time_slot import TimeSlot
from app.models.timetable import TimetableVersion, TimetableEntry

from parser.excel_parser import ExcelTimetableParser

V5_FILE_PATH = "time_table/ACSE TIMETABLE (V5)  - W.e.f 15-7-2026.xlsx"


class SeedService:
    @staticmethod
    async def auto_seed_if_empty(db: AsyncSession) -> bool:
        """Checks if tables are populated; if empty, parses V5 Excel and seeds DB."""
        # Check if sections table has records
        res = await db.execute(select(Section).order_by(Section.id))
        existing_sections = res.scalars().all()

        if existing_sections:
            # Check if existing sections contain generic names like "Section 1"
            has_generic = any("Section " in s.name for s in existing_sections)
            if has_generic:
                print("[Auto-Seed] Updating existing generic section records with real VFSTR academic names...")
                from parser.excel_parser import resolve_v5_path
                excel_path = resolve_v5_path()
                if os.path.exists(excel_path):
                    parsed_res = ExcelTimetableParser().parse_file(excel_path)
                    real_names = list(parsed_res.sections.keys())
                    for idx, sec_obj in enumerate(existing_sections):
                        if idx < len(real_names):
                            sec_obj.name = real_names[idx]
                            sec_obj.label = real_names[idx].split("-")[-1].strip() if "-" in real_names[idx] else "Main"
                    await db.commit()
                    print(f"[Auto-Seed] Updated {min(len(existing_sections), len(real_names))} section names to real academic codes.")
            else:
                print("[Auto-Seed] Database already seeded with real section names. Skipping.")
            return False

        print("[Auto-Seed] Empty database detected. Parsing V5 Excel and seeding PostgreSQL...")

        # 1. Seed Department
        dept_stmt = select(Department).where(Department.code == "ACSE")
        res = await db.execute(dept_stmt)
        dept = res.scalar_one_or_none()
        if not dept:
            dept = Department(
                code="ACSE",
                name="Department of Advanced Computer Science & Engineering",
                program_type="UG"
            )
            db.add(dept)
            await db.commit()
            await db.refresh(dept)

        # 2. Seed Academic Year
        ay_stmt = select(AcademicYear).where(AcademicYear.label == "2026-27 Sem I")
        res = await db.execute(ay_stmt)
        ay = res.scalar_one_or_none()
        if not ay:
            ay = AcademicYear(
                year=2026,
                semester=1,
                label="2026-27 Sem I",
                is_current=True
            )
            db.add(ay)
            await db.commit()
            await db.refresh(ay)

        # 3. Seed Branches
        branches_data = [
            ("AIML", "Artificial Intelligence & Machine Learning"),
            ("CS", "Computer Science & Engineering"),
            ("DS", "Data Science"),
            ("CSBS", "Computer Science & Business Systems"),
            ("IOT", "Internet of Things"),
        ]
        branch_map = {}
        for code, bname in branches_data:
            stmt = select(Branch).where(Branch.code == code)
            res = await db.execute(stmt)
            br = res.scalar_one_or_none()
            if not br:
                br = Branch(code=code, name=bname, dept_id=dept.id)
                db.add(br)
                await db.commit()
                await db.refresh(br)
            branch_map[code] = br.id

        # 4. Parse V5 Excel file using resolve_v5_path
        from parser.excel_parser import resolve_v5_path
        excel_path = resolve_v5_path()
        if not os.path.exists(excel_path):
            print(f"[Auto-Seed Warning] Baseline Excel file not found at {excel_path}. Creating fallback seed.")
            return False

        parser = ExcelTimetableParser()
        parsed_result = parser.parse_file(excel_path)

        # 5. Seed Sections
        section_map = {}
        for sname in parsed_result.sections.keys():
            # Derive Branch code from sname string
            if "CSBS" in sname:
                bcode = "CSBS"
            elif "IOT" in sname:
                bcode = "IOT"
            elif "BS(DS)" in sname or "MSC" in sname or "MTECH" in sname or "DS" in sname:
                bcode = "DS"
            elif "CS" in sname:
                bcode = "CS"
            else:
                bcode = "AIML"

            # Derive Year level from sname string
            if sname.startswith("IV ") or sname.startswith("IV-") or sname.startswith("IV_"):
                ylevel = 4
            elif sname.startswith("III ") or sname.startswith("III-") or sname.startswith("III_"):
                ylevel = 3
            elif sname.startswith("II ") or sname.startswith("II-") or sname.startswith("II_"):
                ylevel = 2
            elif sname.startswith("I ") or sname.startswith("I-") or sname.startswith("I_"):
                ylevel = 1
            else:
                ylevel = 2

            label = sname
            brid = branch_map.get(bcode, list(branch_map.values())[0])

            sec = Section(
                name=sname,
                label=label,
                year_level=ylevel,
                strength=60,
                branch_id=brid,
                academic_year_id=ay.id,
                is_active=True
            )
            db.add(sec)
            await db.commit()
            await db.refresh(sec)
            section_map[sname] = sec.id

        # 6. Seed Faculty Mappings
        faculty_map = {}
        for fname in parsed_result.faculty_mappings.keys():
            fac = Faculty(
                name=fname,
                dept_id=dept.id,
                designation="Assistant Professor",
                max_hours_per_week=16,
                max_daily_classes=5,
                is_external=False
            )
            db.add(fac)
            await db.commit()
            await db.refresh(fac)
            faculty_map[fname] = fac.id

        # 7. Seed Rooms
        room_map = {}
        all_rooms = [
            ("601", "classroom", 66, "6", "Aryabhatta Bhavan / U-Block", False),
            ("602", "classroom", 66, "6", "Aryabhatta Bhavan / U-Block", False),
            ("603", "classroom", 66, "6", "Aryabhatta Bhavan / U-Block", False),
            ("604", "computer_lab", 60, "6", "Aryabhatta Bhavan / U-Block", False),
            ("605", "computer_lab", 60, "6", "Aryabhatta Bhavan / U-Block", False),
            ("606", "computer_lab", 60, "6", "Aryabhatta Bhavan / U-Block", False),
            ("607", "classroom", 66, "6", "Aryabhatta Bhavan / U-Block", False),
            ("608", "classroom", 66, "6", "Aryabhatta Bhavan / U-Block", False),
            ("609", "classroom", 66, "6", "Aryabhatta Bhavan / U-Block", False),
            ("610", "classroom", 66, "6", "Aryabhatta Bhavan / U-Block", False),
            ("611", "computer_lab", 60, "6", "Aryabhatta Bhavan / U-Block", False),
            ("612", "computer_lab", 60, "6", "Aryabhatta Bhavan / U-Block", False),
            ("613", "classroom", 66, "6", "Aryabhatta Bhavan / U-Block", False),
            ("614", "classroom", 66, "6", "Aryabhatta Bhavan / U-Block", False),
            ("615", "computer_lab", 60, "6", "Aryabhatta Bhavan / U-Block", False),
            ("616", "computer_lab", 60, "6", "Aryabhatta Bhavan / U-Block", False),
            ("617", "computer_lab", 60, "6", "Aryabhatta Bhavan / U-Block", False),
            ("618", "classroom", 66, "6", "Aryabhatta Bhavan / U-Block", False),
            ("619", "classroom", 66, "6", "Aryabhatta Bhavan / U-Block", False),
            ("215", "classroom", 60, "2", "Divisional Bhavan / H-Block", False),
            ("216", "classroom", 60, "2", "Divisional Bhavan / H-Block", False),
            ("217", "classroom", 60, "2", "Divisional Bhavan / H-Block", False),
            ("218", "classroom", 60, "2", "Divisional Bhavan / H-Block", False),
            ("401", "classroom", 60, "4", "Aryabhatta Bhavan / U-Block", False),
            ("402", "classroom", 60, "4", "Aryabhatta Bhavan / U-Block", False),
            ("418", "classroom", 60, "4", "Aryabhatta Bhavan / U-Block", False),
            ("501", "classroom", 60, "5", "Aryabhatta Bhavan / U-Block", False),
            ("514-A", "classroom", 60, "5", "Aryabhatta Bhavan / U-Block", False),
            ("514-B", "classroom", 60, "5", "Aryabhatta Bhavan / U-Block", False),
            ("518", "classroom", 60, "5", "Aryabhatta Bhavan / U-Block", False),
            ("AFTF-12", "gpu_lab", 72, "AFTF", "Aryabhatta Bhavan / U-Block", True),
            ("AFTF-13", "gpu_lab", 72, "AFTF", "Aryabhatta Bhavan / U-Block", True),
            ("AFTF-14", "gpu_lab", 72, "AFTF", "Aryabhatta Bhavan / U-Block", True),
            ("AFF-09", "project_room", 35, "AFF", "Aryabhatta Bhavan / U-Block", False),
            ("AFF-10", "project_room", 35, "AFF", "Aryabhatta Bhavan / U-Block", False),
        ]
        for rcode, rtype, rcap, rfloor, rblock, rgpu in all_rooms:
            room = Room(
                dept_id=dept.id,
                code=rcode,
                room_type=rtype,
                capacity=rcap,
                floor=rfloor,
                block=rblock,
                gpu_capable=rgpu,
                is_available=True
            )
            db.add(room)
            await db.commit()
            await db.refresh(room)
            room_map[rcode] = room.id

        # 8. Seed Default Time Slots (MON-SAT, Periods 1-8 + Breaks)
        days = ["MON", "TUE", "WED", "THU", "FRI", "SAT"]
        times = [
            (1, "08:15", "09:05", False),
            (2, "09:05", "09:55", False),
            (None, "09:55", "10:10", True), # Tea Break
            (3, "10:10", "11:00", False),
            (4, "11:00", "11:50", False),
            (5, "11:50", "12:40", False),
            (None, "12:40", "13:40", True), # Lunch Break
            (6, "13:40", "14:30", False),
            (7, "14:30", "15:20", False),
            (8, "15:20", "16:05", False),
        ]
        slot_map = {}
        for d in days:
            for p, st, et, is_b in times:
                ts = TimeSlot(
                    day=d,
                    period=p,
                    start_time=st,
                    end_time=et,
                    is_break=is_b,
                    slot_label="TEA BREAK" if p is None and st == "09:55" else "LUNCH BREAK" if is_b else f"Period {p}"
                )
                db.add(ts)
                await db.commit()
                await db.refresh(ts)
                if p is not None:
                    slot_map[(d, p)] = ts.id

        # 9. Create Timetable Versions (V5 and V3)
        from parser.excel_parser import resolve_version_path

        # Seed V5 (Version ID 5)
        tv5 = TimetableVersion(
            id=5,
            version_label="V5",
            effective_date="15-07-2026",
            is_active=True,
            hard_violations_count=51,
            soft_violations_count=12,
            notes="Current baseline imported from V5 Excel dataset"
        )
        db.add(tv5)
        await db.commit()
        await db.refresh(tv5)

        # Seed V3 (Version ID 3)
        tv3 = TimetableVersion(
            id=3,
            version_label="V3",
            effective_date="13-07-2026",
            is_active=False,
            hard_violations_count=64,
            soft_violations_count=18,
            notes="Previous revision imported from V3 Excel dataset"
        )
        db.add(tv3)
        await db.commit()
        await db.refresh(tv3)

        # 10. Seed Timetable Entries for V5
        entries_count = 0
        for slot in parsed_result.slots:
            sec_id = section_map.get(slot.section_name)
            ts_id = slot_map.get((slot.day, slot.period))
            rm_id = room_map.get(slot.room_code) if slot.room_code else None

            if sec_id and ts_id:
                entry = TimetableEntry(
                    timetable_version_id=tv5.id,
                    section_id=sec_id,
                    time_slot_id=ts_id,
                    room_id=rm_id,
                    entry_type=slot.slot_type,
                    raw_subject_text=slot.subject_code,
                    raw_room_text=slot.room_code or "",
                    raw_faculty_text=", ".join(slot.faculty_names) if slot.faculty_names else "",
                    faculty_ids=[faculty_map[f] for f in slot.faculty_names if f in faculty_map],
                    source="EXCEL_PARSER_V5",
                    span_periods=slot.span_periods
                )
                db.add(entry)
                entries_count += 1

        # 11. Seed Timetable Entries for V3
        v3_path = resolve_version_path("V3")
        if os.path.exists(v3_path):
            parsed_v3 = parser.parse_file(v3_path)
            for slot in parsed_v3.slots:
                sec_id = section_map.get(slot.section_name)
                ts_id = slot_map.get((slot.day, slot.period))
                rm_id = room_map.get(slot.room_code) if slot.room_code else None

                if sec_id and ts_id:
                    entry = TimetableEntry(
                        timetable_version_id=tv3.id,
                        section_id=sec_id,
                        time_slot_id=ts_id,
                        room_id=rm_id,
                        entry_type=slot.slot_type,
                        raw_subject_text=slot.subject_code,
                        raw_room_text=slot.room_code or "",
                        raw_faculty_text=", ".join(slot.faculty_names) if slot.faculty_names else "",
                        faculty_ids=[faculty_map[f] for f in slot.faculty_names if f in faculty_map],
                        source="EXCEL_PARSER_V3",
                        span_periods=slot.span_periods
                    )
                    db.add(entry)
                    entries_count += 1

        await db.commit()
        print(f"[Auto-Seed Complete] Loaded {entries_count} timetable entries across V5 and V3 versions into PostgreSQL.")
        return True
