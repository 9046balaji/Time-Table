import openpyxl
import re
import os
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any, Set

V5_FILE_PATH = "time_table/ACSE TIMETABLE (V5)  - W.e.f 15-7-2026.xlsx"
V3_FILE_PATH = "time_table/ACSE TIMETABLE (V3)  - W.e.f 13-7-2026.xlsx"


def resolve_v5_path(v_name: str = "V5") -> str:
    return resolve_version_path(v_name)


def resolve_version_path(v_name: str = "V5") -> str:
    if str(v_name).upper() in ("3", "V3"):
        candidates = [
            V3_FILE_PATH,
            "data/ACSE_TIMETABLE_V3.xlsx",
            "../time_table/ACSE TIMETABLE (V3)  - W.e.f 13-7-2026.xlsx",
            "/app/time_table/ACSE TIMETABLE (V3)  - W.e.f 13-7-2026.xlsx"
        ]
    else:
        candidates = [
            V5_FILE_PATH,
            "data/ACSE_TIMETABLE_V5.xlsx",
            "../time_table/ACSE TIMETABLE (V5)  - W.e.f 15-7-2026.xlsx",
            "/app/time_table/ACSE TIMETABLE (V5)  - W.e.f 15-7-2026.xlsx"
        ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]


@dataclass
class ParsedSlot:
    section: str
    day: str
    period: int
    subject_code: str
    room: str
    subject_type: str = "L"  # L, T, P, LIBRARY, BREAK, LUNCH, MINORHONOR
    faculty_list: List[str] = field(default_factory=list)
    raw_cell: str = ""
    sheet_name: str = ""


@dataclass
class ParsedResult:
    total_sections: int = 0
    total_slots: int = 0
    sections: Dict[str, List[ParsedSlot]] = field(default_factory=dict)
    faculty_mappings: Dict[str, Dict[str, List[str]]] = field(default_factory=dict)
    raw_entries: List[ParsedSlot] = field(default_factory=list)


