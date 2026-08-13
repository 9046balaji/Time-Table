import re
from typing import Tuple, Dict, Optional, Set


# Full-title → short-code bridge (50+ subject variants from VFSTR ACSE)
SUBJECT_TITLE_TO_CODE: Dict[str, str] = {
    # Core II Year AIML
    "DATA STRUCTURES": "DS",
    "STATISTICAL FOUNDATION FOR COMPUTING": "SFCDS",
    "STATISTICAL FOUNDATION": "SFCDS",
    "DISCRETE MATHEMATICAL STRUCTURES": "DMS",
    "DISCRETE MATHEMATICAL": "DMS",
    "DISCRETE MATH": "DMS",
    "ARTIFICIAL INTELLIGENCE": "AI",
    "DATABASE MANAGEMENT SYSTEMS": "DBMS",
    "DATABASE MANAGEMENT": "DBMS",
    "OBJECT ORIENTED PROGRAMMING": "OOPS",
    "OBJECT-ORIENTED PROGRAMMING": "OOPS",
    "DATA ENGINEERING FOUNDATIONS": "DEF",
    "DATA ENGINEERING": "DEF",
    # III Year
    "DEEP LEARNING": "DL",
    "WEB TECHNOLOGIES": "WT",
    "COMPUTER VISION": "CV",
    "ADVANCED DATA STRUCTURES": "ADS",
    "ADVANCED DATA STRUCTURES AND ALGORITHMS": "ADS",
    "MACHINE LEARNING OPERATIONS": "MLOP",
    "MLOPS": "MLOP",
    "INTERDISCIPLINARY PROJECT": "IDP",
    "INTER DISCIPLINARY PROJECT": "IDP",
    "IDP PROJECT": "IDP",
    # IV Year
    "GENERATIVE AI": "GENAI",
    "GENERATIVE ARTIFICIAL INTELLIGENCE": "GENAI",
    "GEN AI": "GENAI",
    "CRYPTOGRAPHY AND NETWORK SECURITY": "CNS",
    "CRYPTOGRAPHY & NETWORK SECURITY": "CNS",
    "INTERNET OF THINGS": "IOT",
    "TECHNICAL MANAGEMENT": "TM",
    # Special / common
    "MACHINE LEARNING": "ML",
    "NATURAL LANGUAGE PROCESSING": "NLP",
    "REINFORCEMENT LEARNING": "RL",
    "CLOUD COMPUTING": "CC",
    "OPERATIONS RESEARCH": "OR",
    "QUANTITATIVE APTITUDE": "QALR",
    "QUANTITATIVE ANALYSIS": "QALR",
    "OPEN ELECTIVE": "OE",
    "CAREER READINESS TRAINING": "CRT",
    "INNOVATION AND INCUBATION": "IIC",
    "SELF LEARNING": "SL_EL",
    "SL/EL/IL": "SL_EL",
}


def normalize_faculty_name(raw: Optional[str]) -> str:
    """
    Strips legend artefacts like '(P):' / '(L):' prefixes, leading dots,
    collapsed whitespace and trailing punctuation from raw faculty name strings.
    """
    if not raw:
        return ""
    name = str(raw).strip()
    # Remove type-prefix artefacts e.g. "(P):Dr. Name", "(T&P):Name"
    name = re.sub(r'^\([A-Z&]+\)\s*:', '', name).strip()
    # Remove leading dots or commas
    name = name.lstrip('.').lstrip(',').strip()
    # Collapse multiple spaces
    name = re.sub(r'\s+', ' ', name)
    return name


def normalize_room_code(raw: Optional[str]) -> str:
    """
    Standardizes room strings, correcting known typos (e.g. UFTF-13 -> AFTF-13),
    stripping lock annotations, and categorizing external seminar halls.
    """
    if not raw:
        return ""
    room = str(raw).strip().upper()

    # Typo correction: UFTF-13 -> AFTF-13
    if "UFTF-13" in room:
        room = room.replace("UFTF-13", "AFTF-13")

    # Lock annotation removal e.g. AFTF-12(LOCK)
    if "LOCK" in room:
        room = re.sub(r"\(.*LOCK.*\)", "", room, flags=re.IGNORECASE).strip()

    # External venues
    if ":" in room or "SEMINAR" in room or "P-BLOCK" in room:
        room = "EXTERNAL"

    return room


def normalize_subject_code(subj_part: Optional[str]) -> Tuple[str, str]:
    """
    Given a raw legend subject part like 'Data Structures(L)' or 'DS(T&P)',
    returns (clean_code, type_suffix) e.g. ('DS', '(L)') or ('DS', '(T&P)').
    """
    if not subj_part:
        return "", ""
    
    subj_str = str(subj_part).strip()
    subj_upper = subj_str.upper()

    # Extract type suffix
    suffix = ""
    for s in ["(T&P)", "(T)", "(P)", "(L)"]:
        if s in subj_upper:
            suffix = s
            break

    # Strip suffix from the text to get bare title
    bare = re.sub(r'\([A-Z&]+\)', '', subj_str).strip()
    bare_upper = bare.upper()

    # Direct short-code match check
    if len(bare) <= 8 and bare_upper.replace("-", "").replace("_", "").isalpha():
        return bare_upper, suffix

    # Full-title lookup
    for title, code in SUBJECT_TITLE_TO_CODE.items():
        if title in bare_upper:
            return code, suffix

    # Fallback: return first word as code
    first_word = bare_upper.split()[0] if bare_upper.split() else bare_upper
    return first_word, suffix


def normalize_section_name(raw: Optional[str]) -> str:
    """Standardizes section header text."""
    if not raw:
        return ""
    clean_name = str(raw).replace("\n", " ").strip()
    clean_name = re.sub(r"\s+", " ", clean_name)
    return clean_name
