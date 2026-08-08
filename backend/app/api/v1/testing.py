import os
import io
import re
import json
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Dict, Any, List, Optional
from backend.parser.excel_parser import ExcelTimetableParser, normalize_faculty_name
from backend.solver.conflict_checker import ConflictChecker

router = APIRouter()

def get_source_filepath(dataset: str) -> str:
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    file_map = {
        "4th_year": os.path.join(root_dir, "time_table", "4th yr TT 17TH JULY.xlsx"),
        "e2e_test": os.path.join(root_dir, "data", "test_outputs", "Test3_Focused10Sections_Cohort.xlsx"),
        "multi_branch_e2e": os.path.join(root_dir, "time_table", "ACSE TIMETABLE (V5)  - W.e.f 15-7-2026.xlsx"),
        "multi_year_e2e": os.path.join(root_dir, "time_table", "ACSE TIMETABLE (V5)  - W.e.f 15-7-2026.xlsx"),
        "test5_dept": os.path.join(root_dir, "time_table", "ACSE TIMETABLE (V5)  - W.e.f 15-7-2026.xlsx"),
        "v5_baseline": os.path.join(root_dir, "time_table", "ACSE TIMETABLE (V5)  - W.e.f 15-7-2026.xlsx")
    }

    file_path = file_map.get(dataset, file_map["v5_baseline"])
    if not os.path.exists(file_path):
        for alt in [file_map["4th_year"], file_map["v5_baseline"], os.path.join(root_dir, "4th yr TT 17TH JULY.xlsx")]:
            if os.path.exists(alt):
                file_path = alt
                break
    return file_path



@router.get("/tested-data", response_model=Dict[str, Any])
async def get_tested_timetable_data(
    dataset: str = Query("4th_year", description="Dataset type"),
    max_sections: int = Query(10, description="Max sections to return (default 10)")
):
    file_path = get_source_filepath(dataset)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Source dataset file not found: {file_path}")

    parser = ExcelTimetableParser()
    res = parser.parse_file(file_path, max_sections=max_sections)

    checker = ConflictChecker()
    report = checker.detect(res)

    sections_list = []
    for sec_name, slots in res.sections.items():
        class_teacher_name = ""
        class_teacher_phone = ""
        if slots and hasattr(slots[0], "class_teacher") and slots[0].class_teacher:
            ct_raw = slots[0].class_teacher
            m = re.search(r'(.*?)\s*\((.*?)\)', ct_raw)
            if m:
                class_teacher_name = m.group(1).strip()
                class_teacher_phone = m.group(2).strip()
            else:
                class_teacher_name = ct_raw

        slot_list = []
        for s in slots:
            rm = s.room or ""
            is_inherited = False
            if hasattr(s, "raw_cell") and s.raw_cell:
                if not re.search(r'\[(N-[\w\-]+|AFTF-[\w\-]+|\d{3}\w?)\]|\((N-[\w\-]+|AFTF-[\w\-]+|\d{3}\w?)\)', s.raw_cell):
                    is_inherited = True

            fac_name = s.faculty_list[0] if s.faculty_list else ""
            fac_phone = ""
            co_fac = []
            if len(s.faculty_list) > 1:
                co_fac = [{"name": f} for f in s.faculty_list[1:]]

            if fac_name:
                pm = re.search(r'(.*?)\s*\((\d{10})\)', fac_name)
                if pm:
                    fac_name = pm.group(1).strip()
                    fac_phone = pm.group(2).strip()

            is_combined = False
            combined_sec = []
            if "AI(" in s.subject_code or "CE(" in s.subject_code:
                is_combined = True
                combined_sec = [sec_name]

            stype_map = {
                "L": "L",
                "P": "P",
                "T": "T",
                "SL_EL": "PROJECT",
                "MINORHONOR": "MINOR"
            }
            sub_type = stype_map.get(s.subject_type, "L")
            if is_combined:
                sub_type = "SPECIAL"

            slot_list.append({
                "id": f"{sec_name}_{s.day}_{s.period}",
                "day": s.day,
                "period": s.period,
                "time_window": getattr(s, "time_window", ""),
                "subject_code": s.subject_code,
                "subject_title": s.subject_code.split("[")[0].split("(")[0].strip(),
                "subject_type": sub_type,
                "room_code": rm,
                "is_inherited_room": is_inherited,
                "primary_faculty": fac_name or "Faculty Assigned",
                "primary_phone": fac_phone,
                "co_faculty": co_fac,
                "is_combined": is_combined,
                "combined_sections": combined_sec
            })

        # Dynamic branch and year detection
        branch = "CSE (AIML)"
        if "CSE" in sec_name and "AIML" not in sec_name:
            branch = "CSE (Core)"
        elif "DS" in sec_name:
            branch = "CSE (Data Science)"
        elif "CS" in sec_name and "CSE" not in sec_name:
            branch = "CSE (Cyber Security)"

        year_level = "II Year"
        if "III" in sec_name:
            year_level = "III Year"
        elif "IV" in sec_name or "SECTION" in sec_name.upper():
            year_level = "IV Year"

        sections_list.append({
            "id": sec_name.lower().replace(" ", "_").replace("-", "_"),
            "name": sec_name,
            "year_level": year_level,
            "branch": branch,
            "class_teacher": {
                "name": class_teacher_name or "Faculty Advisor",
                "phone": class_teacher_phone or "N/A"
            },
            "slots": slot_list
        })

    return {
        "dataset": dataset,
        "file_parsed": os.path.basename(file_path),
        "total_sections": len(sections_list),
        "total_slots": res.total_slots,
        "hard_violations": report.total_hard_violations,
        "room_clashes": report.room_clashes,
        "faculty_clashes": report.faculty_clashes,
        "sections": sections_list
    }


@router.get("/export/excel")
async def export_tested_excel(
    dataset: str = Query("4th_year", description="Dataset type")
):
    file_path = get_source_filepath(dataset)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Excel file not found")

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    filename = f"VFSTR_{dataset.upper()}_10Sections_Timetable.xlsx"
    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/json-inspection")
async def inspect_json_dataset(
    target: str = Query("demo", description="Target JSON: 'demo', 'v5_all', 'test5_sections', 'test5_faculty', 'test5_rooms', 'test5_entries'")
):
    """
    Endpoint for serving pre-parsed seed and solver output JSON files directly.
    """
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    json_map = {
        "demo": os.path.join(root_dir, "data", "seed", "demo_timetable_seed.json"),
        "v5_all": os.path.join(root_dir, "data", "seed", "original_v5_all_entries.json"),
        "test5_sections": os.path.join(root_dir, "data", "test_outputs", "generated_test5_sections.json"),
        "test5_faculty": os.path.join(root_dir, "data", "test_outputs", "generated_test5_faculty.json"),
        "test5_rooms": os.path.join(root_dir, "data", "test_outputs", "generated_test5_rooms.json"),
        "test5_entries": os.path.join(root_dir, "data", "test_outputs", "generated_test5_all_entries.json")
    }

    fpath = json_map.get(target, json_map["demo"])
    if not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail=f"Target JSON file not found: {fpath}")

    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        "target": target,
        "filename": os.path.basename(fpath),
        "file_size_bytes": os.path.getsize(fpath),
        "data": data
    }
