import io
import csv
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.services.configure_service import ConfigureService
from app.schemas.configure import (
    FacultyCreate, FacultyUpdate, FacultyResponse,
    RoomCreate, RoomUpdate, RoomResponse,
    SubjectCreate, SubjectUpdate, SubjectResponse,
    SectionCreate, SectionUpdate, SectionResponse,
    SectionSubjectMapRequest, SectionSubjectMapResponse,
    CSVImportResult
)

router = APIRouter()


def get_configure_service(db: AsyncSession = Depends(get_db)) -> ConfigureService:
    """Dependency injection helper providing ConfigureService instance."""
    return ConfigureService(db)


# ---------------------------------------------------------
# FACULTY ENDPOINTS
# ---------------------------------------------------------
@router.get(
    "/faculty",
    response_model=List[FacultyResponse],
    summary="List all faculty instructors",
    description="Retrieve list of faculty members with optional filtering by department ID, designation rank, or name search query."
)
async def list_faculty(
    dept_id: Optional[int] = Query(None, description="Filter by department ID"),
    designation: Optional[str] = Query(None, description="Filter by designation rank"),
    search: Optional[str] = Query(None, description="Filter by instructor name"),
    service: ConfigureService = Depends(get_configure_service)
):
    return await service.list_faculty(dept_id=dept_id, designation=designation, search=search)


@router.post(
    "/faculty",
    response_model=FacultyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new faculty instructor",
    description="Register a new faculty member with institutional employee ID, rank, weekly workload hour limit, and availability."
)
async def create_faculty(
    payload: FacultyCreate,
    service: ConfigureService = Depends(get_configure_service)
):
    return await service.create_faculty(payload)


@router.put(
    "/faculty/{faculty_id}",
    response_model=FacultyResponse,
    summary="Update faculty instructor specs",
    description="Modify workload caps, daily class limits, contact details, or designation rank for a faculty member."
)
async def update_faculty(
    faculty_id: int,
    payload: FacultyUpdate,
    service: ConfigureService = Depends(get_configure_service)
):
    return await service.update_faculty(faculty_id, payload)


@router.delete(
    "/faculty/{faculty_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a faculty instructor",
    description="Delete a faculty member from master records."
)
async def delete_faculty(
    faculty_id: int,
    service: ConfigureService = Depends(get_configure_service)
):
    await service.delete_faculty(faculty_id)
    return None


# ---------------------------------------------------------
# ROOM & VENUE ENDPOINTS
# ---------------------------------------------------------
@router.get(
    "/rooms",
    response_model=List[RoomResponse],
    summary="List all classrooms & computer labs",
    description="Retrieve venue list filtered by room type (classroom/computer_lab/gpu_lab), block, or GPU capability."
)
async def list_rooms(
    room_type: Optional[str] = Query(None, description="Filter by room type"),
    block: Optional[str] = Query(None, description="Filter by building block"),
    gpu_capable: Optional[bool] = Query(None, description="Filter by GPU compute capability"),
    search: Optional[str] = Query(None, description="Search by room code"),
    service: ConfigureService = Depends(get_configure_service)
):
    return await service.list_rooms(room_type=room_type, block=block, gpu_capable=gpu_capable, search=search)


@router.post(
    "/rooms",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new classroom or computer lab venue",
    description="Register a new venue code with student seating capacity, building block, and GPU hardware tags."
)
async def create_room(
    payload: RoomCreate,
    service: ConfigureService = Depends(get_configure_service)
):
    return await service.create_room(payload)


@router.put(
    "/rooms/{room_id}",
    response_model=RoomResponse,
    summary="Update venue specs",
    description="Modify room capacity, type, floor level, or GPU compute flags."
)
async def update_room(
    room_id: int,
    payload: RoomUpdate,
    service: ConfigureService = Depends(get_configure_service)
):
    return await service.update_room(room_id, payload)


