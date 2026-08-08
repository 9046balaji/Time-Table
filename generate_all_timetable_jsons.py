import os
import sys
import json
import openpyxl
from collections import defaultdict

sys.path.insert(0, '.')
sys.path.insert(0, 'backend')

from backend.parser.excel_parser import ExcelTimetableParser

V5_PATH = r"time_table/ACSE TIMETABLE (V5)  - W.e.f 15-7-2026.xlsx"
V4_PATH = r"time_table/ACSE TIMETABLE (V4)  - W.e.f 14-7-2026.xlsx"
YR4_PATH = r"time_table/4th yr TT 17TH JULY.xlsx"

SEED_DIR = r"data/seed"
os.makedirs(SEED_DIR, exist_ok=True)

def process_excel_dataset(file_path, prefix):
    print(f"\n==================================================")
    print(f" processing dataset: {prefix} ({file_path})")
    print(f"==================================================")
    
    if not os.path.exists(file_path):
        print(f"ERROR: File not found: {file_path}")
        return None

    parser = ExcelTimetableParser()
    parsed_data = parser.parse_file(file_path)
    raw_entries = parsed_data.raw_entries

    # 1. All Entries
    entries_list = []
    for e in raw_entries:
        entries_list.append({
            "section": e.section,
            "day": e.day,
            "period": e.period,
            "subject_code": e.subject_code,
            "room": e.room,
            "subject_type": e.subject_type,
            "faculty_list": e.faculty_list,
            "sheet_name": e.sheet_name
        })

    entries_out = os.path.join(SEED_DIR, f"{prefix}_all_entries.json")
    with open(entries_out, "w", encoding="utf-8") as f:
        json.dump(entries_list, f, indent=2)
    print(f"  • Saved {prefix}_all_entries.json ({len(entries_list)} entries)")

    # 2. Legend / Faculty mapping lookup
    legend_mappings = parsed_data.faculty_mappings
    sec_sub_to_fac = defaultdict(list)
    for sec_name, sub_fac_map in legend_mappings.items():
        for sub_name, f_list in sub_fac_map.items():
            clean_facs = [f.strip() for f in f_list if f and f.strip() and not f.strip()[0].isdigit() and f.strip() not in ["***", "undefined"]]
            sec_sub_to_fac[(sec_name, sub_name)] = clean_facs

    # 3. Faculty Workload & Assignments
    faculty_dict = defaultdict(lambda: {
        "weekly_hours": 0,
        "daily_hours": defaultdict(int),
        "subjects_taught": set(),
        "sections_taught": set(),
        "lab_hours": 0,
        "lecture_hours": 0
    })

    for e in raw_entries:
        sec = e.section
        subj = e.subject_code
        day = e.day
        assigned_facs = sec_sub_to_fac.get((sec, subj), [])
        if not assigned_facs and subj:
            clean_sub = subj.replace("(P)", "").replace("(T&P)", "").replace("(T)", "").strip()
            for (s, sub_k), f_list in sec_sub_to_fac.items():
                if s == sec and clean_sub in sub_k:
                    assigned_facs = f_list
                    break

        for f_name in assigned_facs:
            faculty_dict[f_name]["weekly_hours"] += 1
            faculty_dict[f_name]["daily_hours"][day] += 1
            faculty_dict[f_name]["subjects_taught"].add(subj)
            faculty_dict[f_name]["sections_taught"].add(sec)
            if "(P)" in subj or "(T&P)" in subj:
                faculty_dict[f_name]["lab_hours"] += 1
            else:
                faculty_dict[f_name]["lecture_hours"] += 1

    formatted_faculty = {}
    for fac_name, data in sorted(faculty_dict.items()):
        daily_dict = dict(data["daily_hours"])
        formatted_faculty[fac_name] = {
            "weekly_hours": data["weekly_hours"],
            "max_daily_hours": max(daily_dict.values()) if daily_dict else 0,
            "daily_breakdown": daily_dict,
            "lecture_hours": data["lecture_hours"],
            "lab_hours": data["lab_hours"],
            "subjects_taught": sorted(list(data["subjects_taught"])),
            "sections_taught": sorted(list(data["sections_taught"]))
        }

    fac_out = os.path.join(SEED_DIR, f"{prefix}_faculty.json")
    with open(fac_out, "w", encoding="utf-8") as f:
        json.dump(formatted_faculty, f, indent=2)
    print(f"  • Saved {prefix}_faculty.json ({len(formatted_faculty)} faculty members)")

    # 4. Rooms Breakdown
    rooms_dict = defaultdict(lambda: {
        "total_occupied_hours": 0,
        "room_type": "classroom",
        "sections_using": set(),
        "daily_breakdown": defaultdict(int)
    })

    for e in raw_entries:
        rm = e.room
        if rm and rm not in ["LIBRARY", "BREAK", "LUNCH"]:
            rtype = "gpu_lab" if "AFTF" in rm else ("computer_lab" if rm in ["604", "605", "606", "611", "612", "615", "616", "617"] else "classroom")
            rooms_dict[rm]["room_type"] = rtype
            rooms_dict[rm]["total_occupied_hours"] += 1
            rooms_dict[rm]["sections_using"].add(e.section)
            rooms_dict[rm]["daily_breakdown"][e.day] += 1

    formatted_rooms = {}
    for rm_code, data in sorted(rooms_dict.items()):
        formatted_rooms[rm_code] = {
            "room_code": rm_code,
            "room_type": data["room_type"],
            "total_occupied_hours": data["total_occupied_hours"],
            "daily_breakdown": dict(data["daily_breakdown"]),
            "sections_using": sorted(list(data["sections_using"]))
        }

    rooms_out = os.path.join(SEED_DIR, f"{prefix}_rooms.json")
    with open(rooms_out, "w", encoding="utf-8") as f:
        json.dump(formatted_rooms, f, indent=2)
    print(f"  • Saved {prefix}_rooms.json ({len(formatted_rooms)} rooms)")

    # 5. Sections Breakdown
    sections_dict = defaultdict(lambda: {
        "total_slots": 0,
        "subjects": defaultdict(int),
        "rooms_used": set()
    })

    for e in raw_entries:
        sec = e.section
        sections_dict[sec]["total_slots"] += 1
        sections_dict[sec]["subjects"][e.subject_code] += 1
        if e.room:
            sections_dict[sec]["rooms_used"].add(e.room)

    formatted_sections = {}
    for sec_name, data in sorted(sections_dict.items()):
        year_level = "IV" if "IV" in sec_name or "sec" in sec_name.lower() else ("III" if "III" in sec_name else "II")
        formatted_sections[sec_name] = {
            "section_name": sec_name,
            "year_level": year_level,
            "total_weekly_slots": data["total_slots"],
            "subjects_breakdown": dict(data["subjects"]),
            "rooms_used": sorted(list(data["rooms_used"]))
        }

    sec_out = os.path.join(SEED_DIR, f"{prefix}_sections.json")
    with open(sec_out, "w", encoding="utf-8") as f:
        json.dump(formatted_sections, f, indent=2)
    print(f"  • Saved {prefix}_sections.json ({len(formatted_sections)} sections)")

    # 6. Subjects Breakdown
    subjects_dict = defaultdict(lambda: {
        "subject_code": "",
        "subject_type": "L",
        "total_demand_hours": 0,
        "assigned_faculty": set(),
        "sections_offering": set()
    })

    for e in raw_entries:
        sub = e.subject_code
        if sub:
            stype = "P" if "(P)" in sub or "(T&P)" in sub else ("T" if "(T)" in sub else ("LIBRARY" if "LIBRARY" in sub else "L"))
            subjects_dict[sub]["subject_code"] = sub
            subjects_dict[sub]["subject_type"] = stype
            subjects_dict[sub]["total_demand_hours"] += 1
            subjects_dict[sub]["sections_offering"].add(e.section)
            
            facs = sec_sub_to_fac.get((e.section, sub), [])
            for f in facs:
                subjects_dict[sub]["assigned_faculty"].add(f)

    formatted_subjects = {}
    for sub_code, data in sorted(subjects_dict.items()):
        formatted_subjects[sub_code] = {
            "subject_code": sub_code,
            "subject_type": data["subject_type"],
            "total_demand_hours": data["total_demand_hours"],
            "sections_count": len(data["sections_offering"]),
            "assigned_faculty": sorted(list(data["assigned_faculty"])),
            "sections_offering": sorted(list(data["sections_offering"]))
        }

    sub_out = os.path.join(SEED_DIR, f"{prefix}_subjects.json")
    with open(sub_out, "w", encoding="utf-8") as f:
        json.dump(formatted_subjects, f, indent=2)
    print(f"  • Saved {prefix}_subjects.json ({len(formatted_subjects)} subjects)")

    return {
        "entries": entries_list,
        "sections": formatted_sections,
        "faculty": formatted_faculty,
        "rooms": formatted_rooms,
        "subjects": formatted_subjects
    }

