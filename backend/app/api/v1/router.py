from fastapi import APIRouter
from app.api.v1.sections import router as sections_router
from app.api.v1.faculty import router as faculty_router
from app.api.v1.rooms import router as rooms_router
from app.api.v1.timetable import router as timetable_router
from app.api.v1.validate import router as validate_router
from app.api.v1.import_excel import router as import_excel_router
from app.api.v1.solve import router as solve_router
from app.api.v1.wizard_solve import router as wizard_solve_router
from app.api.v1.wizard_defaults import router as wizard_defaults_router
from app.api.v1.export import router as export_router, sync_master_timetable_to_smartclass
from app.api.v1.configure import router as configure_router
from app.api.v1.testing import router as testing_router
from app.api.v1.telemetry import router as telemetry_router

api_v1_router = APIRouter()

api_v1_router.include_router(sections_router, prefix="/sections", tags=["Sections"])
api_v1_router.include_router(faculty_router, prefix="/faculty", tags=["Faculty"])
api_v1_router.include_router(rooms_router, prefix="/rooms", tags=["Rooms"])
api_v1_router.include_router(configure_router, prefix="/configure", tags=["Master Configuration"])
api_v1_router.include_router(wizard_defaults_router, prefix="/configure", tags=["Wizard Configuration"])
api_v1_router.include_router(timetable_router, prefix="/timetable", tags=["Timetable"])
api_v1_router.include_router(validate_router, prefix="/validate", tags=["Validation"])
api_v1_router.include_router(import_excel_router, prefix="/import/excel", tags=["Import"])
api_v1_router.include_router(solve_router, prefix="/solve", tags=["Solver"])
api_v1_router.include_router(wizard_solve_router, prefix="/solve", tags=["Wizard Solver"])
api_v1_router.include_router(export_router, prefix="/export", tags=["Export"])
api_v1_router.include_router(testing_router, prefix="/testing", tags=["Testing Lab"])
api_v1_router.include_router(telemetry_router, prefix="/telemetry", tags=["Telemetry & Health"])
api_v1_router.add_api_route("/timetable/sync-master", sync_master_timetable_to_smartclass, methods=["POST"], tags=["SmartClass Sync"])


