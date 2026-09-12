import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.section import Section
from app.services.timetable_service import TimetableService


class CalendarSyncService:
    """
    RFC 5545 compliant iCalendar (.ics) Generator Service.
    Enables dynamic calendar subscriptions for Sections, Cohorts, and Departments
    with native synchronization support for Google Calendar, Apple Calendar, and Microsoft Outlook.
    """

    PERIOD_TIMES = {
        1: ("081500", "090500"),
        2: ("090500", "095500"),
        3: ("101000", "110000"),
        4: ("110000", "115000"),
        5: ("115000", "124000"),
        6: ("134000", "143000"),
        7: ("143000", "152000"),
        8: ("152000", "160500"),
    }

    DAY_TO_BYDAY = {
        "MON": "MO", "TUE": "TU", "WED": "WE", "THU": "TH", "FRI": "FR", "SAT": "SA"
    }

    # Reference Monday for recurrence base (e.g. 2026-07-13)
    REFERENCE_MONDAY = datetime(2026, 7, 13)

    DAY_OFFSETS = {
        "MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5
    }

    @staticmethod
    def _build_ics_document(
        cal_name: str,
        events: List[Dict[str, Any]],
        reference_monday: Optional[datetime] = None,
        semester_weeks: int = 18
    ) -> str:
        """Constructs an RFC 5545 VCALENDAR document with semester recurrence boundaries."""
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            f"PRODID:-//VFSTR University//Timetable Scheduler V2.1//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            f"X-WR-CALNAME:{cal_name}",
            "X-WR-TIMEZONE:Asia/Kolkata",
        ]

        ref_monday = reference_monday or CalendarSyncService.REFERENCE_MONDAY
        term_end = ref_monday + timedelta(weeks=semester_weeks)
        until_str = term_end.strftime("%Y%m%dT235959Z")
        now_str = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

        for idx, ev in enumerate(events):
            day = str(ev.get("day", "MON")).upper()[:3]
            p = int(ev.get("period", 1))
            times = CalendarSyncService.PERIOD_TIMES.get(p, ("081500", "090500"))
            byday = CalendarSyncService.DAY_TO_BYDAY.get(day, "MO")
            offset = CalendarSyncService.DAY_OFFSETS.get(day, 0)

            event_date = ref_monday + timedelta(days=offset)
            date_str = event_date.strftime("%Y%m%d")

            dtstart = f"{date_str}T{times[0]}"
            dtend = f"{date_str}T{times[1]}"

            subj = str(ev.get("subject", "Class Slot"))
            room = str(ev.get("room", "Campus Room"))
            sec = str(ev.get("section", "Section"))
            fac = str(ev.get("faculty", "Faculty"))

            uid = f"slot_{sec}_{day}_P{p}_{idx}@timetable.vfstr.ac.in"

            lines.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{now_str}",
                f"DTSTART;TZID=Asia/Kolkata:{dtstart}",
                f"DTEND;TZID=Asia/Kolkata:{dtend}",
                f"RRULE:FREQ=WEEKLY;BYDAY={byday};UNTIL={until_str}",
                f"SUMMARY:{subj} ({sec})",
                f"LOCATION:{room}",
                f"DESCRIPTION:Subject: {subj}\\nSection: {sec}\\nRoom: {room}\\nInstructor: {fac}",
                "STATUS:CONFIRMED",
                "END:VEVENT"
            ])

        lines.append("END:VCALENDAR")
        return "\r\n".join(lines) + "\r\n"

    @staticmethod
    async def generate_section_ical(
        db: AsyncSession,
        section_identifier: str,
        version_id: int = 5
    ) -> str:
        """Generates dynamic .ics calendar stream for a single academic section."""
        tt_res = await TimetableService.get_version_timetable(db, version_id=version_id, section_name="ALL")
        all_entries = tt_res.get("entries", [])

        # Filter by section ID or name
        target_norm = section_identifier.upper().replace("-", " ").strip()
        section_entries = [
            e for e in all_entries
            if target_norm in str(e.get("section", "")).upper().replace("-", " ") or str(e.get("section_id")) == section_identifier
        ]

        cal_name = f"VFSTR {section_identifier} Timetable"
        return CalendarSyncService._build_ics_document(cal_name, section_entries)

    @staticmethod
    async def generate_cohort_ical(
        db: AsyncSession,
        cohort_key: str,
        version_id: int = 5
    ) -> str:
        """Generates dynamic .ics calendar for an entire academic year cohort (e.g. 'YEAR_2', 'YEAR_3', 'YEAR_4')."""
        tt_res = await TimetableService.get_version_timetable(db, version_id=version_id, section_name="ALL")
        all_entries = tt_res.get("entries", [])

        c_key = cohort_key.upper()
        if "2" in c_key or "II" in c_key:
            cohort_entries = [e for e in all_entries if "II " in str(e.get("section", ""))]
            label = "2nd Year Cohort"
        elif "3" in c_key or "III" in c_key:
            cohort_entries = [e for e in all_entries if "III " in str(e.get("section", ""))]
            label = "3rd Year Cohort"
        elif "4" in c_key or "IV" in c_key:
            cohort_entries = [e for e in all_entries if "IV " in str(e.get("section", ""))]
            label = "4th Year Cohort"
        else:
            cohort_entries = all_entries
            label = "All Cohorts"

        return CalendarSyncService._build_ics_document(f"VFSTR {label} Master Calendar", cohort_entries)

    @staticmethod
    async def generate_master_ical(
        db: AsyncSession,
        version_id: int = 5
    ) -> str:
        """Generates full department master .ics calendar stream."""
        tt_res = await TimetableService.get_version_timetable(db, version_id=version_id, section_name="ALL")
        return CalendarSyncService._build_ics_document(f"VFSTR ACSE Master Timetable V{version_id}", tt_res.get("entries", []))
