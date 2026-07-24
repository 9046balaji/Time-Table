import os
import io
import re
import shutil
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from typing import Dict, Any
from backend.parser.excel_parser import ExcelTimetableParser
from backend.solver.conflict_checker import ConflictChecker

router = APIRouter()

MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB limit


def sanitize_filename(filename: str) -> str:
    """Sanitize uploaded filenames to prevent path traversal attacks."""
    clean_name = re.sub(r"[^\w\.-]", "_", filename)
    return clean_name[:100]


@router.post("", response_model=Dict[str, Any])
async def import_excel_timetable(file: UploadFile = File(...)):
    raw_filename = file.filename or "uploaded_timetable.xlsx"
    clean_filename = sanitize_filename(raw_filename)

    if not (clean_filename.endswith(".xlsx") or clean_filename.endswith(".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security Error: Only Excel workbook files (.xlsx, .xls) are allowed."
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Payload Error: Uploaded file exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB."
        )

    if len(content) < 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parse Error: Uploaded payload is empty or corrupted."
        )

    temp_dir = os.path.join(os.getcwd(), "scratch")
    os.makedirs(temp_dir, exist_ok=True)
    temp_filepath = os.path.join(temp_dir, f"uploaded_{clean_filename}")

    try:
        with open(temp_filepath, "wb") as buffer:
            buffer.write(content)

        parser = ExcelTimetableParser()
        parsed_res = parser.parse_file(temp_filepath)

        checker = ConflictChecker()
        report = checker.detect(parsed_res)

        details_json = [
            {
                "clash_type": d.clash_type,
                "type": d.clash_type,
                "day": d.day,
                "period": d.period,
                "key": d.key,
                "room": d.key if d.clash_type == "ROOM" else "",
                "faculty": d.key if d.clash_type == "FACULTY" else "",
                "section_a": d.section_a,
                "subject_a": d.subject_a,
                "section_b": d.section_b,
                "subject_b": d.subject_b,
                "message": d.message
            }
            for d in report.details
        ]

        return {
            "filename": clean_filename,
            "total_sections": parsed_res.total_sections,
            "total_slots": parsed_res.total_slots,
            "faculty_mappings": len(parsed_res.faculty_mappings),
            "hard_violations": report.total_hard_violations,
            "room_clashes": report.room_clashes,
            "faculty_clashes": report.faculty_clashes,
            "status": "VALID" if report.total_hard_violations == 0 else "NEEDS_FIX",
            "clash_details": details_json
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Excel Parsing Failed: Structural error detected in sheet layouts. ({str(e)})"
        )
    finally:
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except Exception:
                pass

