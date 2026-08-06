import os
import io
import re
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List, Optional
from backend.parser.excel_parser import ExcelTimetableParser, normalize_faculty_name
from backend.solver.conflict_checker import ConflictChecker

router = APIRouter()

def get_source_filepath(dataset: str) -> str:
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    file_map = {
        "4th_year": os.path.join(root_dir, "4th yr TT 17TH JULY.xlsx"),
        "e2e_test": os.path.join(root_dir, "data", "test_outputs", "Test3_Focused10Sections_Cohort.xlsx"),
        "v5_baseline": os.path.join(root_dir, "data", "ACSE_TIMETABLE_V5.xlsx")
    }

    file_path = file_map.get(dataset, file_map["4th_year"])
    if not os.path.exists(file_path):
        for alt in [file_map["4th_year"], file_map["v5_baseline"], os.path.join(root_dir, "time_table", "ACSE TIMETABLE (V5)  - W.e.f 15-7-2026.xlsx")]:
            if os.path.exists(alt):
                file_path = alt
                break
    return file_path


@router.get("/tested-data", response_model=Dict[str, Any])
async def get_tested_timetable_data(
    dataset: str = Query("4th_year", description="Dataset type: '4th_year', 'e2e_test', or 'v5_baseline'"),
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

        sections_list.append({
            "id": sec_name.lower().replace(" ", "_").replace("-", "_"),
            "name": sec_name,
            "year_level": "IV Year" if "SECTION" in sec_name.upper() else "II/III Year",
            "branch": "CSE (AIML)",
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
