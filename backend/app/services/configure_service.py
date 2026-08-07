import io
import csv
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.exceptions import (
    ResourceNotFoundException,
    ConflictException,
    CapacityExceededException
)
from app.repositories.faculty_repository import FacultyRepository
from app.repositories.room_repository import RoomRepository
from app.repositories.subject_repository import SubjectRepository
from app.repositories.section_repository import SectionRepository
from app.models.section_subject import SectionSubject
from app.models.faculty import Faculty
from app.models.room import Room
from app.models.subject import Subject
from app.models.section import Section
from app.schemas.configure import (
    FacultyCreate, FacultyUpdate, FacultyResponse,
    RoomCreate, RoomUpdate, RoomResponse,
    SubjectCreate, SubjectUpdate, SubjectResponse,
    SectionCreate, SectionUpdate, SectionResponse,
    SectionSubjectMapRequest, SectionSubjectMapResponse,
    CSVImportResult
)


class ConfigureService:
    """Service layer orchestrating business logic and transaction boundaries for entity configuration."""
    def __init__(self, db: AsyncSession):
        self.db = db
        self.faculty_repo = FacultyRepository(db)
        self.room_repo = RoomRepository(db)
        self.subject_repo = SubjectRepository(db)
        self.section_repo = SectionRepository(db)

    # ---------------------------------------------------------
    # FACULTY SERVICES
    # ---------------------------------------------------------
    async def list_faculty(
        self,
        dept_id: Optional[int] = None,
        designation: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[FacultyResponse]:
        items = await self.faculty_repo.find_by_filters(dept_id=dept_id, designation=designation, search=search)
        if items:
            return [FacultyResponse.model_validate(f) for f in items]

        # Seed cache fallback if DB table is uninitialized
        from app.core.seed_cache import get_seed_data
        seed = get_seed_data()
        fallback = [FacultyResponse(**f) for f in seed.get("faculty", [])]
        if designation:
            fallback = [f for f in fallback if f.designation == designation]
        if search:
            fallback = [f for f in fallback if search.lower() in f.name.lower()]
        return fallback

    async def create_faculty(self, payload: FacultyCreate) -> FacultyResponse:
        if payload.employee_id:
            existing = await self.faculty_repo.get_by_employee_id(payload.employee_id)
            if existing:
                raise ConflictException(f"Faculty with Employee ID '{payload.employee_id}' already exists.")

        created = await self.faculty_repo.create(payload.model_dump())
        return FacultyResponse.model_validate(created)

    async def update_faculty(self, faculty_id: int, payload: FacultyUpdate) -> FacultyResponse:
        updated = await self.faculty_repo.update(faculty_id, payload.model_dump(exclude_unset=True))
        if not updated:
            raise ResourceNotFoundException("Faculty member", faculty_id)
        return FacultyResponse.model_validate(updated)

    async def delete_faculty(self, faculty_id: int) -> None:
        deleted = await self.faculty_repo.delete(faculty_id)
        if not deleted:
            raise ResourceNotFoundException("Faculty member", faculty_id)

    # ---------------------------------------------------------
    # ROOM & VENUE SERVICES
    # ---------------------------------------------------------
    async def list_rooms(
        self,
        room_type: Optional[str] = None,
        block: Optional[str] = None,
        gpu_capable: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[RoomResponse]:
        items = await self.room_repo.find_by_filters(room_type=room_type, block=block, gpu_capable=gpu_capable, search=search)
        if items:
            return [RoomResponse.model_validate(r) for r in items]

        # Seed cache fallback
        from app.core.seed_cache import get_seed_data
        seed = get_seed_data()
        fallback = [RoomResponse(**r) for r in seed.get("rooms", [])]
        if room_type:
            fallback = [r for r in fallback if r.room_type == room_type]
        if block:
            fallback = [r for r in fallback if r.block == block]
        if search:
            fallback = [r for r in fallback if search.lower() in r.code.lower()]
        return fallback

    async def create_room(self, payload: RoomCreate) -> RoomResponse:
        existing = await self.room_repo.get_by_code(payload.code)
        if existing:
            raise ConflictException(f"Room code '{payload.code}' already exists.")

        created = await self.room_repo.create(payload.model_dump())
        return RoomResponse.model_validate(created)

    async def update_room(self, room_id: int, payload: RoomUpdate) -> RoomResponse:
        updated = await self.room_repo.update(room_id, payload.model_dump(exclude_unset=True))
        if not updated:
            raise ResourceNotFoundException("Room venue", room_id)
        return RoomResponse.model_validate(updated)

    async def delete_room(self, room_id: int) -> None:
        deleted = await self.room_repo.delete(room_id)
        if not deleted:
            raise ResourceNotFoundException("Room venue", room_id)

    # ---------------------------------------------------------
    # CURRICULUM SUBJECT SERVICES
    # ---------------------------------------------------------
    async def list_subjects(
        self,
        slot_type: Optional[str] = None,
        is_lab: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[SubjectResponse]:
        items = await self.subject_repo.find_by_filters(slot_type=slot_type, is_lab=is_lab, search=search)
        if items:
            return [SubjectResponse.model_validate(s) for s in items]

        # Seed cache fallback
        from app.core.seed_cache import get_seed_data
        seed = get_seed_data()
        fallback = [SubjectResponse(**s) for s in seed.get("subjects", [])]
        if slot_type:
            fallback = [s for s in fallback if s.slot_type == slot_type]
        if search:
            fallback = [s for s in fallback if search.lower() in s.code.lower() or search.lower() in s.full_name.lower()]
        return fallback

    async def create_subject(self, payload: SubjectCreate) -> SubjectResponse:
        existing = await self.subject_repo.get_by_code(payload.code)
        if existing:
            raise ConflictException(f"Subject code '{payload.code}' already exists.")

        created = await self.subject_repo.create(payload.model_dump())
        return SubjectResponse.model_validate(created)

    async def update_subject(self, subject_id: int, payload: SubjectUpdate) -> SubjectResponse:
        updated = await self.subject_repo.update(subject_id, payload.model_dump(exclude_unset=True))
        if not updated:
            raise ResourceNotFoundException("Subject curriculum", subject_id)
        return SubjectResponse.model_validate(updated)

    async def delete_subject(self, subject_id: int) -> None:
        deleted = await self.subject_repo.delete(subject_id)
        if not deleted:
            raise ResourceNotFoundException("Subject curriculum", subject_id)

    # ---------------------------------------------------------
    # SECTION SERVICES
    # ---------------------------------------------------------
    async def list_sections(
        self,
        year_level: Optional[int] = None,
        branch_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[SectionResponse]:
        items = await self.section_repo.find_by_filters(year_level=year_level, branch_id=branch_id, search=search)
        if items:
            return [SectionResponse.model_validate(s) for s in items]

        # Seed cache fallback
        from app.core.seed_cache import get_seed_data
        seed = get_seed_data()
        fallback = [SectionResponse(**s) for s in seed.get("sections", [])]
        if year_level is not None:
            fallback = [s for s in fallback if s.year_level == year_level]
        if search:
            fallback = [s for s in fallback if search.lower() in s.name.lower()]
        return fallback

    async def create_section(self, payload: SectionCreate) -> SectionResponse:
        existing = await self.section_repo.get_by_name(payload.name)
        if existing:
            raise ConflictException(f"Section name '{payload.name}' already exists.")

        created = await self.section_repo.create(payload.model_dump())
        return SectionResponse.model_validate(created)

    async def update_section(self, section_id: int, payload: SectionUpdate) -> SectionResponse:
        updated = await self.section_repo.update(section_id, payload.model_dump(exclude_unset=True))
        if not updated:
            raise ResourceNotFoundException("Section", section_id)
        return SectionResponse.model_validate(updated)

    async def delete_section(self, section_id: int) -> None:
        deleted = await self.section_repo.delete(section_id)
        if not deleted:
            raise ResourceNotFoundException("Section", section_id)

    # ---------------------------------------------------------
    # SECTION-SUBJECT TEAM MAPPING
    # ---------------------------------------------------------
    async def batch_assign_section_subject(self, payload: SectionSubjectMapRequest) -> SectionSubjectMapResponse:
        stmt = select(SectionSubject).where(
            SectionSubject.section_id == payload.section_id,
            SectionSubject.subject_id != payload.subject_id
        )
        res = await self.db.execute(stmt)
        existing_maps = res.scalars().all()
        existing_slots = sum(m.lecture_slots_needed + m.tutorial_slots_needed + m.lab_slots_needed for m in existing_maps)
        new_slots = payload.lecture_slots_needed + payload.tutorial_slots_needed + payload.lab_slots_needed

        if (existing_slots + new_slots) > 40:
            raise CapacityExceededException(f"Total weekly slots ({existing_slots + new_slots}) exceeds maximum safe section capacity of 40 slots/week.")

        stmt = select(SectionSubject).where(
            SectionSubject.section_id == payload.section_id,
            SectionSubject.subject_id == payload.subject_id
        )
        res = await self.db.execute(stmt)
        sec_sub = res.scalar_one_or_none()

        if sec_sub:
            sec_sub.lecture_faculty_id = payload.lecture_faculty_id
            sec_sub.tutorial_faculty_id = payload.tutorial_faculty_id
            sec_sub.lab_lead_faculty_id = payload.lab_lead_faculty_id
            sec_sub.lab_co_faculty_ids = payload.lab_co_faculty_ids
            sec_sub.lecture_slots_needed = payload.lecture_slots_needed
            sec_sub.tutorial_slots_needed = payload.tutorial_slots_needed
            sec_sub.lab_slots_needed = payload.lab_slots_needed
        else:
            sec_sub = SectionSubject(**payload.model_dump())
            self.db.add(sec_sub)

        await self.db.commit()
        await self.db.refresh(sec_sub)
        total_slots = sec_sub.lecture_slots_needed + sec_sub.tutorial_slots_needed + sec_sub.lab_slots_needed
        return SectionSubjectMapResponse(
            id=sec_sub.id,
            section_id=sec_sub.section_id,
            subject_id=sec_sub.subject_id,
            lecture_faculty_id=sec_sub.lecture_faculty_id,
            tutorial_faculty_id=sec_sub.tutorial_faculty_id,
            lab_lead_faculty_id=sec_sub.lab_lead_faculty_id,
            lab_co_faculty_ids=sec_sub.lab_co_faculty_ids,
            lecture_slots_needed=sec_sub.lecture_slots_needed,
            tutorial_slots_needed=sec_sub.tutorial_slots_needed,
            lab_slots_needed=sec_sub.lab_slots_needed,
            total_slots=total_slots
        )

    # ---------------------------------------------------------
    # BULK CSV IMPORT
    # ---------------------------------------------------------
    async def import_csv_data(self, entity_type: str, content: bytes) -> CSVImportResult:
        decoded = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(decoded))
        imported_count = 0
        errors = []

        for row_idx, row in enumerate(reader, start=2):
            try:
                if entity_type == "faculty":
                    fac = Faculty(
                        name=row["name"].strip(),
                        employee_id=row.get("employee_id", "").strip() or None,
                        designation=row.get("designation", "Assistant Professor").strip(),
                        max_hours_per_week=int(row.get("max_hours_per_week", 16)),
                        max_daily_classes=int(row.get("max_daily_classes", 5)),
                        is_external=row.get("is_external", "").lower() in ["true", "1", "yes"]
                    )
                    self.db.add(fac)
                    imported_count += 1
                elif entity_type == "rooms":
                    room = Room(
                        code=row["code"].strip(),
                        room_type=row.get("room_type", "classroom").strip(),
                        capacity=int(row.get("capacity", 60)),
                        floor=row.get("floor", "6").strip(),
                        block=row.get("block", "U-Block").strip(),
                        gpu_capable=row.get("gpu_capable", "").lower() in ["true", "1", "yes"]
                    )
                    self.db.add(room)
                    imported_count += 1
                elif entity_type == "subjects":
                    sub = Subject(
                        code=row["code"].strip(),
                        full_name=row["full_name"].strip(),
                        lecture_hours=int(row.get("lecture_hours", 3)),
                        tutorial_hours=int(row.get("tutorial_hours", 0)),
                        lab_hours=int(row.get("lab_hours", 0)),
                        is_lab=row.get("is_lab", "").lower() in ["true", "1", "yes"],
                        gpu_required=row.get("gpu_required", "").lower() in ["true", "1", "yes"],
                        slot_type=row.get("slot_type", "L").strip()
                    )
                    self.db.add(sub)
                    imported_count += 1
                elif entity_type == "sections":
                    sec = Section(
                        name=row["name"].strip(),
                        label=row.get("label", "A").strip(),
                        year_level=int(row.get("year_level", 2)),
                        strength=int(row.get("strength", 60)),
                        branch_id=int(row.get("branch_id", 1)),
                        academic_year_id=int(row.get("academic_year_id", 1))
                    )
                    self.db.add(sec)
                    imported_count += 1
            except Exception as e:
                errors.append(f"Row {row_idx}: {str(e)}")

        await self.db.commit()
        return CSVImportResult(
            success=imported_count > 0,
            imported_count=imported_count,
            errors=errors,
            message=f"Successfully imported {imported_count} {entity_type} records from CSV."
        )
