import os
import json
from typing import Dict, Any, List

_SEED_CACHE: Dict[str, Any] = {}

IGNORED_ROOM_CODES = {
    "", "NONE", "LIBRARY", "BREAK", "LUNCH", "SL/EL", "/AL/IL", "AL/IL", "MINORS/HONORS",
    "MINOR/HONOR", "MINORS", "HONORS", "N/A", "NA", "-", "ONLINE", "CRT", "OE"
}


def get_seed_data() -> Dict[str, Any]:
    global _SEED_CACHE
    if _SEED_CACHE:
        return _SEED_CACHE

    paths = [
        "data/seed/demo_timetable_seed.json",
        "../data/seed/demo_timetable_seed.json",
        "/app/data/seed/demo_timetable_seed.json",
        "c:/Users/ggvfj/Downloads/All Projects/Time_Table/data/seed/demo_timetable_seed.json"
    ]

    raw_data = None
    for p in paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                    break
            except Exception as ex:
                print(f"[SeedCache JSON Read Warning] {ex}")

    if not raw_data:
        from parser.excel_parser import ExcelTimetableParser, resolve_v5_path
        try:
            parsed = ExcelTimetableParser().parse_file(resolve_v5_path())
            raw_data = {
                "sections": [{"id": idx + 1, "name": sname} for idx, sname in enumerate(parsed.sections.keys())],
                "rooms": [{"id": idx + 1, "code": r} for idx, r in enumerate(parsed.raw_entries if hasattr(parsed, 'raw_entries') else [])],
                "faculty": [],
                "subjects": [],
                "entries": []
            }
        except Exception:
            raw_data = {}

    # Sanitize and strictly format entities with valid Integer IDs for Pydantic models
    raw_rooms = raw_data.get("rooms", [])
    clean_rooms = []
    seen_room_codes = set()

    for idx, r in enumerate(raw_rooms):
        code = str(r.get("code") or r.get("id") or "").strip().upper()
        if code and code not in IGNORED_ROOM_CODES and code not in seen_room_codes:
            seen_room_codes.add(code)
            rtype = "gpu_lab" if "AFTF" in code else ("computer_lab" if code in ["604", "605", "606", "611", "612", "615", "616", "617"] else "classroom")
            cap = 72 if "AFTF" in code else (60 if rtype == "computer_lab" else 66)
            clean_rooms.append({
                "id": len(clean_rooms) + 1,
                "code": code,
                "room_type": rtype,
                "capacity": cap,
                "floor": "AFTF" if "AFTF" in code else ("AFF" if "AFF" in code else code[0] if code[0].isdigit() else "1"),
                "block": "Aryabhatta Bhavan / U-Block",
                "gpu_capable": "AFTF" in code,
                "is_available": True
            })

    raw_fac = raw_data.get("faculty", [])
    clean_fac = []
    for idx, fac in enumerate(raw_fac):
        fname = str(fac.get("name") or fac.get("id") or f"Faculty {idx+1}")
        clean_fac.append({
            "id": idx + 1,
            "name": fname,
            "employee_id": str(fac.get("employee_id") or f"FAC-{100 + idx + 1}"),
            "designation": str(fac.get("designation") or ("Associate Professor" if "DR" in fname.upper() else "Assistant Professor")),
            "max_hours_per_week": int(fac.get("max_hours_per_week") or (14 if "DR" in fname.upper() else 16)),
            "max_daily_classes": 5,
            "is_external": bool(fac.get("is_external", False)),
            "dept_id": 1,
            "availability": fac.get("availability") or {}
        })

    raw_secs = raw_data.get("sections", [])
    clean_secs = []
    for idx, sec in enumerate(raw_secs):
        sname = str(sec.get("name") or sec.get("id") or f"Section {idx+1}")
        y_lvl = 2 if "II " in sname else (3 if "III " in sname else (4 if "IV " in sname else 1))
        lbl = sname.split("-")[-1].strip() if "-" in sname else sname[-1]
        clean_secs.append({
            "id": idx + 1,
            "name": sname,
            "label": lbl,
            "year_level": y_lvl,
            "strength": int(sec.get("strength") or (66 if "501" not in sname else 30)),
            "branch_id": 1,
            "academic_year_id": 1,
            "is_active": True
        })

    raw_subjs = raw_data.get("subjects", [])
    clean_subjs = []
    for idx, sub in enumerate(raw_subjs):
        code = str(sub.get("code") or f"SUBJ-{idx+1}")
        is_l = "(P)" in code or "LAB" in code.upper()
        clean_subjs.append({
            "id": idx + 1,
            "code": code,
            "full_name": str(sub.get("full_name") or code),
            "lecture_hours": 0 if is_l else 3,
            "tutorial_hours": 1 if "(T)" in code else 0,
            "lab_hours": 2 if is_l else 0,
            "is_lab": is_l,
            "gpu_required": "AFTF" in code,
            "slot_type": "P" if is_l else ("T" if "(T)" in code else "L"),
            "requires_consecutive": 2 if is_l else 1
        })

    _SEED_CACHE = {
        "sections": clean_secs,
        "rooms": clean_rooms,
        "faculty": clean_fac,
        "subjects": clean_subjs,
        "entries": raw_data.get("entries", [])
    }
    return _SEED_CACHE
