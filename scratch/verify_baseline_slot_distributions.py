import sys
import os
import json
from collections import defaultdict

sys.path.insert(0, '.')
sys.path.insert(0, 'backend')

from parser.excel_parser import ExcelTimetableParser, resolve_v5_path

def analyze_v5_baseline_slots_distribution():
    v5_path = resolve_v5_path()
    parser = ExcelTimetableParser()
    parsed = parser.parse_file(v5_path)

    sections_dict = parsed.sections
    print("==================================================================================")
    print("      V5 BASELINE TIMETABLE — EXACT WEEKLY & DAILY SLOT BREAKDOWN AUDIT           ")
    print("==================================================================================")
    print(f"Total Sections Audited: {len(sections_dict)}")

    cohort_breakdown = defaultdict(list)

    for sname, slots in sections_dict.items():
        total_possible = 48 # 6 days * 8 periods
        counts = {
            "theory_lecture": 0,
            "practical_lab": 0,
            "tutorial": 0,
            "library": 0,
            "iic": 0,
            "minors_honors": 0,
            "crt": 0,
            "sl_el": 0,
            "total_filled_classes": 0,
            "total_empty_free_slots": 0
        }

        daily_filled = defaultdict(int)

        for s in slots:
            scode = (s.subject_code or "").upper().strip()
            stype = s.subject_type
            day = s.day

            counts["total_filled_classes"] += 1
            daily_filled[day] += 1

            if "LIBRARY" in scode or "LIB" in scode:
                counts["library"] += 1
            elif "IIC" in scode:
                counts["iic"] += 1
            elif "MINOR" in scode or "HONOR" in scode:
                counts["minors_honors"] += 1
            elif "CRT" in scode:
                counts["crt"] += 1
            elif "SL/EL" in scode or "SL_EL" in scode or "EXPERIENTIAL" in scode:
                counts["sl_el"] += 1
            elif stype == "P" or "(P)" in scode or "LAB" in scode:
                counts["practical_lab"] += 1
            elif stype == "T" or "(T)" in scode:
                counts["tutorial"] += 1
            else:
                counts["theory_lecture"] += 1

        counts["total_empty_free_slots"] = total_possible - counts["total_filled_classes"]
        counts["daily_classes_breakdown"] = dict(daily_filled)
        counts["avg_classes_per_day"] = round(counts["total_filled_classes"] / 6.0, 1)

        # Categorize by Year Group / Cohort
        if "II AIML" in sname:
            cohort_breakdown["2nd Year AIML"].append((sname, counts))
        elif "III AIML" in sname:
            cohort_breakdown["3rd Year AIML"].append((sname, counts))
        elif "IV AIML" in sname:
            cohort_breakdown["4th Year AIML"].append((sname, counts))
        elif "CS" in sname:
            cohort_breakdown["CS Cohort"].append((sname, counts))
        elif "DS" in sname:
            cohort_breakdown["DS Cohort"].append((sname, counts))
        else:
            cohort_breakdown["Other Cohorts"].append((sname, counts))

    # Print Cohort Averages & Sample Section Breakdown
    summary_report = {}

    for cname, list_secs in cohort_breakdown.items():
        print(f"\n----------------------------------------------------------------------------------")
        print(f" COHORT: {cname} ({len(list_secs)} Sections)")
        print(f"----------------------------------------------------------------------------------")
        
        avg_filled = sum(c[1]["total_filled_classes"] for c in list_secs) / len(list_secs)
        avg_empty = sum(c[1]["total_empty_free_slots"] for c in list_secs) / len(list_secs)
        avg_lib = sum(c[1]["library"] for c in list_secs) / len(list_secs)
        avg_theory = sum(c[1]["theory_lecture"] for c in list_secs) / len(list_secs)
        avg_lab = sum(c[1]["practical_lab"] for c in list_secs) / len(list_secs)

        print(f"  [Cohort Averages]")
        print(f"    Avg Filled Classes/Week : {avg_filled:.1f} slots ({avg_filled/6.0:.1f} classes/day)")
        print(f"    Avg Empty/Free Slots    : {avg_empty:.1f} slots ({avg_empty/6.0:.1f} free slots/day)")
        print(f"    Avg Theory Lectures     : {avg_theory:.1f} slots")
        print(f"    Avg Practical Labs      : {avg_lab:.1f} slots")
        print(f"    Avg Library Slots       : {avg_lib:.1f} slots")

        print(f"\n  [Sample Sections Detail]")
        for sname, c in list_secs[:3]:
            print(f"    • {sname:<12}: Filled={c['total_filled_classes']:2d} | Free={c['total_empty_free_slots']:2d} | Lib={c['library']} | Theory={c['theory_lecture']} | Lab={c['practical_lab']} | Tut={c['tutorial']} | Daily={c['daily_classes_breakdown']}")

        summary_report[cname] = {
            "avg_filled": avg_filled,
            "avg_empty": avg_empty,
            "avg_library": avg_lib,
            "sections_detail": {s[0]: s[1] for s in list_secs}
        }

    out_json = os.path.join("scratch", "v5_baseline_slot_distribution_audit.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary_report, f, indent=2)

    print(f"\n[SUCCESS] Baseline Slot Distribution Audit Saved to: {out_json}")

if __name__ == "__main__":
    analyze_v5_baseline_slots_distribution()