@router.delete(
    "/rooms/{room_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a venue",
    description="Delete a venue from master room records."
)
async def delete_room(
    room_id: int,
    service: ConfigureService = Depends(get_configure_service)
):
    await service.delete_room(room_id)
    return None


# ---------------------------------------------------------
# CURRICULUM SUBJECT ENDPOINTS
# ---------------------------------------------------------
@router.get(
    "/subjects",
    response_model=List[SubjectResponse],
    summary="List curriculum courses",
    description="Retrieve subjects filtered by slot type (L/T/P), lab requirement, or course name search query."
)
async def list_subjects(
    slot_type: Optional[str] = Query(None, description="Filter by slot type (L/T/P)"),
    is_lab: Optional[bool] = Query(None, description="Filter by practical lab requirement"),
    search: Optional[str] = Query(None, description="Search course code or full title"),
    service: ConfigureService = Depends(get_configure_service)
):
    return await service.list_subjects(slot_type=slot_type, is_lab=is_lab, search=search)


@router.post(
    "/subjects",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new course curriculum subject",
    description="Register a new subject with L/T/P weekly credit hours, consecutive period requirements, and GPU flags."
)
async def create_subject(
    payload: SubjectCreate,
    service: ConfigureService = Depends(get_configure_service)
):
    return await service.create_subject(payload)


@router.put(
    "/subjects/{subject_id}",
    response_model=SubjectResponse,
    summary="Update course specs",
    description="Modify L/T/P credit hours or lab rules for a subject."
)
async def update_subject(
    subject_id: int,
    payload: SubjectUpdate,
    service: ConfigureService = Depends(get_configure_service)
):
    return await service.update_subject(subject_id, payload)


@router.delete(
    "/subjects/{subject_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a course",
    description="Delete a subject from curriculum records."
)
async def delete_subject(
    subject_id: int,
    service: ConfigureService = Depends(get_configure_service)
):
    await service.delete_subject(subject_id)
    return None


# ---------------------------------------------------------
# SECTION ENDPOINTS
# ---------------------------------------------------------
@router.get(
    "/sections",
    response_model=List[SectionResponse],
    summary="List student sections",
    description="Retrieve list of student sections filtered by year level (II/III/IV Year) or branch ID."
)
async def list_sections(
    year_level: Optional[int] = Query(None, description="Filter by year level (2, 3, 4)"),
    branch_id: Optional[int] = Query(None, description="Filter by branch ID"),
    search: Optional[str] = Query(None, description="Search by section name"),
    service: ConfigureService = Depends(get_configure_service)
):
    return await service.list_sections(year_level=year_level, branch_id=branch_id, search=search)


@router.post(
    "/sections",
    response_model=SectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new student section",
    description="Register a new section with student strength and academic year mapping."
)
async def create_section(
    payload: SectionCreate,
    service: ConfigureService = Depends(get_configure_service)
):
    return await service.create_section(payload)


@router.put(
    "/sections/{section_id}",
    response_model=SectionResponse,
    summary="Update section specs",
    description="Modify section student strength, year level, or active status."
)
async def update_section(
    section_id: int,
    payload: SectionUpdate,
    service: ConfigureService = Depends(get_configure_service)
):
    return await service.update_section(section_id, payload)


@router.delete(
    "/sections/{section_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a section",
    description="Delete a section from records."
)
async def delete_section(
    section_id: int,
    service: ConfigureService = Depends(get_configure_service)
):
    await service.delete_section(section_id)
    return None


@router.post(
    "/import-csv",
    response_model=CSVImportResult,
    summary="Bulk import entities from CSV file",
    description="Import faculty, rooms, subjects, or sections from uploaded CSV file."
)
async def import_csv_data(
    entity_type: str = Query(..., description="faculty | rooms | subjects | sections"),
    file: UploadFile = File(...),
    service: ConfigureService = Depends(get_configure_service)
):
    content = await file.read()
    return await service.import_csv_data(entity_type=entity_type, content=content)

