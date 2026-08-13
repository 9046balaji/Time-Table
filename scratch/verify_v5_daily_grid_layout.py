import sys
import os
import json
from collections import defaultdict

sys.path.insert(0, ".")
sys.path.insert(0, "backend")

from parser.excel_parser import ExcelTimetableParser, resolve_v5_path

parsed = ExcelTimetableParser().parse_file(resolve_v5_path())

print("==================================================================================")
print("   V5 BASELINE TIMETABLE — 2ND & 3RD YEAR DAILY PERIOD-BY-PERIOD LAYOUT AUDIT     ")
print("==================================================================================")

ii_aiml_sections = [f"II AIML-{ch}" for ch in ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]]
iii_aiml_sections = [f"III AIML-{ch}" for ch in ["A", "B", "C", "D", "E", "F", "G"]]

def audit_cohort_daily_grid(cohort_name, sec_names):
    print(f"\n==================================================================================")
    print(f" COHORT AUDIT: {cohort_name} ({len(sec_names)} Sections)")
    print(f"==================================================================================")

    # Track free periods and library periods frequency
    period_free_counts = defaultdict(int)
    period_library_counts = defaultdict(int)
    daily_class_counts = defaultdict(list)

    for sname in sec_names:
        sec_entries = [s for s in parsed.raw_entries if s.section == sname]
        grid = defaultdict(dict)
        for s in sec_entries:
            grid[s.day][s.period] = s.subject_code or "CLASS"

        for day in ["MON", "TUE", "WED", "THU", "FRI", "SAT"]:
            day_filled = 0
            for p in range(1, 9):
                val = grid[day].get(p, None)
                if val:
                    day_filled += 1
                    if "LIB" in val.upper():
                        period_library_counts[(day, p)] += 1
                else:
                    period_free_counts[(day, p)] += 1
            daily_class_counts[day].append(day_filled)

    print(f"  [Daily Class Counts Average (out of 8 periods)]")
    for day in ["MON", "TUE", "WED", "THU", "FRI", "SAT"]:
        counts = daily_class_counts[day]
        avg_c = sum(counts) / len(counts)
        print(f"    • {day}: Avg {avg_c:.2f} classes/day (Min: {min(counts)}, Max: {max(counts)})")

    print(f"\n  [Library Slot Placement in V5 Baseline]")
    if period_library_counts:
        for (day, p), cnt in sorted(period_library_counts.items()):
            print(f"    • {day} Period {p}: {cnt} sections have LIBRARY here")
    else:
        print("    • 0 Library slots found in this cohort!")

    print(f"\n  [Top Most Common Free Period Slots in V5 Baseline]")
    sorted_free = sorted(period_free_counts.items(), key=lambda x: x[1], reverse=True)
    for (day, p), cnt in sorted_free[:10]:
        print(f"    • {day} Period {p}: {cnt}/{len(sec_names)} sections are FREE here")

audit_cohort_daily_grid("2nd Year AIML", ii_aiml_sections)
audit_cohort_daily_grid("3rd Year AIML", iii_aiml_sections)
