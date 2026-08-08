import os
import sys
import json
from datetime import datetime, timezone, time


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
        # Check if sections, faculty, and rooms tables have full records
        res_sec = await db.execute(select(func.count(Section.id)))
        sec_count = res_sec.scalar() or 0

        res_fac = await db.execute(select(func.count(Faculty.id)))
        fac_count = res_fac.scalar() or 0

        res_rm = await db.execute(select(func.count(Room.id)))
        room_count = res_rm.scalar() or 0

        if sec_count >= 59 and fac_count >= 110 and room_count >= 40:
            print(f"[Auto-Seed] Database fully seeded ({sec_count} sections, {fac_count} faculty, {room_count} rooms). Skipping.")
            return False

        print(f"[Auto-Seed] Incomplete database detected ({sec_count} sections, {fac_count} faculty, {room_count} rooms). Re-seeding full master dataset...")
        
        # Clean out incomplete old seed records if present
        from sqlalchemy import delete
        await db.execute(delete(TimetableEntry))
        await db.execute(delete(Section))
        await db.execute(delete(Faculty))
        await db.execute(delete(Room))
        await db.commit()


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

        # 3. Seed Branches (Full 9 Programs)
        branches_data = [
            ("AIML", "Artificial Intelligence & Machine Learning"),
            ("CS", "Computer Science & Engineering"),
            ("DS", "Data Science"),
            ("CSBS", "Computer Science & Business Systems"),
            ("IOT", "Internet of Things"),
            ("BS(DS)", "Bachelor of Science in Data Science"),
            ("MSC(DS)", "Master of Science in Data Science"),
            ("M.TECH", "Master of Technology"),
            ("MINORHONORS", "Minors & Honors Program"),
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
            elif "MSC" in sname:
                bcode = "MSC(DS)"
            elif "MTECH" in sname or "M.TECH" in sname:
                bcode = "M.TECH"
            elif "BS(DS)" in sname or "BS" in sname:
                bcode = "BS(DS)"
            elif "DS" in sname:
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

            label = (sname.split("-")[-1].strip() if "-" in sname else sname)[:10]
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

        # Parse 4th Year Excel if available (19 sections sec1..sec19)
        yr4_path = os.path.join(os.path.dirname(excel_path), "4th yr TT 17TH JULY.xlsx")
        if os.path.exists(yr4_path):
            try:
                yr4_parsed = parser.parse_file(yr4_path)
                for sname in yr4_parsed.sections.keys():
                    if sname not in section_map:
                        sec = Section(
                            name=sname,
                            label=sname[:10],
                            year_level=4,
                            strength=60,
                            branch_id=branch_map.get("CS", list(branch_map.values())[0]),
                            academic_year_id=ay.id,
                            is_active=True
                        )


                        db.add(sec)
                        await db.commit()
                        await db.refresh(sec)
                        section_map[sname] = sec.id
            except Exception as ex:
                print(f"[Auto-Seed Warning] Could not parse 4th Year Excel: {ex}")

        # 6. Seed Faculty Mappings (All 116 Faculty Members & Workload Limits)
        all_faculty_names = set(parsed_result.faculty_mappings.keys())
        seed_dir = os.path.abspath("data/seed")
        for sname_json in ["original_v5_faculty.json", "original_v4_faculty.json"]:
            spath = os.path.join(seed_dir, sname_json)
            if os.path.exists(spath):
                try:
                    with open(spath, "r", encoding="utf-8") as f:
                        f_data = json.load(f)
                        if isinstance(f_data, dict):
                            all_faculty_names.update(f_data.keys())
                        elif isinstance(f_data, list):
                            for fitem in f_data:
                                fn = fitem.get("name") if isinstance(fitem, dict) else str(fitem)
                                if fn:
                                    all_faculty_names.add(fn)
                except Exception as ex:
                    print(f"[Auto-Seed Warning] Could not load faculty seed {sname_json}: {ex}")


        faculty_map = {}
        for fname in sorted(all_faculty_names):
            upper_name = fname.upper()
            if "DR." in upper_name or "DR " in upper_name or "PROF" in upper_name:
                desig = "Professor"
                max_h = 12
            elif "ASSOC" in upper_name:
                desig = "Associate Professor"
                max_h = 14
            else:
                desig = "Assistant Professor"
                max_h = 16

            fac = Faculty(
                name=fname,
                dept_id=dept.id,
                designation=desig,
                max_hours_per_week=max_h,
                is_external=False
            )
            db.add(fac)
            await db.commit()
            await db.refresh(fac)
            faculty_map[fname] = fac.id


        # 7. Seed All 40 Rooms & Building Blocks
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
            ("619A", "classroom", 60, "6", "Aryabhatta Bhavan / U-Block", False),
            ("215", "classroom", 60, "2", "Divisional Bhavan / H-Block", False),
            ("216", "classroom", 60, "2", "Divisional Bhavan / H-Block", False),
            ("217", "classroom", 60, "2", "Divisional Bhavan / H-Block", False),
            ("218", "classroom", 60, "2", "Divisional Bhavan / H-Block", False),
            ("401", "classroom", 60, "4", "Aryabhatta Bhavan / U-Block", False),
            ("402", "classroom", 60, "4", "Aryabhatta Bhavan / U-Block", False),
            ("418", "classroom", 60, "4", "Aryabhatta Bhavan / U-Block", False),
            ("501", "classroom", 60, "5", "Aryabhatta Bhavan / U-Block", False),
            ("501A", "classroom", 60, "5", "Aryabhatta Bhavan / U-Block", False),
            ("502", "classroom", 60, "5", "Aryabhatta Bhavan / U-Block", False),
            ("514", "classroom", 60, "5", "Aryabhatta Bhavan / U-Block", False),
            ("514-A", "classroom", 60, "5", "Aryabhatta Bhavan / U-Block", False),
            ("514-B", "classroom", 60, "5", "Aryabhatta Bhavan / U-Block", False),
            ("514A", "classroom", 60, "5", "Aryabhatta Bhavan / U-Block", False),
            ("514B", "classroom", 60, "5", "Aryabhatta Bhavan / U-Block", False),
            ("518", "classroom", 60, "5", "Aryabhatta Bhavan / U-Block", False),
            ("AFTF-12", "gpu_lab", 72, "AFTF", "Aryabhatta Bhavan / U-Block", True),
            ("AFTF-13", "gpu_lab", 72, "AFTF", "Aryabhatta Bhavan / U-Block", True),
            ("AFTF-14", "gpu_lab", 72, "AFTF", "Aryabhatta Bhavan / U-Block", True),
            ("AFF-09", "project_room", 35, "AFF", "Aryabhatta Bhavan / U-Block", False),
            ("AFF-10", "project_room", 35, "AFF", "Aryabhatta Bhavan / U-Block", False),
            ("AFF-9", "project_room", 35, "AFF", "Aryabhatta Bhavan / U-Block", False),
            ("/AL/IL", "activity_room", 50, "1", "A-Block", False),
            ("A-Block First Floor", "activity_room", 60, "1", "A-Block", False),
            ("VIRTUAL_LIBRARY", "virtual_room", 100, "1", "Central Library", False),
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
        slot_map = {}
        res_ts = await db.execute(select(TimeSlot))
        existing_slots = res_ts.scalars().all()

        if existing_slots:
            for ts in existing_slots:
                if ts.period is not None:
                    slot_map[(ts.day, ts.period)] = ts.id
        else:
            days = ["MON", "TUE", "WED", "THU", "FRI", "SAT"]
            times = [
                (1, time(8, 15), time(9, 5), False),
                (2, time(9, 5), time(9, 55), False),
                (None, time(9, 55), time(10, 10), True), # Tea Break
                (3, time(10, 10), time(11, 0), False),
                (4, time(11, 0), time(11, 50), False),
                (5, time(11, 50), time(12, 40), False),
                (None, time(12, 40), time(13, 40), True), # Lunch Break
                (6, time(13, 40), time(14, 30), False),
                (7, time(14, 30), time(15, 20), False),
                (8, time(15, 20), time(16, 5), False),
            ]
            for d in days:
                for p, st, et, is_b in times:
                    ts = TimeSlot(
                        day=d,
                        period=p,
                        start_time=st,
                        end_time=et,
                        is_blocked=is_b,
                        slot_label="TEA BREAK" if p is None and st == time(9, 55) else ("LUNCH BREAK" if is_b else f"Period {p}")
                    )
                    db.add(ts)
                    await db.commit()
                    await db.refresh(ts)
                    if p is not None:
                        slot_map[(d, p)] = ts.id


        # 9. Create Timetable Versions (V5 and V3)
        from parser.excel_parser import resolve_version_path

        from datetime import date

        # Seed V5 (Version ID 5)
        tv5 = TimetableVersion(
            academic_year_id=ay.id,
            version_label="V5",
            valid_from=date(2026, 7, 15),
            is_current=True,
            source="IMPORTED",
            notes="Current baseline imported from V5 Excel dataset"
        )
        db.add(tv5)
        await db.commit()
        await db.refresh(tv5)

        # Seed V3 (Version ID 3)
        tv3 = TimetableVersion(
            academic_year_id=ay.id,
            version_label="V3",
            valid_from=date(2026, 7, 13),
            is_current=False,
            source="IMPORTED",
            notes="Previous revision imported from V3 Excel dataset"
        )
        db.add(tv3)
        await db.commit()
        await db.refresh(tv3)


        # 10. Seed Timetable Entries for V5
        entries_count = 0
        for slot in parsed_result.raw_entries:
            sec_id = section_map.get(slot.section)
            ts_id = slot_map.get((slot.day, slot.period))
            rm_id = room_map.get(slot.room) if slot.room else None

            if sec_id and ts_id:
                entry = TimetableEntry(
                    timetable_version_id=tv5.id,
                    section_id=sec_id,
                    time_slot_id=ts_id,
                    room_id=rm_id,
                    entry_type=slot.subject_type,
                    raw_subject_text=slot.subject_code,
                    raw_room_text=slot.room or "",
                    faculty_ids=[faculty_map[f] for f in slot.faculty_list if f in faculty_map],
                    span_periods=1
                )
                db.add(entry)
                entries_count += 1

        # 11. Seed Timetable Entries for V3
        v3_path = resolve_version_path("V3")
        if os.path.exists(v3_path):
            parsed_v3 = parser.parse_file(v3_path)
            for slot in parsed_v3.raw_entries:
                sec_id = section_map.get(slot.section)
                ts_id = slot_map.get((slot.day, slot.period))
                rm_id = room_map.get(slot.room) if slot.room else None

                if sec_id and ts_id:
                    entry = TimetableEntry(
                        timetable_version_id=tv3.id,
                        section_id=sec_id,
                        time_slot_id=ts_id,
                        room_id=rm_id,
                        entry_type=slot.subject_type,
                        raw_subject_text=slot.subject_code,
                        raw_room_text=slot.room or "",
                        faculty_ids=[faculty_map[f] for f in slot.faculty_list if f in faculty_map],
                        span_periods=1
                    )
                    db.add(entry)
                    entries_count += 1


        await db.commit()
        print(f"[Auto-Seed Complete] Loaded {entries_count} timetable entries across V5 and V3 versions into PostgreSQL.")
        return True
