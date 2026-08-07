import io
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.export_service import ExportService

from fastapi import APIRouter, Depends, Query

router = APIRouter()


@router.get("/excel/cohorts")
async def list_cohort_groups():
    from parser.excel_exporter import COHORT_GROUPS
    return [
        {"key": k, "label": v["label"], "sections_count": len(v["sections"]), "sections": v["sections"]}
        for k, v in COHORT_GROUPS.items()
    ]


@router.post("/excel/cohort/{cohort_key}")
async def export_cohort_excel_timetable(cohort_key: str, version_id: int = Query(5), db: AsyncSession = Depends(get_db)):
    content = await ExportService.generate_cohort_excel_export(db, cohort_key=cohort_key, version_id=version_id)
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=VFSTR_V{version_id}_Cohort_{cohort_key}_Timetable.xlsx"}
    )


@router.post("/excel/minors-honors")
async def export_minors_honors_excel(version_id: int = Query(5), db: AsyncSession = Depends(get_db)):
    content = await ExportService.generate_minors_honors_excel_export(db, version_id=version_id)
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=VFSTR_V{version_id}_Minors_Honors_Master.xlsx"}
    )


@router.post("/excel")
async def export_excel_timetable(version_id: int = Query(5), db: AsyncSession = Depends(get_db)):
    content = await ExportService.generate_excel_export(db, version_id=version_id)
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=ACSE_V{version_id}_Timetable.xlsx"}
    )


@router.post("/pdf")
@router.post("/pdf/sections")
async def export_sections_pdf(version_id: int = Query(5), db: AsyncSession = Depends(get_db)):
    pdf_bytes = await ExportService.generate_section_pdfs(db, version_id=version_id)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=VFSTR_V{version_id}_Section_Timetables.pdf"}
    )


@router.post("/pdf/faculty")
async def export_faculty_pdf(version_id: int = Query(5), db: AsyncSession = Depends(get_db)):
    pdf_bytes = await ExportService.generate_faculty_pdfs(db, version_id=version_id)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=VFSTR_V{version_id}_Faculty_Weekly_Schedules.pdf"}
    )


@router.get("/pdf/faculty/{faculty_id}")
async def export_single_faculty_pdf(faculty_id: int, version_id: int = Query(5), db: AsyncSession = Depends(get_db)):
    pdf_bytes = await ExportService.generate_single_faculty_pdf(db, faculty_id=faculty_id, version_id=version_id)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=VFSTR_V{version_id}_Faculty_{faculty_id}_Schedule.pdf"}
    )


@router.post("/sync-master")
async def sync_master_timetable_to_smartclass():
    return await ExportService.sync_smartclass_nodes()


@router.get("/json")
async def export_json_timetable(version_id: int = Query(5), db: AsyncSession = Depends(get_db)):
    """Export complete raw JSON structure of timetable entries for API integrations."""
    from app.services.timetable_service import TimetableService
    return await TimetableService.get_version_timetable(db, version_id=version_id, section_name="ALL")


@router.get("/room-utilization")
async def export_room_utilization_report(version_id: int = Query(5), db: AsyncSession = Depends(get_db)):
    """Generate room utilization matrix across all 35 rooms and 48 slots/week."""
    content = await ExportService.generate_room_utilization_excel(db, version_id=version_id)
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=VFSTR_V{version_id}_Room_Utilization_Report.xlsx"}
    )


@router.get("/ical/faculty/{faculty_id}")
async def export_faculty_ical(faculty_id: int, version_id: int = Query(5), db: AsyncSession = Depends(get_db)):
    """Generate iCal (.ics) calendar file for faculty member schedule sync."""
    ics_text = await ExportService.generate_ical_export(db, faculty_id=faculty_id, version_id=version_id)
    return StreamingResponse(
        io.BytesIO(ics_text.encode("utf-8")),
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=Faculty_{faculty_id}_Schedule.ics"}
    )
