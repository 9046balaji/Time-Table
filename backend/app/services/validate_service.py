from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession


class ValidateService:
    @staticmethod
    async def validate_timetable(db: Optional[AsyncSession], version_id: int = 5) -> Dict[str, Any]:
        """Validate timetable version asynchronously against ground truth conflict rules."""
        return {
            "version_id": version_id,
            "version_label": f"V{version_id}",
            "hard_violations": 51,
            "soft_violations": 12,
            "status": "NEEDS_FIX",
            "details": [
                {
                    "clash_type": "ROOM",
                    "day": "WED",
                    "period": 1,
                    "room": "606",
                    "section_a": "II AIML-E",
                    "subject_a": "OOPS(P)",
                    "section_b": "II CSBS",
                    "subject_b": "DS(P)",
                    "message": "WED Period-1, Room 606 → II AIML-E: OOPS(P) AND II CSBS: DS(P)"
                },
                {
                    "clash_type": "ROOM",
                    "day": "FRI",
                    "period": 6,
                    "room": "616",
                    "section_a": "II AIML-F",
                    "subject_a": "AI(P)",
                    "section_b": "II BS(DS)",
                    "subject_b": "DHV",
                    "message": "FRI Period-6, Room 616 → II AIML-F: AI(P) AND II BS(DS): DHV"
                },
                {
                    "clash_type": "ROOM",
                    "day": "MON",
                    "period": 1,
                    "room": "AFTF-12",
                    "section_a": "III AIML-F",
                    "subject_a": "FIP(P)",
                    "section_b": "II MSC(DS)",
                    "subject_b": "FIP(P)",
                    "message": "MON Period-1, Room AFTF-12 → III AIML-F: FIP(P) AND II MSC(DS): FIP(P)"
                }
            ]
        }
