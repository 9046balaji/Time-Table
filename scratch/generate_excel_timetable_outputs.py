import sys
import os
import openpyxl

sys.path.insert(0, '.')
sys.path.insert(0, 'backend')

from parser.excel_exporter import ExcelTimetableExporter
from scratch.e2e_manual_and_ai_wizard_timetable_test import test_ai_wizard_timetable_generation

def main():
    print("\n" + "="*80)
    print(" GENERATING OFFICIAL VFSTR EXCEL WORKBOOK OUTPUT (.XLSX)")
    print("="*80)

    # 1. Run AI Wizard CP-SAT Solver to generate 100% clash-free timetable
    ai_result = test_ai_wizard_timetable_generation()
    
    # 2. Export to official VFSTR Excel Workbook (.xlsx) format
    exporter = ExcelTimetableExporter()
    
    # Format entries for exporter
    slots = [
        {
            "section": e.get("section") or e.get("sectionName") or e.get("section_name"),
            "day": e.get("day"),
            "period": e.get("period"),
            "subject": e.get("subject") or e.get("subjectCode") or e.get("subject_code"),
            "room": e.get("room") or e.get("roomCode") or e.get("room_code") or "",
            "faculty": e.get("faculty") or e.get("facultyName") or ""
        }
        for e in ai_result.get("entries", [])
    ]
    
    formatted_data = {
        "sections": [{"name": s["name"]} for s in [
            {"name": "II AIML-A"}, {"name": "II AIML-B"}, {"name": "III AIML-A"}, {"name": "IV AIML-A"},
            {"name": "II CS-A"}, {"name": "II DS-A"}, {"name": "II AIML-C"}, {"name": "II AIML-D"},
            {"name": "III AIML-B"}, {"name": "IV AIML-B"}
        ]],
        "slots": slots
    }
    
    excel_bytes = exporter.export_cohort_excel("II_AIML", formatted_data)


    # Save output to both data/test_outputs/ and time_table/ directories
    out_dir1 = os.path.join("data", "test_outputs")
    os.makedirs(out_dir1, exist_ok=True)
    out_path1 = os.path.join(out_dir1, "VFSTR_ACSE_TIMETABLE_AI_WIZARD_GENERATED.xlsx")

    out_dir2 = "time_table"
    os.makedirs(out_dir2, exist_ok=True)
    out_path2 = os.path.join(out_dir2, "VFSTR_ACSE_TIMETABLE_AI_WIZARD_GENERATED.xlsx")

    with open(out_path1, "wb") as f:
        f.write(excel_bytes)

    with open(out_path2, "wb") as f:
        f.write(excel_bytes)

    print(f"\n  [SUCCESS] Generated Excel workbook saved to:")
    print(f"    1. {out_path1}")
    print(f"    2. {out_path2}")

    # 3. Verify created Excel sheets & format
    wb = openpyxl.load_workbook(out_path1, data_only=True)
    print(f"\n  [Excel Verification] Total Sheets: {len(wb.sheetnames)}")
    print(f"  [Excel Verification] Sheet Names: {wb.sheetnames}")
    
    sheet = wb["II AIML-A"]
    print(f"\n  [Sample Sheet: II AIML-A] Dimensions: Max Row = {sheet.max_row}, Max Col = {sheet.max_column}")
    print("  --- Top 12 Rows Preview of Generated Excel Sheet ---")
    for r in range(1, 13):
        row_vals = [sheet.cell(r, c).value for c in range(1, 12)]
        print(f"    Row {r:2d}: {row_vals}")

    print("\n" + "="*80)
    print(" OFFICIAL EXCEL WORKBOOK GENERATION COMPLETED SUCCESSFULLY ")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
