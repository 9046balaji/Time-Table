import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.solver.incremental_validator import ScheduleIndexStore, IncrementalValidator, DragDropSwapRequest



class MockTimetableEntry:
    def __init__(self, entry_id: int, day: str, period: int, room: str, section: str, subject: str, faculty: list):
        self.id = entry_id
        self.day = day
        self.period = period
        self.room = room
        self.section = section
        self.subject = subject
        self.faculty = faculty


def test_schedule_index_store_construction():
    entries = [
        MockTimetableEntry(1, "MON", 1, "601", "II AIML-A", "DS", ["Dr. Reddy"]),
        MockTimetableEntry(2, "MON", 1, "604", "II AIML-B", "AI(P)", ["P. Girija", "K. Nikhitha"]),
    ]
    store = ScheduleIndexStore(entries)
    
    assert ("MON", 1, "601") in store.room_occupancy
    assert ("MON", 1, "604") in store.room_occupancy
    assert ("MON", 1, "DR. REDDY") in store.faculty_schedule
    assert ("MON", 1, "P. GIRIJA") in store.faculty_schedule



def test_incremental_validator_valid_swap():
    entries = [
        MockTimetableEntry(1, "MON", 1, "601", "II AIML-A", "DS", ["Dr. Reddy"]),
    ]
    store = ScheduleIndexStore(entries)
    validator = IncrementalValidator(store)

    req = DragDropSwapRequest(
        entry_id=1,
        source_day="MON",
        source_period=1,
        target_day="MON",
        target_period=2,
        target_room_code="602",
        faculty_names=["Dr. Reddy"]
    )
    result = validator.validate_swap(req)
    assert result.is_valid is True
    assert result.conflict_message is None


def test_incremental_validator_room_conflict():
    entries = [
        MockTimetableEntry(1, "MON", 1, "601", "II AIML-A", "DS", ["Dr. Reddy"]),
        MockTimetableEntry(2, "MON", 2, "601", "II AIML-B", "AI", ["P. Girija"]),
    ]
    store = ScheduleIndexStore(entries)
    validator = IncrementalValidator(store)

    # Try moving entry 1 into MON P2 Room 601 (which is occupied by II AIML-B)
    req = DragDropSwapRequest(
        entry_id=1,
        source_day="MON",
        source_period=1,
        target_day="MON",
        target_period=2,
        target_room_code="601",
        faculty_names=["Dr. Reddy"]
    )
    result = validator.validate_swap(req)
    assert result.is_valid is False
    assert result.clash_type == "ROOM"
    assert "Room 601 is already booked" in result.conflict_message
