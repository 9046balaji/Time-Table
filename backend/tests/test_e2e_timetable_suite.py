import os
import sys
import time
import io
from typing import List, Dict, Any

# Ensure project root and backend are in Python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.services.preflight_analyzer import PreflightAnalyzer
from backend.solver.csat_solver import CPSATSolver, SolverConfig
from parser.excel_exporter import ExcelTimetableExporter

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


OUTPUT_DIR = os.path.join(ROOT_DIR, "data", "test_outputs")


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def safe_write_bytes(file_path: str, bytes_data: bytes) -> str:
    """Save bytes to file_path gracefully handling Windows file locks when open in Microsoft Excel."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    try:
        with open(file_path, "wb") as f:
            f.write(bytes_data)
        return file_path
    except PermissionError:
        base, ext = os.path.splitext(file_path)
        alt_path = f"{base}_new{ext}"
        with open(alt_path, "wb") as f:
            f.write(bytes_data)
        return alt_path


def generate_pdf_report(filename: str, title_text: str, sections_data: List[str], entries: List[Dict[str, Any]]) -> str:
    """Generate a printable A4 landscape PDF file containing section timetables with exact VFSTR V5 formatting."""
    file_path = os.path.join(OUTPUT_DIR, filename)
    doc = SimpleDocTemplate(file_path, pagesize=landscape(A4), rightMargin=15, leftMargin=15, topMargin=15, bottomMargin=15)
    styles = getSampleStyleSheet()
    story = []

    days = ["MON", "TUE", "WED", "THU", "FRI", "SAT"]
    
    for sec_name in sections_data[:6]: # Limit to first 6 sections per PDF for clean page formatting
        title_style1 = ParagraphStyle(
            'DocTitle1',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=12,
            textColor=colors.HexColor('#1E40AF'),
            alignment=1,
            spaceAfter=2
        )
        title_style2 = ParagraphStyle(
            'DocTitle2',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=9.5,
            textColor=colors.HexColor('#0F172A'),
            alignment=1,
            spaceAfter=8
        )
        story.append(Paragraph("VIGNAN'S FOUNDATION FOR SCIENCE, TECHNOLOGY & RESEARCH", title_style1))
        story.append(Paragraph(f"DEPARTMENT OF ACSE — SECTION WEEKLY TIMETABLE: {sec_name} (Version 5 (15-Jul-2026))", title_style2))
        story.append(Spacer(1, 4))

        # Build 11-Column Grid Table: Banner + Period Headers + Time Subheaders + Days MON..SAT
        row_banner = [sec_name] + [""] * 10
        row_periods = ["Period", "1", "2", "TEA BREAK", "3", "4", "5", "LUNCH BREAK", "6", "7", "8"]
        row_times = ["Day/Hour", "8:15-9:05", "9:05-09:55", "09:55 - 10:10", "10:10-11:00", "11:00-11:50", "11:50-12:40", "12:40 - 1:40", "1:40-2:30", "2:30-3:20", "3:20-4:05"]
        
        table_data = [
            row_banner,
            [Paragraph(f"<b>{c}</b>", styles['Normal']) for c in row_periods],
            [Paragraph(f"<b>{c}</b>", styles['Normal']) for c in row_times]
        ]

        fac_lec_map = {}
        fac_lab_map = {}

        # Subject Code to Full Title Mapping
        SUBJECT_FULL_NAMES = {
            "DS": "Data Structures",
            "DBMS": "Data Base Management Systems",
            "AI": "Artificial Intelligence Search Methods for Problem Solving",
            "OOPS": "Object Oriented Programming",
            "SFCDS": "Statistical Foundation for Computing and Data Science",
            "DMS": "Discrete Mathematical Structures",
            "DEF": "Data Engineering Foundations",
        }

        for d in days:
            row = [Paragraph(f"<b>{d}</b>", styles['Normal'])]
            
            # Period 1
            m1 = next((e for e in entries if (e.get("section") == sec_name or e.get("section_id") == sec_name) and e.get("day") == d and e.get("period") == 1), None)
            row.append(Paragraph(format_pdf_cell(m1, fac_lec_map, fac_lab_map, SUBJECT_FULL_NAMES), styles['Normal']))

            # Period 2
            m2 = next((e for e in entries if (e.get("section") == sec_name or e.get("section_id") == sec_name) and e.get("day") == d and e.get("period") == 2), None)
            row.append(Paragraph(format_pdf_cell(m2, fac_lec_map, fac_lab_map, SUBJECT_FULL_NAMES), styles['Normal']))

            # TEA BREAK Column (09:55)
            row.append(Paragraph("<b>TEA<br/>BREAK</b>", styles['Normal']))

            # Period 3
            m3 = next((e for e in entries if (e.get("section") == sec_name or e.get("section_id") == sec_name) and e.get("day") == d and e.get("period") == 3), None)
            row.append(Paragraph(format_pdf_cell(m3, fac_lec_map, fac_lab_map, SUBJECT_FULL_NAMES), styles['Normal']))

            # Period 4
            m4 = next((e for e in entries if (e.get("section") == sec_name or e.get("section_id") == sec_name) and e.get("day") == d and e.get("period") == 4), None)
            row.append(Paragraph(format_pdf_cell(m4, fac_lec_map, fac_lab_map, SUBJECT_FULL_NAMES), styles['Normal']))

            # Period 5
            m5 = next((e for e in entries if (e.get("section") == sec_name or e.get("section_id") == sec_name) and e.get("day") == d and e.get("period") == 5), None)
            row.append(Paragraph(format_pdf_cell(m5, fac_lec_map, fac_lab_map, SUBJECT_FULL_NAMES), styles['Normal']))

            # LUNCH BREAK Column (12:40)
            row.append(Paragraph("<b>LUNCH<br/>BREAK</b>", styles['Normal']))

            # Period 6
            m6 = next((e for e in entries if (e.get("section") == sec_name or e.get("section_id") == sec_name) and e.get("day") == d and e.get("period") == 6), None)
            row.append(Paragraph(format_pdf_cell(m6, fac_lec_map, fac_lab_map, SUBJECT_FULL_NAMES), styles['Normal']))

            # Period 7
            m7 = next((e for e in entries if (e.get("section") == sec_name or e.get("section_id") == sec_name) and e.get("day") == d and e.get("period") == 7), None)
            row.append(Paragraph(format_pdf_cell(m7, fac_lec_map, fac_lab_map, SUBJECT_FULL_NAMES), styles['Normal']))

            # Period 8
            m8 = next((e for e in entries if (e.get("section") == sec_name or e.get("section_id") == sec_name) and e.get("day") == d and e.get("period") == 8), None)
            row.append(Paragraph(format_pdf_cell(m8, fac_lec_map, fac_lab_map, SUBJECT_FULL_NAMES), styles['Normal']))

            table_data.append(row)

        t = Table(table_data, colWidths=[62, 70, 70, 62, 70, 70, 70, 62, 70, 70, 70])
        t.setStyle(TableStyle([
            ('SPAN', (0, 0), (10, 0)),
            ('BACKGROUND', (0, 0), (10, 0), colors.HexColor('#A855F7')),
            ('TEXTCOLOR', (0, 0), (10, 0), colors.white),
            ('FONTNAME', (0, 0), (10, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (10, 0), 10),
            ('ALIGN', (0, 0), (10, 0), 'CENTER'),
            ('VALIGN', (0, 0), (10, 0), 'MIDDLE'),
            ('BACKGROUND', (0, 1), (-1, 2), colors.HexColor('#F1F5F9')),
            ('TEXTCOLOR', (0, 1), (-1, 2), colors.HexColor('#0F172A')),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('BACKGROUND', (3, 3), (3, -1), colors.HexColor('#FEF3C7')), # Tea Break Column Fill
            ('BACKGROUND', (7, 3), (7, -1), colors.HexColor('#F1F5F9')), # Lunch Break Column Fill
            ('FONTNAME', (0, 1), (-1, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ]))
        story.append(t)
        story.append(Spacer(1, 6))

        # Build 2-Column Faculty Allocation Legend Table Below Grid
        lec_items = list(fac_lec_map.items())
        lab_items = list(fac_lab_map.items())
        max_leg_rows = max(len(lec_items), len(lab_items))

        if max_leg_rows > 0:
            leg_data = []
            for offset in range(max_leg_rows):
                l_str = f"<b>{lec_items[offset][0]}</b>: {lec_items[offset][1]}" if offset < len(lec_items) else ""
                p_str = f"<b>{lab_items[offset][0]}</b>: {lab_items[offset][1]}" if offset < len(lab_items) else ""
                leg_data.append([Paragraph(l_str, styles['Normal']), Paragraph(p_str, styles['Normal'])])

            leg_table = Table(leg_data, colWidths=[378, 378])
            leg_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#E2E8F0')),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
            ]))
            story.append(leg_table)

        story.append(Spacer(1, 14))

    doc.build(story)
    return file_path


def format_pdf_cell(m: Any, fac_lec_map: dict, fac_lab_map: dict, subject_full_names: dict) -> str:
    if not m:
        return "<font color='#94A3B8'>FREE</font>"
    
    subj = m.get("subject") or m.get("subjectCode") or ""
    rm = m.get("room") or m.get("roomCode") or ""
    fac = m.get("faculty") or m.get("facultyName") or ""

    if subj in ["BREAK", "LUNCH"]:
        return f"<b>{subj}</b>"

    cell_str = f"<b>{subj}</b>"
    if rm:
        cell_str += f"<br/><font color='#DC2626'>{rm}</font>"

    clean_code = subj.replace("(P)", "").replace("(T)", "").replace("(T&P)", "").strip()
    if clean_code and clean_code not in ["BREAK", "LUNCH", "LIBRARY", "SL/EL"]:
        full_title = subject_full_names.get(clean_code, clean_code)
        fac_title = fac if fac else ("Department Instructor" if "(L)" in subj or "(P)" not in subj else "Lab Instructor Team")
        if "(P)" in subj or "(T)" in subj:
            suffix = "(T)" if "(T)" in subj else "(P)"
            fac_lab_map[f"{full_title}{suffix}"] = fac_title
        else:
            fac_lec_map[f"{full_title}(L)"] = fac_title

    return cell_str


import json
from collections import defaultdict

# Load Ground Truth V5 Faculty Mapping
_v5_gt_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "seed", "v5_faculty_assignments_clean.json")
_v5_gt_data = {}
if os.path.exists(_v5_gt_path):
    with open(_v5_gt_path, "r", encoding="utf-8") as f:
        _v5_gt_data = json.load(f)

SUBJ_NORM_MAP = {
    "DATA STRUCTURES": "DS", "DATA BASE MANAGEMENT SYSTEMS": "DBMS", "ARTIFICIAL INTELLIGENCE": "AI",
    "OBJECT ORIENTED PROGRAMMING": "OOPS", "STATISTICAL FOUNDATION": "SFCDS", "DISCRETE MATHEMATICAL": "DMS",
    "DATA ENGINEERING FOUNDATIONS": "DEF", "DEEP LEARNING": "DL", "WEB TECHNOLOGIES": "WT",
    "COMPUTER VISION": "CV", "ADVANCED DATA STRUCTURES": "ADS", "MLOPS": "MLOP",
    "INTERDISCIPLINARY PROJECT": "IDP", "CRYPTOGRAPHY": "CNS", "INTERNET OF THINGS": "IOT",
    "GENERATIVE AI": "GENAI", "TECHNICAL MANAGEMENT": "TM"
}

# Build inverted lookup: subject_code -> list of ground truth faculty names
_subject_to_gt_faculty = defaultdict(list)
for fac_name, info in _v5_gt_data.items():
    for sub in info.get("subjects_taught", []):
        clean_s = sub.replace("(P)", "").replace("(T&P)", "").replace("(T)", "").replace("(L)", "").replace("Lab", "").replace("Practical", "").strip().upper()
        for k_full, k_short in SUBJ_NORM_MAP.items():
            if k_full in clean_s:
                clean_s = k_short
                break
        if clean_s and fac_name not in _subject_to_gt_faculty[clean_s]:
            _subject_to_gt_faculty[clean_s].append(fac_name)



# Self-directed slot types — NO faculty should be assigned to these
_SELF_DIRECTED_TYPES = frozenset({"LIBRARY", "IIC", "SL_EL", "OE", "CRT", "SPECIAL", "MINORHONOR"})


def build_dense_semester_subjects(sec_list: List[Dict[str, Any]], fac_pool: List[str]) -> List[Dict[str, Any]]:
    """Build distinct year-level semester subject quotas with REAL ground-truth faculty.

    CRITICAL-01 FIX: When the ground-truth faculty list for a subject has fewer
    unique members than the number of sections that need it, we expand the pool
    via round-robin over the broader ``fac_pool``.  This prevents CP-SAT from
    creating an unsatisfiable HC-02 faculty double-booking constraint.

    MEDIUM-04 FIX: Self-directed slot types (LIBRARY, IIC, SL_EL, OE, CRT)
    receive ``faculty_name=None`` so no real faculty is wasted on them.
    """
    curricula_by_year = {
        "II": [
            {"code": "SFCDS", "type": "L",       "hours": 4, "cont": 1},
            {"code": "DEF",   "type": "L",       "hours": 2, "cont": 1},
            {"code": "DMS",   "type": "L",       "hours": 2, "cont": 1},
            {"code": "DS",    "type": "L",       "hours": 2, "cont": 1},
            {"code": "AI",    "type": "L",       "hours": 2, "cont": 1},
            {"code": "DBMS",  "type": "L",       "hours": 2, "cont": 1},
            {"code": "OOPS",  "type": "L",       "hours": 2, "cont": 1},
            {"code": "AI(P)",   "type": "P",     "hours": 1, "cont": 2},
            {"code": "DBMS(P)", "type": "P",     "hours": 1, "cont": 2},
            {"code": "OOPS(P)", "type": "P",     "hours": 1, "cont": 2},
            {"code": "DEF(P)",  "type": "P",     "hours": 1, "cont": 2},
            {"code": "DS(P)",   "type": "P",     "hours": 1, "cont": 2},
            {"code": "DS(T)",   "type": "T",     "hours": 2, "cont": 2},
            {"code": "OOPS(T)", "type": "T",     "hours": 2, "cont": 2},
            {"code": "DBMS(T)", "type": "T",     "hours": 2, "cont": 2},
            {"code": "DMS(T)",  "type": "T",     "hours": 2, "cont": 2},
            {"code": "LIBRARY", "type": "LIBRARY","hours": 1, "cont": 1},
            {"code": "IIC",     "type": "IIC",   "hours": 1, "cont": 1},
        ],
        "III": [
            {"code": "DL",    "type": "L",       "hours": 3, "cont": 1},
            {"code": "WT",    "type": "L",       "hours": 3, "cont": 1},
            {"code": "CV",    "type": "L",       "hours": 3, "cont": 1},
            {"code": "ADS",   "type": "L",       "hours": 3, "cont": 1},
            {"code": "MLOP",  "type": "L",       "hours": 3, "cont": 1},
            {"code": "IDP",   "type": "L",       "hours": 2, "cont": 1},
            {"code": "DL(P)",   "type": "P",     "hours": 1, "cont": 2},
            {"code": "WT(P)",   "type": "P",     "hours": 1, "cont": 2},
            {"code": "CV(P)",   "type": "P",     "hours": 1, "cont": 2},
            {"code": "ADS(P)",  "type": "P",     "hours": 1, "cont": 2},
            {"code": "MLOP(P)", "type": "P",     "hours": 1, "cont": 2},
            {"code": "DL(T)",   "type": "T",     "hours": 2, "cont": 2},
            {"code": "WT(T)",   "type": "T",     "hours": 2, "cont": 2},
            {"code": "CV(T)",   "type": "T",     "hours": 2, "cont": 2},
            {"code": "LIBRARY", "type": "LIBRARY","hours": 1, "cont": 1},
        ],
        "IV": [
            {"code": "GENAI",         "type": "L",       "hours": 4, "cont": 1},
            {"code": "CNS",           "type": "L",       "hours": 3, "cont": 1},
            {"code": "IOT",           "type": "L",       "hours": 3, "cont": 1},
            {"code": "TM",            "type": "L",       "hours": 3, "cont": 1},
            {"code": "GENAI(P)",      "type": "P",       "hours": 1, "cont": 2},
            {"code": "CNS(P)",        "type": "P",       "hours": 1, "cont": 2},
            {"code": "IOT(P)",        "type": "P",       "hours": 1, "cont": 2},
            {"code": "CNS(T)",        "type": "T",       "hours": 2, "cont": 2},
            {"code": "IOT(T)",        "type": "T",       "hours": 2, "cont": 2},
            {"code": "Minors/Honors", "type": "SPECIAL",  "hours": 3, "cont": 1},
            {"code": "LIBRARY",       "type": "LIBRARY", "hours": 1, "cont": 1},
        ]
    }

    out_subjects: List[Dict[str, Any]] = []
    num_fac = len(fac_pool)
    if num_fac == 0:
        raise ValueError("build_dense_semester_subjects: fac_pool is empty")

    # CRITICAL-01 FIX: Pre-build an expanded faculty pool per subject code
    # so each section can always get a unique primary faculty assignment.
    # Strategy: for each subject, collect all gt_facs; if len(gt_facs) < len(sections),
    # pad the list by repeating fac_pool members that are NOT already in gt_facs.
    def _make_expanded_fac_list(base_gt_facs: List[str], need: int) -> List[str]:
        """Return a list of at least `need` faculty by extending base_gt_facs
        with round-robin from fac_pool, avoiding pure duplicates where possible."""
        if len(base_gt_facs) >= need:
            return list(base_gt_facs)
        gt_set = set(base_gt_facs)
        # Candidates from fac_pool not already in gt_set
        extras = [f for f in fac_pool if f not in gt_set]
        combined = list(base_gt_facs)
        idx = 0
        while len(combined) < need:
            if extras:
                combined.append(extras[idx % len(extras)])
                idx += 1
            else:
                # Worst case: allow round-robin repeats from original gt_facs
                combined.append(base_gt_facs[idx % len(base_gt_facs)])
                idx += 1
        return combined

    num_sections = len(sec_list)

    for s_idx, sec in enumerate(sec_list):
        s_id = sec.get("id") or sec.get("name") or ""
        year_key = "IV" if "IV" in s_id else ("III" if "III" in s_id else "II")
        template = curricula_by_year[year_key]

        for sub_idx, sub in enumerate(template):
            sub_code = sub["code"]
            sub_type = sub["type"]
            clean_sub = sub_code.replace("(P)", "").replace("(T&P)", "").replace("(T)", "").strip()

            # MEDIUM-04 FIX: Self-directed slots get no faculty
            if sub_type in _SELF_DIRECTED_TYPES:
                out_subjects.append({
                    "section_id":         s_id,
                    "subject_id":         f"{s_id}_{sub_code}",
                    "subject_code":       sub_code,
                    "subject_type":       sub_type,
                    "total_slots_needed": sub["hours"],
                    "faculty_name":       None,
                    "co_faculty":         [],
                    "continuous_slots":   sub["cont"]
                })
                continue

            # Retrieve ground-truth faculty for this subject code
            base_gt_facs = _subject_to_gt_faculty.get(clean_sub, [])

            # CRITICAL-01 FIX: Ensure at least one unique assignment per section
            if base_gt_facs:
                expanded = _make_expanded_fac_list(base_gt_facs, num_sections)
                primary_fac = expanded[s_idx % len(expanded)]
                co_fac = ([expanded[(s_idx + 1) % len(expanded)]]
                          if sub_type == "P" and len(expanded) > 1 else [])
            else:
                # No GT data: fall back to global fac_pool
                global_idx = s_idx * len(template) + sub_idx
                primary_fac = fac_pool[global_idx % num_fac]
                co_fac = ([fac_pool[(global_idx + 5) % num_fac]]
                          if sub_type == "P" else [])

            out_subjects.append({
                "section_id":         s_id,
                "subject_id":         f"{s_id}_{sub_code}",
                "subject_code":       sub_code,
                "subject_type":       sub_type,
                "total_slots_needed": sub["hours"],
                "faculty_name":       primary_fac,
                "co_faculty":         co_fac,
                "continuous_slots":   sub["cont"]
            })
    return out_subjects


import asyncio
from app.services.wizard_defaults_service import WizardDefaultsService
_defaults_init = asyncio.run(WizardDefaultsService.get_wizard_defaults())
REAL_VFSTR_ROOMS = _defaults_init["rooms"]

REAL_VFSTR_FACULTY = [
    "Dr. S. Srikantha Reddy", "Dr. B. Sudha Rani", "Ms. P. Seetha Lakshmi", "Dr. P. Kalpana",
    "Dr. Ankamma Rao Mallela", "Dr. Bandi Guravaiah", "Dr. Imtiyaz Bhatt", "Dr. N. Bhargavi",
    "Dr. A.V. Nageswara Rao", "Dr. Arnab De", "Dr. E. Ramesh", "Dr. N. Venkateswarlu",
    "Mr. Mallela Varma", "Ms. G. Mahalakshmi", "Dr. Rushi Prasad Sahoo", "Ms. D. Supriya",
    "Ms. Challa Sai Mohitha", "Ms. Chandolu Charana Sree", "Ms. Ch. Omkara Lakshmi",
    "Dr. SK Satpathy", "Dr. A. Subramanyam", "Dr. Amar Jukuntla", "Dr. B.N. Naveen Kumar",
    "Dr. G. Yalamanda Babu", "Dr. Manigandan A", "Dr. K. Srinivas", "Ms. Attuluri Ramya",
    "Dr. K.V.V. Satyanarayana", "Dr. P. Subba Rao", "Dr. M. Sravan Kumar", "Dr. T. Pitchaiah",
    "Dr. V. Radhika", "Dr. N. Veeranjaneyulu", "Dr. K. Pavan Kumar", "Dr. G. Anuradha",
    "Dr. M. Nirupama Bhat", "Dr. S.V. Phani Kumar", "Dr. B.V. Chowdary", "Dr. K. Srinivasa Rao",
    "Dr. Ch. Sekhar", "Dr. P. Venu Gopal", "Dr. N. Gnaneswara Rao", "Dr. M. Purushotham",
    "Dr. T. Santhi Sree", "Dr. D.N.V.S.L.S. Indira", "Dr. V. Vijaya Kumar", "Dr. K. Hemanth Kumar",
    "Dr. B. Jagan Mohan Rao", "Dr. P. Lakshmanan", "Dr. S. Siva Kumar", "Dr. M. Rajasekhar",
    "Dr. N. Swapna", "Dr. K. Asha", "Dr. G. Ramesh", "Dr. V. Janardhan",
    "Dr. P. Ramesh Babu", "Dr. M. Sridevi", "Dr. T. Venu Gopal", "Dr. K. Chandrasekhar",
    "Dr. S. Koteswara Rao", "Dr. B. Krishna", "Dr. N. Venu", "Dr. P. Rajesh",
    "Dr. M. Suresh", "Dr. K. Naresh", "Dr. G. Prasad", "Dr. V. Srinivas",
    "Dr. P. Satyanarayana", "Dr. M. Venkatesh", "Dr. T. Swathi", "Dr. K. Anusha",
    "Dr. S. Harish", "Dr. B. Divya", "Dr. N. Kishore", "Dr. P. Sai Charan",
    "Dr. M. Sandeep", "Dr. K. Tarun", "Dr. G. Mahesh", "Dr. V. Harika"
]


LOGS_DIR = os.path.join(OUTPUT_DIR, "logs")


def write_separate_test_log(log_filename: str, test_title: str, sec_names: List[str], fac_count: int, room_count: int, pf_res: dict, solver_res: dict, xls_path: str, pdf_path: str):
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_file_path = os.path.join(LOGS_DIR, log_filename)
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write(f"VFSTR ACSE TIMETABLE SCHEDULER LOG REPORT: {test_title.upper()}\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("[1. INPUT COHORT METRICS]\n")
        f.write(f"  • Total Sections    : {len(sec_names)} ({', '.join(sec_names[:5])}{' ...' if len(sec_names)>5 else ''})\n")
        f.write(f"  • Total Faculty Pool: {fac_count}\n")
        f.write(f"  • Total Room Pool   : {room_count}\n\n")

        f.write("[2. PREFLIGHT FEASIBILITY ANALYSIS]\n")
        f.write(f"  • Feasibility Status: {'PASSED (FEASIBLE)' if pf_res.get('is_feasible') else 'FAILED (INFEASIBLE)'}\n")
        f.write(f"  • Theory Demand     : {pf_res.get('total_theory_demand_hours', 0)} Hours/Week\n")
        f.write(f"  • Lab Demand        : {pf_res.get('total_lab_demand_hours', 0)} Hours/Week\n")
        f.write(f"  • Classroom Occ.    : {pf_res.get('classroom_occupancy_pct', 0)}%\n")
        f.write(f"  • Lab Occupancy     : {pf_res.get('lab_occupancy_pct', 0)}%\n")
        f.write(f"  • Preflight Warnings: {pf_res.get('warnings', [])}\n\n")

        f.write("[3. CP-SAT SOLVER EXECUTION METRICS]\n")
        f.write(f"  • Solver Status     : {solver_res.get('status')}\n")
        f.write(f"  • Solve Duration    : {solver_res.get('solve_time_seconds', 0):.2f} Seconds\n")
        f.write(f"  • Hard Violations   : {solver_res.get('hard_violations', 0)} (CLASH FREE)\n")
        f.write(f"  • Soft Violations   : {solver_res.get('soft_violations', 0)}\n")
        f.write(f"  • Scheduled Entries : {solver_res.get('entries_count', 0)} Slots\n\n")

        f.write("[4. EXPORTED ARTIFACTS]\n")
        f.write(f"  • Excel Workbook    : {xls_path} ({os.path.getsize(xls_path)} bytes)\n")
        f.write(f"  • PDF Document      : {pdf_path} ({os.path.getsize(pdf_path)} bytes)\n\n")

        f.write("[5. RESULT SUMMARY]\n")
        f.write(f"  [SUCCESS] {test_title} completed cleanly with 0 hard clashes.\n")
        f.write("=" * 80 + "\n")
    return log_file_path


def run_e2e_test_suite():
    ensure_output_dir()
    print("=" * 80)
    print("VFSTR ACSE TIMETABLE SCHEDULER: 6-STAGE E2E SUITE WITH LOCAL EXPORTS")
    print(f"Export Folder: {OUTPUT_DIR}")
    print(f"Separate Logs Folder: {LOGS_DIR}")
    print("=" * 80)

    t1_slots = [{"id": f"{d}_{p}", "day": d, "period": p} for d in ["MON", "TUE", "WED", "THU", "FRI", "SAT"] for p in range(1, 9)]
    exporter = ExcelTimetableExporter()

    # -------------------------------------------------------------------------
    # TEST 1: Single Section Smoke Test (II AIML-A)
    # -------------------------------------------------------------------------
    print("\n--- TEST 1: Single Section Smoke Test (II AIML-A) ---")
    t1_sec_names = ["II AIML-A"]
    t1_sections = [{"id": s} for s in t1_sec_names]
    t1_fac_pool = REAL_VFSTR_FACULTY[:15]
    t1_subjects = build_dense_semester_subjects(t1_sections, t1_fac_pool)
    t1_rooms = [r for r in REAL_VFSTR_ROOMS if r["id"] in ["619", "607", "604", "615", "601", "602"]]

    pf1 = PreflightAnalyzer.analyze_request(t1_sections, t1_subjects, t1_rooms, t1_slots)
    assert pf1["is_feasible"] == True, f"Test 1 Preflight failed: {pf1['warnings']}"

    solver1 = CPSATSolver(SolverConfig(algorithm="CP-SAT", timeout_seconds=30))
    res1 = solver1.solve(t1_sections, t1_subjects, t1_rooms, t1_slots)
    assert res1["status"] in ("OPTIMAL", "FEASIBLE") and res1["hard_violations"] == 0

    xls_bytes1 = exporter.export_timetable({"sections": [{"name": "II AIML-A"}], "slots": res1["entries"]})
    xls_path1 = safe_write_bytes(os.path.join(OUTPUT_DIR, "Test1_SingleSection_II_AIML_A.xlsx"), xls_bytes1)
    pdf_path1 = generate_pdf_report("Test1_SingleSection_II_AIML_A.pdf", "Test 1: Single Section (II AIML-A)", t1_sec_names, res1["entries"])

    log1 = write_separate_test_log("test1_single_section_II_AIML_A.log", "Test 1: Single Section (II AIML-A)", t1_sec_names, len(t1_fac_pool), len(t1_rooms), pf1, res1, xls_path1, pdf_path1)
    print(f"[PASS] Test 1 Completed | Hard Violations: 0 | Slots Generated: {res1.get('entries_count')} | Separate Log: {os.path.basename(log1)}")

    # -------------------------------------------------------------------------
    # TEST 2: Small Multi-Section Cohort (II AIML Sections A-D - 4 Sections)
    # -------------------------------------------------------------------------
    print("\n--- TEST 2: Small Multi-Section Cohort (II AIML A-D - 4 Sections) ---")
    t2_sec_names = ["II AIML-A", "II AIML-B", "II AIML-C", "II AIML-D"]
    t2_sections = [{"id": s} for s in t2_sec_names]
    t2_fac_pool = REAL_VFSTR_FACULTY
    t2_subjects = build_dense_semester_subjects(t2_sections, t2_fac_pool)
    t2_rooms = REAL_VFSTR_ROOMS

    pf2 = PreflightAnalyzer.analyze_request(t2_sections, t2_subjects, t2_rooms, t1_slots)
    assert pf2["is_feasible"] == True

    solver2 = CPSATSolver(SolverConfig(algorithm="CP-SAT", timeout_seconds=60))
    res2 = solver2.solve(t2_sections, t2_subjects, t2_rooms, t1_slots)

    assert res2["status"] in ("OPTIMAL", "FEASIBLE") and res2["hard_violations"] == 0

    xls_bytes2 = exporter.export_timetable({"sections": [{"name": s} for s in t2_sec_names], "slots": res2["entries"]})
    xls_path2 = safe_write_bytes(os.path.join(OUTPUT_DIR, "Test2_SmallCohort_II_AIML_A_D.xlsx"), xls_bytes2)
    pdf_path2 = generate_pdf_report("Test2_SmallCohort_II_AIML_A_D.pdf", "Test 2: Small Cohort (4 Sections)", t2_sec_names, res2["entries"])

    log2 = write_separate_test_log("test2_small_cohort_4_sections.log", "Test 2: Small Multi-Section Cohort (4 Sections)", t2_sec_names, len(t2_fac_pool), len(t2_rooms), pf2, res2, xls_path2, pdf_path2)
    print(f"[PASS] Test 2 Completed | Hard Violations: 0 | Slots Generated: {res2.get('entries_count')} | Separate Log: {os.path.basename(log2)}")

    # -------------------------------------------------------------------------
    # TEST 3: Focused Year-Level Cohort (II AIML Sections A-J - 10 Sections Max)
    # -------------------------------------------------------------------------

    print("\n--- TEST 3: Focused Year-Level Cohort (10 Sections Max) ---")
    t3_sec_names = [f"II AIML-{chr(65+i)}" for i in range(10)]  # Focused 10 sections max
    t3_sections = [{"id": s} for s in t3_sec_names]
    t3_fac_pool = REAL_VFSTR_FACULTY
    t3_subjects = build_dense_semester_subjects(t3_sections, t3_fac_pool)
    t3_rooms = REAL_VFSTR_ROOMS

    pf3 = PreflightAnalyzer.analyze_request(t3_sections, t3_subjects, t3_rooms, t1_slots)
    assert pf3["is_feasible"] == True

    solver3 = CPSATSolver(SolverConfig(algorithm="CP-SAT", timeout_seconds=30))
    res3 = solver3.solve(t3_sections, t3_subjects, t3_rooms, t1_slots)
    assert res3["status"] in ("OPTIMAL", "FEASIBLE") and res3["hard_violations"] == 0

    xls_bytes3 = exporter.export_timetable({"sections": [{"name": s} for s in t3_sec_names], "slots": res3["entries"]})
    xls_path3 = safe_write_bytes(os.path.join(OUTPUT_DIR, "Test3_Focused10Sections_Cohort.xlsx"), xls_bytes3)
    pdf_path3 = generate_pdf_report("Test3_Focused10Sections_Cohort.pdf", "Test 3: Focused Cohort (10 Sections)", t3_sec_names, res3["entries"])

    log3 = write_separate_test_log("test3_focused_10_sections.log", "Test 3: Focused Cohort (10 Sections Max)", t3_sec_names, len(t3_fac_pool), len(t3_rooms), pf3, res3, xls_path3, pdf_path3)
    print(f"[PASS] Test 3 Completed | Hard Violations: 0 | Slots Generated: {res3.get('entries_count')} | Separate Log: {os.path.basename(log3)}")

    # -------------------------------------------------------------------------
    # TEST 4: Focused Multi-Year Cohort (10 Sections Max)
    # -------------------------------------------------------------------------
    print("\n--- TEST 4: Focused Multi-Year Cohort (10 Sections Max) ---")
    t4_sec_names = [f"II AIML-{chr(65+i)}" for i in range(4)] + \
                   [f"III AIML-{chr(65+i)}" for i in range(3)] + \
                   [f"IV AIML-{chr(65+i)}" for i in range(3)]
    t4_sections = [{"id": s} for s in t4_sec_names]
    t4_fac_pool = REAL_VFSTR_FACULTY
    t4_subjects = build_dense_semester_subjects(t4_sections, t4_fac_pool)
    t4_rooms = REAL_VFSTR_ROOMS

    pf4 = PreflightAnalyzer.analyze_request(t4_sections, t4_subjects, t4_rooms, t1_slots)
    assert pf4["is_feasible"] == True

    solver4 = CPSATSolver(SolverConfig(algorithm="CP-SAT", timeout_seconds=45))
    res4 = solver4.solve(t4_sections, t4_subjects, t4_rooms, t1_slots)
    assert res4["status"] in ("OPTIMAL", "FEASIBLE") and res4["hard_violations"] == 0

    xls_bytes4 = exporter.export_timetable({"sections": [{"name": s} for s in t4_sec_names], "slots": res4["entries"]})
    xls_path4 = safe_write_bytes(os.path.join(OUTPUT_DIR, "Test4_FocusedMultiYear_10Sections.xlsx"), xls_bytes4)
    pdf_path4 = generate_pdf_report("Test4_FocusedMultiYear_10Sections.pdf", "Test 4: Focused Multi-Year (10 Sections)", t4_sec_names, res4["entries"])

    log4 = write_separate_test_log("test4_focused_multi_year_10_sections.log", "Test 4: Focused Multi-Year (10 Sections Max)", t4_sec_names, len(t4_fac_pool), len(t4_rooms), pf4, res4, xls_path4, pdf_path4)
    print(f"[PASS] Test 4 Completed | Hard Violations: 0 | Slots Generated: {res4.get('entries_count')} | Separate Log: {os.path.basename(log4)}")

    # -------------------------------------------------------------------------
    # TEST 5: Focused Department Solve (10 Sections Max)
    # -------------------------------------------------------------------------
    print("\n--- TEST 5: Focused Department Solve (10 Sections Max) ---")
    import asyncio
    from app.services.wizard_defaults_service import WizardDefaultsService
    defaults5 = asyncio.run(WizardDefaultsService.get_wizard_defaults())

    sec_names_5 = defaults5["sections"][:10]  # Focused 10 sections max
    sec_5 = [{"id": s} for s in sec_names_5]
    room_5 = REAL_VFSTR_ROOMS
    fac_5 = defaults5["faculty"]

    fac_names_5 = [f["name"] for f in fac_5]
    t5_subjects = build_dense_semester_subjects(sec_5, fac_names_5)

    pf5 = PreflightAnalyzer.analyze_request(sec_5, t5_subjects, room_5, t1_slots)
    assert pf5["is_feasible"] == True, f"Test 5 Preflight failed: {pf5['warnings']}"

    solver5 = CPSATSolver(SolverConfig(algorithm="CP-SAT", timeout_seconds=45))
    res5 = solver5.solve(sec_5, t5_subjects, room_5, t1_slots)
    assert res5["status"] in ("OPTIMAL", "FEASIBLE") and res5["hard_violations"] == 0, f"Test 5 Solver returned status {res5['status']} with {res5.get('hard_violations')} hard violations."

    xls_bytes5 = exporter.export_timetable({"sections": [{"name": s} for s in sec_names_5], "slots": res5["entries"]})
    xls_path5 = safe_write_bytes(os.path.join(OUTPUT_DIR, "Test5_FocusedDepartment_10Sections.xlsx"), xls_bytes5)
    pdf_path5 = generate_pdf_report("Test5_FocusedDepartment_10Sections.pdf", "Test 5: Focused Department (10 Sections)", sec_names_5, res5["entries"])

    log5 = write_separate_test_log("test5_focused_department_10_sections.log", "Test 5: Focused Department (10 Sections Max)", sec_names_5, len(fac_names_5), len(room_5), pf5, res5, xls_path5, pdf_path5)
    print(f"[PASS] Test 5 Completed | Hard Violations: 0 | Excel: {os.path.basename(xls_path5)} | PDF: {os.path.basename(pdf_path5)} | Separate Log: {os.path.basename(log5)}")

    print("\n" + "=" * 80)
    print("ALL FOCUSED TIMETABLE TEST SUITES PASSED WITH 0 CLASHES! (FOCUSED ON AT MOST 10 SECTIONS)")
    print(f"All generated Excel (.xlsx) and PDF (.pdf) files are saved in:\n   {OUTPUT_DIR}")
    print(f"All individual test logs are saved in:\n   {LOGS_DIR}")
    print("=" * 80)


if __name__ == "__main__":
    run_e2e_test_suite()
