import asyncio
import os
import sys
from typing import Dict, List, Tuple

from sqlalchemy import select, delete, update
from backend.solver.conflict_checker import faculty_identity_key
from backend.parser.excel_parser import ExcelTimetableParser, resolve_version_path
from app.core.database import AsyncSessionLocal
from app.models.faculty import Faculty
from app.models.room import Room
from app.models.section import Section
from app.models.time_slot import TimeSlot
from app.models.timetable import TimetableVersion, TimetableEntry
from app.services.timetable_service import TimetableService


async def remediate():
    async with AsyncSessionLocal() as db:
        print("[Remediation] 1. Deduplicating faculty records...")
        res_fac = await db.execute(select(Faculty))
        faculties = res_fac.scalars().all()
        by_key: Dict[str, List[Faculty]] = {}
        for f in faculties:
            k = faculty_identity_key(f.name)
            by_key.setdefault(k, []).append(f)

        merged_count = 0
        id_replacement_map: Dict[int, int] = {}
        for k, flist in by_key.items():
            if len(flist) > 1:
                # Pick the canonical one (prefer mixed case / dotted titles)
                def sort_priority(fac: Faculty):
                    score = 0
                    if not fac.name.isupper(): score += 5
                    if "Dr." in fac.name or "Mr." in fac.name or "Ms." in fac.name: score += 3
                    return score

                flist.sort(key=sort_priority, reverse=True)
                primary = flist[0]
                duplicates = flist[1:]
                for dup in duplicates:
                    id_replacement_map[dup.id] = primary.id
                    print(f"  Merging duplicate faculty ID {dup.id} ('{dup.name}') into ID {primary.id} ('{primary.name}')")
                    await db.delete(dup)
                    merged_count += 1

        await db.commit()
        print(f"[Remediation] Successfully merged and removed {merged_count} duplicate faculty rows.")

        print("[Remediation] 2. Re-resolving V5 and V3 Timetable Entry Foreign Keys...")
        # Build lookup dictionaries
        res_rooms = await db.execute(select(Room))
        rooms = res_rooms.scalars().all()
        room_map: Dict[str, int] = {}
        for r in rooms:
            room_map[r.code] = r.id
            room_map[r.code.upper()] = r.id
            room_map[r.code.replace("-", "").replace(" ", "").upper()] = r.id

        res_secs = await db.execute(select(Section))
        sections = res_secs.scalars().all()
        sec_map = {s.name: s.id for s in sections}

        res_slots = await db.execute(select(TimeSlot))
        slots = res_slots.scalars().all()
        slot_map = {(ts.day, ts.period): ts.id for ts in slots if ts.period is not None}

        res_fac_active = await db.execute(select(Faculty))
        active_fac = res_fac_active.scalars().all()
        fac_by_name = {f.name: f.id for f in active_fac}
        fac_by_id_key = {faculty_identity_key(f.name): f.id for f in active_fac}

        def resolve_fids(names: List[str]) -> List[int]:
            out = []
            for n in names:
                fid = fac_by_name.get(n) or fac_by_id_key.get(faculty_identity_key(n))
                if fid and fid not in out:
                    out.append(fid)
            return out

        # Update V5 entries
        v5_path = resolve_version_path("V5")
        parser = ExcelTimetableParser()
        res_v5 = parser.parse_file(v5_path)

        res_entries = await db.execute(select(TimetableEntry))
        entries = res_entries.scalars().all()
        entry_by_sec_slot = {}
        for e in entries:
            entry_by_sec_slot.setdefault((e.section_id, e.time_slot_id), []).append(e)
        print(f"[Remediation] Found {len(entries)} total entries in database to index.")

        from sqlalchemy.orm.attributes import flag_modified
        from app.models.timetable_entry_faculty import TimetableEntryFaculty

        res_existing_fa = await db.execute(select(TimetableEntryFaculty))
        existing_fa = {(fa.timetable_entry_id, fa.faculty_id) for fa in res_existing_fa.scalars().all()}
        new_fa_count = 0

        updated_entries = 0
        for slot in res_v5.raw_entries:
            s_id = sec_map.get(slot.section)
            ts_id = slot_map.get((slot.day, slot.period))
            if not s_id or not ts_id:
                continue

            entries_for_slot = entry_by_sec_slot.get((s_id, ts_id), [])
            for entry in entries_for_slot:
                # Update Room
                if not entry.room_id and slot.room:
                    r_clean = slot.room.strip().upper()
                    rid = room_map.get(r_clean) or room_map.get(r_clean.replace("-", "").replace(" ", ""))
                    if rid:
                        entry.room_id = rid

                # Update Faculty IDs
                chosen_facs = slot.faculty_list or (slot.faculty_candidates[:1] if slot.faculty_candidates else [])
                f_ids = resolve_fids(chosen_facs)
                if f_ids:
                    entry.faculty_ids = f_ids
                    flag_modified(entry, "faculty_ids")
                    updated_entries += 1
                    for fid in f_ids:
                        if (entry.id, fid) not in existing_fa:
                            db.add(TimetableEntryFaculty(
                                timetable_entry_id=entry.id,
                                faculty_id=fid,
                                role_type="LEAD"
                            ))
                            existing_fa.add((entry.id, fid))
                            new_fa_count += 1

        await db.commit()
        print(f"[Remediation] Updated foreign keys across {updated_entries} timetable entries; added {new_fa_count} TimetableEntryFaculty rows in PostgreSQL.")

        # Run integrity audit across current version
        v5_vid = 5
        audit = await TimetableService.check_data_integrity(db, version_id=v5_vid)
        print(f"[Remediation Audit Result for Version {v5_vid}]:")
        import json
        print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    asyncio.run(remediate())
