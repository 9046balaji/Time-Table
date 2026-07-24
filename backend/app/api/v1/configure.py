import io
import csv
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from app.core.database import get_db
from app.models.faculty import Faculty
from app.models.room import Room
from app.models.subject import Subject
from app.models.section import Section
from app.models.section_subject import SectionSubject

from app.schemas.configure import (
    FacultyCreate, FacultyUpdate, FacultyResponse,
    RoomCreate, RoomUpdate, RoomResponse,
    SubjectCreate, SubjectUpdate, SubjectResponse,
    SectionCreate, SectionUpdate, SectionResponse,
    SectionSubjectMapRequest, SectionSubjectMapResponse,
    CSVImportResult
)

router = APIRouter()

# ---------------------------------------------------------
# FACULTY CRUD ENDPOINTS
# ---------------------------------------------------------
@router.get("/faculty", response_model=List[FacultyResponse])
async def list_faculty(
    dept_id: Optional[int] = Query(None),
    designation: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(Faculty)
    if dept_id:
        query = query.where(Faculty.dept_id == dept_id)
    if designation:
        query = query.where(Faculty.designation == designation)
    if search:
        query = query.where(Faculty.name.ilike(f"%{search}%"))

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/faculty", response_model=FacultyResponse, status_code=status.HTTP_201_CREATED)
async def create_faculty(payload: FacultyCreate, db: AsyncSession = Depends(get_db)):
    faculty = Faculty(**payload.model_dump())
    db.add(faculty)
    await db.commit()
    await db.refresh(faculty)
    return faculty


@router.put("/faculty/{faculty_id}", response_model=FacultyResponse)
async def update_faculty(faculty_id: int, payload: FacultyUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Faculty).where(Faculty.id == faculty_id))
    faculty = result.scalar_one_or_none()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty member not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(faculty, field, value)

    await db.commit()
    await db.refresh(faculty)
    return faculty


@router.delete("/faculty/{faculty_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_faculty(faculty_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Faculty).where(Faculty.id == faculty_id))
    faculty = result.scalar_one_or_none()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty member not found")

    await db.delete(faculty)
    await db.commit()
    return None


# ---------------------------------------------------------
# ROOMS CRUD ENDPOINTS
# ---------------------------------------------------------
@router.get("/rooms", response_model=List[RoomResponse])
async def list_rooms(
    room_type: Optional[str] = Query(None),
    block: Optional[str] = Query(None),
    gpu_capable: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(Room)
    if room_type:
        query = query.where(Room.room_type == room_type)
    if block:
        query = query.where(Room.block == block)
    if gpu_capable is not None:
        query = query.where(Room.gpu_capable == gpu_capable)
    if search:
        query = query.where(Room.code.ilike(f"%{search}%"))

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/rooms", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(payload: RoomCreate, db: AsyncSession = Depends(get_db)):
    room = Room(**payload.model_dump())
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room


@router.put("/rooms/{room_id}", response_model=RoomResponse)
async def update_room(room_id: int, payload: RoomUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Room).where(Room.id == room_id))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(room, field, value)

    await db.commit()
    await db.refresh(room)
    return room


@router.delete("/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(room_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Room).where(Room.id == room_id))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    await db.delete(room)
    await db.commit()
    return None


# ---------------------------------------------------------
# SUBJECTS CRUD ENDPOINTS
# ---------------------------------------------------------
@router.get("/subjects", response_model=List[SubjectResponse])
async def list_subjects(
    slot_type: Optional[str] = Query(None),
    is_lab: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(Subject)
    if slot_type:
        query = query.where(Subject.slot_type == slot_type)
    if is_lab is not None:
        query = query.where(Subject.is_lab == is_lab)
    if search:
        query = query.where((Subject.code.ilike(f"%{search}%")) | (Subject.full_name.ilike(f"%{search}%")))

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/subjects", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(payload: SubjectCreate, db: AsyncSession = Depends(get_db)):
    subject = Subject(**payload.model_dump())
    db.add(subject)
    await db.commit()
    await db.refresh(subject)
    return subject


@router.put("/subjects/{subject_id}", response_model=SubjectResponse)
async def update_subject(subject_id: int, payload: SubjectUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subject).where(Subject.id == subject_id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(subject, field, value)

    await db.commit()
    await db.refresh(subject)
    return subject


@router.delete("/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject(subject_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subject).where(Subject.id == subject_id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    await db.delete(subject)
    await db.commit()
    return None


# ---------------------------------------------------------
# SECTIONS CRUD ENDPOINTS
# ---------------------------------------------------------
@router.get("/sections", response_model=List[SectionResponse])
async def list_sections(
    year_level: Optional[int] = Query(None),
    branch_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(Section)
    if year_level:
        query = query.where(Section.year_level == year_level)
    if branch_id:
        query = query.where(Section.branch_id == branch_id)
    if search:
        query = query.where(Section.name.ilike(f"%{search}%"))

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/sections", response_model=SectionResponse, status_code=status.HTTP_201_CREATED)
async def create_section(payload: SectionCreate, db: AsyncSession = Depends(get_db)):
    section = Section(**payload.model_dump())
    db.add(section)
    await db.commit()
    await db.refresh(section)
    return section


@router.put("/sections/{section_id}", response_model=SectionResponse)
async def update_section(section_id: int, payload: SectionUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Section).where(Section.id == section_id))
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(section, field, value)

    await db.commit()
    await db.refresh(section)
    return section


# ---------------------------------------------------------
# SECTION-SUBJECT BATCH TEAM MAPPING
# ---------------------------------------------------------
@router.post("/section-subjects/batch-assign", response_model=SectionSubjectMapResponse)
async def batch_assign_section_subject(payload: SectionSubjectMapRequest, db: AsyncSession = Depends(get_db)):
    # Verify total weekly slots per section protection (must be <= 40 slots/week)
    stmt = select(SectionSubject).where(
        SectionSubject.section_id == payload.section_id,
        SectionSubject.subject_id != payload.subject_id
    )
    res = await db.execute(stmt)
    existing_maps = res.scalars().all()

    existing_slots = sum(
        m.lecture_slots_needed + m.tutorial_slots_needed + m.lab_slots_needed
        for m in existing_maps
    )
    new_slots = payload.lecture_slots_needed + payload.tutorial_slots_needed + payload.lab_slots_needed

    if (existing_slots + new_slots) > 40:
        raise HTTPException(
            status_code=400,
            detail=f"Total weekly slots ({existing_slots + new_slots}) exceeds maximum safe section capacity of 40 slots/week."
        )

    # Upsert section subject map
    stmt = select(SectionSubject).where(
        SectionSubject.section_id == payload.section_id,
        SectionSubject.subject_id == payload.subject_id
    )
    res = await db.execute(stmt)
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
        db.add(sec_sub)

    await db.commit()
    await db.refresh(sec_sub)

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
# BULK CSV DATA INGESTION
# ---------------------------------------------------------
@router.post("/import-csv", response_model=CSVImportResult)
async def import_csv_data(
    entity_type: str = Query(..., description="faculty | rooms | subjects | sections"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    content = await file.read()
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
                db.add(fac)
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
                db.add(room)
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
                db.add(sub)
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
                db.add(sec)
                imported_count += 1

        except Exception as e:
            errors.append(f"Row {row_idx}: {str(e)}")

    await db.commit()
    return CSVImportResult(
        success=imported_count > 0,
        imported_count=imported_count,
        errors=errors,
        message=f"Successfully imported {imported_count} {entity_type} records from CSV."
    )
