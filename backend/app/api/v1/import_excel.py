import os
import io
import re
import shutil
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from typing import Dict, Any
from app.core.config import settings
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
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Payload Error: Uploaded file exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB."
        )

    if len(content) < 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parse Error: Uploaded payload is empty or corrupted."
        )

    # Byte-level magic number inspection (PK Zip header for OOXML .xlsx)
    if not (content.startswith(b"PK\x03\x04") or content.startswith(b"\xd0\xcf\x11\xe0")):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Security Error: File header does not match valid Excel spreadsheet MIME structure."
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

        # Build Section Breakdown Report
        clash_sections = set()
        clash_rooms = set()
        clash_faculty = set()
        for d in report.details:
            clash_sections.add(d.section_a)
            clash_sections.add(d.section_b)
            if d.clash_type == "ROOM":
                clash_rooms.add(d.key)
            elif d.clash_type == "FACULTY":
                clash_faculty.add(d.key)

        sections_report = []
        for sec_name, slots in parsed_res.sections.items():
            rooms = sorted(list(set(s.room for s in slots if s.room)))
            faculty_members = sorted(list(set(f for s in slots for f in s.faculty_list if f)))
            subjects = sorted(list(set(s.subject_code for s in slots if s.subject_code and s.subject_code not in ["BREAK", "LUNCH"])))
            ct = slots[0].class_teacher if slots and hasattr(slots[0], "class_teacher") else ""

            l_count = sum(1 for s in slots if s.subject_type == "L")
            p_count = sum(1 for s in slots if s.subject_type in ["P", "T&P"])
            t_count = sum(1 for s in slots if s.subject_type == "T")

            sections_report.append({
                "name": sec_name,
                "total_slots": len(slots),
                "lecture_slots": l_count,
                "lab_slots": p_count,
                "tutorial_slots": t_count,
                "rooms": rooms,
                "faculty_count": len(faculty_members),
                "faculty_list": faculty_members,
                "subjects": subjects,
                "class_teacher": ct,
                "has_clash": sec_name in clash_sections,
            })
        sections_report.sort(key=lambda x: x["name"])

        # Build Faculty Workload Report
        faculty_map = {}
        for s in parsed_res.raw_entries:
            for f in s.faculty_list:
                if not f or f in ["LIBRARY", "BREAK", "LUNCH"]:
                    continue
                if f not in faculty_map:
                    faculty_map[f] = {
                        "name": f,
                        "total_hours": 0,
                        "sections": set(),
                        "subjects": set(),
                        "rooms": set(),
                    }
                faculty_map[f]["total_hours"] += 1
                faculty_map[f]["sections"].add(s.section)
                if s.subject_code and s.subject_code not in ["BREAK", "LUNCH"]:
                    faculty_map[f]["subjects"].add(s.subject_code)
                if s.room:
                    faculty_map[f]["rooms"].add(s.room)

        faculty_report = [
            {
                "name": info["name"],
                "total_hours": info["total_hours"],
                "sections_count": len(info["sections"]),
                "sections": sorted(list(info["sections"])),
                "subjects": sorted(list(info["subjects"])),
                "rooms": sorted(list(info["rooms"])),
                "has_clash": any(f_name.lower() in f_key.lower() for f_key in clash_faculty for f_name in [info["name"]]),
            }
            for info in faculty_map.values()
        ]
        faculty_report.sort(key=lambda x: x["name"])

        # Build Rooms Utilization Report
        rooms_map = {}
        for s in parsed_res.raw_entries:
            rm = s.room
            if not rm:
                continue
            if rm not in rooms_map:
                rooms_map[rm] = {
                    "code": rm,
                    "total_slots": 0,
                    "sections": set(),
                    "subjects": set(),
                }
            rooms_map[rm]["total_slots"] += 1
            rooms_map[rm]["sections"].add(s.section)
            if s.subject_code and s.subject_code not in ["BREAK", "LUNCH"]:
                rooms_map[rm]["subjects"].add(s.subject_code)

        rooms_report = [
            {
                "code": rm_info["code"],
                "total_slots": rm_info["total_slots"],
                "sections_count": len(rm_info["sections"]),
                "sections": sorted(list(rm_info["sections"])),
                "subjects": sorted(list(rm_info["subjects"])),
                "occupancy_rate": min(100, round((rm_info["total_slots"] / 48) * 100)),
                "has_clash": rm_info["code"] in clash_rooms,
            }
            for rm_info in rooms_map.values()
        ]
        rooms_report.sort(key=lambda x: x["code"])

        # Build Subjects Distribution Report
        subjects_map = {}
        for s in parsed_res.raw_entries:
            code = s.subject_code
            if not code or code in ["BREAK", "LUNCH"]:
                continue
            if code not in subjects_map:
                subjects_map[code] = {
                    "code": code,
                    "type": s.subject_type,
                    "total_slots": 0,
                    "sections": set(),
                    "faculty": set(),
                }
            subjects_map[code]["total_slots"] += 1
            subjects_map[code]["sections"].add(s.section)
            for f in s.faculty_list:
                if f:
                    subjects_map[code]["faculty"].add(f)

        subjects_report = [
            {
                "code": info["code"],
                "type": info["type"],
                "total_slots": info["total_slots"],
                "sections_count": len(info["sections"]),
                "sections": sorted(list(info["sections"])),
                "faculty_count": len(info["faculty"]),
                "faculty": sorted(list(info["faculty"])),
            }
            for info in subjects_map.values()
        ]
        subjects_report.sort(key=lambda x: x["code"])

        return {
            "filename": clean_filename,
            "total_sections": parsed_res.total_sections,
            "total_slots": parsed_res.total_slots,
            "total_faculty": len(faculty_report),
            "total_rooms": len(rooms_report),
            "total_subjects": len(subjects_report),
            "faculty_mappings": len(parsed_res.faculty_mappings),
            "hard_violations": report.total_hard_violations,
            "room_clashes": report.room_clashes,
            "faculty_clashes": report.faculty_clashes,
            "status": "VALID" if report.total_hard_violations == 0 else "NEEDS_FIX",
            "clash_details": details_json,
            "sections_report": sections_report,
            "faculty_report": faculty_report,
            "rooms_report": rooms_report,
            "subjects_report": subjects_report,
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

