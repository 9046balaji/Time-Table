import os
import json
from parser.excel_parser import ExcelTimetableParser, resolve_v5_path
from solver.conflict_checker import ConflictChecker

IGNORED_ROOM_CODES = {
    "", "NONE", "LIBRARY", "BREAK", "LUNCH", "SL/EL", "/AL/IL", "AL/IL", "MINORS/HONORS",
    "MINOR/HONOR", "MINORS", "HONORS", "N/A", "NA", "-", "ONLINE", "CRT", "OE"
}


def build_and_save_seed():
    v5_path = resolve_v5_path()
    print(f"Parsing V5 Excel file from: {v5_path}")
    parsed = ExcelTimetableParser().parse_file(v5_path)

    # 1. Sections
    sections_list = []
    sec_names = sorted(list(parsed.sections.keys()))
    for idx, sname in enumerate(sec_names):
        y_lvl = 2 if "II " in sname else (3 if "III " in sname else (4 if "IV " in sname else 1))
        lbl = sname.split("-")[-1].strip() if "-" in sname else sname[-1]
        sections_list.append({
            "id": idx + 1,
            "name": sname,
            "label": lbl,
            "year_level": y_lvl,
            "strength": 66 if "501" not in sname else 30,
            "branch_id": 1,
            "academic_year_id": 1,
            "is_active": True
        })

    # 2. Rooms
    all_rooms = set()
    for s in parsed.raw_entries:
        r = (s.room or "").strip().upper()
        if r and r not in IGNORED_ROOM_CODES:
            all_rooms.add(r)

    rooms_list = []
    for idx, rcode in enumerate(sorted(list(all_rooms))):
        rtype = "gpu_lab" if "AFTF" in rcode else ("computer_lab" if rcode in ["604", "605", "606", "611", "612", "615", "616", "617"] else "classroom")
        cap = 72 if "AFTF" in rcode else (60 if rtype == "computer_lab" else 66)
        rooms_list.append({
            "id": idx + 1,
            "code": rcode,
            "room_type": rtype,
            "capacity": cap,
            "floor": "AFTF" if "AFTF" in rcode else ("AFF" if "AFF" in rcode else rcode[0] if rcode[0].isdigit() else "1"),
            "block": "Aryabhatta Bhavan / U-Block",
            "gpu_capable": "AFTF" in rcode,
            "is_available": True
        })

    # 3. Faculty
    fac_set = set()
    for sec_map in parsed.faculty_mappings.values():
        for fac_list in sec_map.values():
            for f in fac_list:
                if f.strip():
                    fac_set.add(f.strip())

    faculty_list = [
        {
            "id": idx + 1,
            "name": fname,
            "employee_id": f"FAC-{100 + idx + 1}",
            "designation": "Associate Professor" if "DR" in fname.upper() else "Assistant Professor",
            "max_hours_per_week": 14 if "DR" in fname.upper() else 16,
            "max_daily_classes": 5,
            "is_external": False,
            "dept_id": 1,
            "availability": {}
        }
        for idx, fname in enumerate(sorted(list(fac_set)))
    ]

    # 4. Subjects
    subj_map = {}
    for s in parsed.raw_entries:
        code = s.subject_code.split("(")[0].strip()
        if code and code not in subj_map:
            is_l = "(P)" in s.subject_code or "LAB" in s.subject_code.upper()
            subj_map[code] = {
                "id": len(subj_map) + 1,
                "code": code,
                "full_name": s.subject_code,
                "lecture_hours": 0 if is_l else 3,
                "tutorial_hours": 1 if "(T)" in s.subject_code else 0,
                "lab_hours": 2 if is_l else 0,
                "is_lab": is_l,
                "gpu_required": "AFTF" in s.subject_code,
                "slot_type": "P" if is_l else ("T" if "(T)" in s.subject_code else "L"),
                "requires_consecutive": 2 if is_l else 1
            }

    # 5. Raw Entries (All 1,508 slots with Faculty attached)
    entries_list = []
    for idx, s in enumerate(parsed.raw_entries):
        sec_facs = parsed.faculty_mappings.get(s.section, {})
        code_clean = s.subject_code.split("(")[0].strip()
        fac_list = s.faculty_list or sec_facs.get(s.subject_code) or sec_facs.get(code_clean) or []

        is_lab = "(P)" in s.subject_code or "LAB" in s.subject_code.upper()
        is_tut = "(T)" in s.subject_code

        entries_list.append({
            "id": idx + 1,
            "section": s.section,
            "day": s.day,
            "period": s.period,
            "subject": s.subject_code,
            "room": s.room or "",
            "faculty": fac_list,
            "entry_type": "P" if is_lab else ("T" if is_tut else "L"),
            "span_periods": 2 if is_lab else 1
        })

    seed_data = {
        "sections": sections_list,
        "rooms": rooms_list,
        "faculty": faculty_list,
        "subjects": list(subj_map.values()),
        "entries": entries_list
    }

    out_paths = [
        "data/seed/demo_timetable_seed.json",
        "../data/seed/demo_timetable_seed.json"
    ]
    for p in out_paths:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(seed_data, f, indent=2)
        print(f"Saved {len(entries_list)} entries to {p}")


if __name__ == "__main__":
    build_and_save_seed()