class ExcelTimetableParser:
    KNOWN_SECTION_PREFIXES = (
        "II AIML", "III AIML", "IV AIML",
        "II CS", "III CS", "IV CS",
        "II DS", "III DS", "IV DS",
        "II CSBS", "III CSBS", "IV CSBS", "IV - CSBS",
        "II IOT", "III IOT", "IV IOT",
        "I BS(DS)", "II BS(DS)", "III BS(DS)",
        "I MSC", "II MSC", "I MTECH", "II MTECH",
        "MINOR", "HONOR", "MINORHONORS", "MINORS/HONORS"
    )

    DAY_NORM_MAP = {
        "MON": "MON", "MONDAY": "MON",
        "TUE": "TUE", "TUESDAY": "TUE",
        "WED": "WED", "WEDNESDAY": "WED",
        "THU": "THU", "THURSDAY": "THU",
        "FRI": "FRI", "FRIDAY": "FRI",
        "SAT": "SAT", "SATURDAY": "SAT",
    }

    COL_PERIOD_MAP = {
        2: 1, 3: 2,
        5: 3, 6: 4, 7: 5,
        9: 6, 10: 7, 11: 8
    }

    def parse_file(self, file_path: str) -> ParsedResult:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        result = ParsedResult()

        all_slots: List[ParsedSlot] = []
        sections_dict: Dict[str, List[ParsedSlot]] = {}
        faculty_map: Dict[str, Dict[str, List[str]]] = {}

        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            self._parse_sheet(sheet, sheet_name, all_slots, sections_dict, faculty_map)

        # Filter out empty dummy section keys if any
        sections_dict = {k: v for k, v in sections_dict.items() if len(v) > 0}

        result.raw_entries = all_slots
        result.sections = sections_dict
        result.total_sections = len(sections_dict)
        result.total_slots = len(all_slots)
        result.faculty_mappings = faculty_map

        return result

    def _parse_sheet(self, sheet: Any, sheet_name: str, all_slots: List[ParsedSlot],
                     sections_dict: Dict[str, List[ParsedSlot]],
                     faculty_map: Dict[str, Dict[str, List[str]]]):
        merged_value_map: Dict[Tuple[int, int], Tuple[int, int]] = {}
        for rng in sheet.merged_cells.ranges:
            top_left = (rng.min_row, rng.min_col)
            for r in range(rng.min_row, rng.max_row + 1):
                for c in range(rng.min_col, rng.max_col + 1):
                    merged_value_map[(r, c)] = top_left

        max_r = sheet.max_row
        r = 1
        current_section: Optional[str] = None

        while r <= max_r:
            c1_val = str(sheet.cell(r, 1).value or "").strip()
            c2_val = str(sheet.cell(r, 2).value or "").strip()

            sec_header = self._match_section_header(c1_val) or self._match_section_header(c2_val)
            if sec_header:
                current_section = sec_header
                if current_section not in sections_dict:
                    sections_dict[current_section] = []
                if current_section not in faculty_map:
                    faculty_map[current_section] = {}

            c1_upper = c1_val.upper()
            if c1_upper in self.DAY_NORM_MAP and current_section:
                day = self.DAY_NORM_MAP[c1_upper]
                self._parse_day_row(sheet, r, current_section, day, sheet_name,
                                    merged_value_map, all_slots, sections_dict[current_section])

            if current_section and (":" in c1_val or ":" in c2_val):
                line = c1_val if ":" in c1_val else c2_val
                if not any(k in line.upper() for k in ["DEPARTMENT", "PERIOD", "DAY"]):
                    self._parse_faculty_legend(line, current_section, faculty_map)

            r += 1

    def _match_section_header(self, text: str) -> Optional[str]:
        if not text:
            return None
        upper = text.replace("\n", " ").strip().upper()
        if "DEPARTMENT" in upper or "ACADEMIC" in upper or "PERIOD" in upper or "DAY" in upper:
            return None
        if "HONORS--" in upper or "PROBABILITY" in upper or "ELEMENTARY" in upper or "INTERNSHIP" in upper:
            return None
        for prefix in self.KNOWN_SECTION_PREFIXES:
            if upper.startswith(prefix) or upper == prefix:
                clean_name = text.replace("\n", " ").strip()
                clean_name = re.sub(r"\s+", " ", clean_name)
                return clean_name
        return None

    def _get_cell_value(self, sheet: Any, r: int, c: int, merged_map: Dict[Tuple[int, int], Tuple[int, int]]) -> Any:
        if (r, c) in merged_map:
            top_r, top_c = merged_map[(r, c)]
            return sheet.cell(top_r, top_c).value
        return sheet.cell(r, c).value

    def _parse_day_row(self, sheet: Any, r: int, section: str, day: str, sheet_name: str,
                       merged_map: Dict[Tuple[int, int], Tuple[int, int]],
                       all_slots: List[ParsedSlot], section_slots: List[ParsedSlot]):
        for col, period in self.COL_PERIOD_MAP.items():
            cell_val = self._get_cell_value(sheet, r, col, merged_map)
            cell_str = str(cell_val or "").strip()

            if not cell_str or cell_str.upper() in ["BREAK", "LUNCH"]:
                continue

            subj, room, stype = self._extract_subject_room(cell_str)

            slot = ParsedSlot(
                section=section,
                day=day,
                period=period,
                subject_code=subj,
                room=room,
                subject_type=stype,
                raw_cell=cell_str,
                sheet_name=sheet_name
            )

            all_slots.append(slot)
            section_slots.append(slot)

    def _extract_subject_room(self, cell_str: str) -> Tuple[str, str, str]:
        lines = [line.strip() for line in cell_str.split("\n") if line.strip()]
        if not lines:
            return "", "", "L"

        subj = lines[0]
        room = lines[1] if len(lines) > 1 else ""

        if not room:
            parts = subj.rsplit(" ", 1)
            if len(parts) == 2 and re.match(r"^(?:[A-Z]{1,4}-?\d+|\d{3,4}[A-B]?)$", parts[1], re.IGNORECASE):
                subj = parts[0].strip()
                room = parts[1].strip()

        # Appendix B Normalizations
        # 1. Typo UFTF-13 -> AFTF-13
        if "UFTF-13" in room.upper():
            room = room.upper().replace("UFTF-13", "AFTF-13")

        # 2. AFTF-12(U-BLOCK LOCK) -> AFTF-12
        if "LOCK" in room.upper():
            room = re.sub(r"\(.*LOCK.*\)", "", room, flags=re.IGNORECASE).strip()

        # 3. External venue strings
        if ":" in room or "SEMINAR" in room.upper() or "P-BLOCK" in room.upper():
            room = "EXTERNAL"

        stype = "L"
        subj_upper = subj.upper()
        if "(P)" in subj or "LAB" in subj_upper:
            stype = "P"
        elif "(T)" in subj:
            stype = "T"
        elif "LIBRARY" in subj_upper or "LIB" == subj_upper:
            stype = "LIBRARY"
        elif "MINOR" in subj_upper or "HONOR" in subj_upper:
            stype = "MINORHONOR"
        elif any(k in subj_upper for k in ["SL/EL", "AL/IL", "SL/EL/IL", "SL_EL"]):
            stype = "SL_EL"
        elif "IDP" in subj_upper:
            stype = "IDP"
        elif "QALR" in subj_upper:
            stype = "QALR"
        elif "CRT" in subj_upper:
            stype = "CRT"

        return subj, room, stype

    def _parse_faculty_legend(self, line: str, section: str, faculty_map: Dict[str, Dict[str, List[str]]]):
        if ":" not in line:
            return
        parts = line.split(":", 1)
        subj_part = parts[0].strip()
        fac_part = parts[1].strip()

        fac_names = [f.strip() for f in re.split(r"[,;/&]", fac_part) if f.strip()]
        if section not in faculty_map:
            faculty_map[section] = {}
        faculty_map[section][subj_part] = fac_names