def generate_combined_master(v5_data, v4_data, yr4_data):
    print("\n==================================================")
    print(" GENERATING COMBINED MASTER TIMETABLE DATASET")
    print("==================================================")
    
    all_sections = {}
    all_faculty = set()
    all_rooms = set()
    all_subjects = set()
    all_entries = []

    for dataset in [v5_data, v4_data, yr4_data]:
        if not dataset:
            continue
        all_entries.extend(dataset["entries"])
        all_sections.update(dataset["sections"])
        all_faculty.update(dataset["faculty"].keys())
        all_rooms.update(dataset["rooms"].keys())
        all_subjects.update(dataset["subjects"].keys())

    master_summary = {
        "total_combined_entries": len(all_entries),
        "total_combined_sections": len(all_sections),
        "total_combined_faculty": len(all_faculty),
        "total_combined_rooms": len(all_rooms),
        "total_combined_subjects": len(all_subjects),
        "sections_list": sorted(list(all_sections.keys())),
        "faculty_list": sorted(list(all_faculty)),
        "rooms_list": sorted(list(all_rooms)),
        "subjects_list": sorted(list(all_subjects))
    }

    master_out = os.path.join(SEED_DIR, "master_combined_timetables_summary.json")
    with open(master_out, "w", encoding="utf-8") as f:
        json.dump(master_summary, f, indent=2)
    print(f"  * Saved master_combined_timetables_summary.json:")

    print(f"    - Combined Entries:  {master_summary['total_combined_entries']}")
    print(f"    - Combined Sections: {master_summary['total_combined_sections']}")
    print(f"    - Combined Faculty:  {master_summary['total_combined_faculty']}")
    print(f"    - Combined Rooms:    {master_summary['total_combined_rooms']}")
    print(f"    - Combined Subjects: {master_summary['total_combined_subjects']}")

def main():
    v5_data = process_excel_dataset(V5_PATH, "original_v5")
    v4_data = process_excel_dataset(V4_PATH, "original_v4")
    yr4_data = process_excel_dataset(YR4_PATH, "original_4th_year")

    generate_combined_master(v5_data, v4_data, yr4_data)

if __name__ == '__main__':
    main()
