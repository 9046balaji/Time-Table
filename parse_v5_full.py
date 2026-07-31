import openpyxl
import json
import os
import sys
sys.path.insert(0, '.')

from collections import defaultdict
from backend.parser.excel_parser import ExcelTimetableParser

excel_path = r"c:\Users\ggvfj\Downloads\All Projects\Time_Table\time_table\ACSE TIMETABLE (V5)  - W.e.f 15-7-2026.xlsx"
parser = ExcelTimetableParser()
parsed_data = parser.parse_file(excel_path)

entries = parsed_data.raw_entries
print(f"Total extracted timetable slots from V5: {len(entries)}")

# Faculty workload analysis
faculty_workload = defaultdict(lambda: {
    "weekly_hours": 0,
    "daily_hours": defaultdict(int),
    "subjects_taught": set(),
    "sections_taught": set(),
    "lab_hours": 0,
    "lecture_hours": 0
})

sec_sub_to_fac = defaultdict(list)
legend_mappings = parsed_data.faculty_mappings
for sec_name, sub_fac_map in legend_mappings.items():
    for sub_name, f_list in sub_fac_map.items():
        clean_facs = [f.strip() for f in f_list if f and f.strip() and not f.strip()[0].isdigit() and f.strip() not in ["***", "undefined"]]
        sec_sub_to_fac[(sec_name, sub_name)] = clean_facs

for e in entries:
    sec = e.section or "Unknown"
    subj = e.subject_code or "Unknown"
    day = e.day or "Unknown"
    
    assigned_facs = sec_sub_to_fac.get((sec, subj), [])
    if not assigned_facs:
        clean_sub = subj.replace("(P)", "").replace("(T&P)", "").replace("(T)", "").strip()
        for (s, sub_k), f_list in sec_sub_to_fac.items():
            if s == sec and clean_sub in sub_k:
                assigned_facs = f_list
                break

    for f_name in assigned_facs:
        faculty_workload[f_name]["weekly_hours"] += 1
        faculty_workload[f_name]["daily_hours"][day] += 1
        faculty_workload[f_name]["subjects_taught"].add(subj)
        faculty_workload[f_name]["sections_taught"].add(sec)
        
        if "(P)" in subj or "(T&P)" in subj:
            faculty_workload[f_name]["lab_hours"] += 1
        else:
            faculty_workload[f_name]["lecture_hours"] += 1

final_faculty_report = {}
for fac_name, data in sorted(faculty_workload.items()):
    daily_dict = dict(data["daily_hours"])
    max_daily = max(daily_dict.values()) if daily_dict else 0
    final_faculty_report[fac_name] = {
        "weekly_hours": data["weekly_hours"],
        "max_daily_hours": max_daily,
        "daily_breakdown": daily_dict,
        "lecture_hours": data["lecture_hours"],
        "lab_hours": data["lab_hours"],
        "subjects_taught": sorted(list(data["subjects_taught"])),
        "sections_taught": sorted(list(data["sections_taught"]))
    }

out_dir = r"c:\Users\ggvfj\Downloads\All Projects\Time_Table\data\seed"
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "v5_faculty_assignments_extracted.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(final_faculty_report, f, indent=2)

print(f"Successfully extracted {len(final_faculty_report)} unique faculty assignments to {out_path}")

# Format workload dictionary for clean JSON export
final_faculty_report = {}
for fac_name, data in sorted(faculty_workload.items()):
    daily_dict = dict(data["daily_hours"])
    max_daily = max(daily_dict.values()) if daily_dict else 0
    final_faculty_report[fac_name] = {
        "weekly_hours": data["weekly_hours"],
        "max_daily_hours": max_daily,
        "daily_breakdown": daily_dict,
        "lecture_hours": data["lecture_hours"],
        "lab_hours": data["lab_hours"],
        "subjects_taught": sorted(list(data["subjects"])),
        "sections_taught": sorted(list(data["sections"]))
    }

output_json_path = r"c:\Users\ggvfj\Downloads\All Projects\Time_Table\data\seed\v5_faculty_assignments_extracted.json"
os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
with open(output_json_path, "w", encoding="utf-8") as f:
    json.dump(final_faculty_report, f, indent=2)

print(f"Successfully extracted {len(final_faculty_report)} unique faculty assignments to {output_json_path}")
