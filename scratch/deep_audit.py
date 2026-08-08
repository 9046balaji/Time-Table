import json
import os
import glob
import openpyxl

def detailed_audit():
    with open('data/seed/original_v5_sections.json', 'r', encoding='utf-8') as f:
        v5_sections = json.load(f)
    print(f"V5 Sections count: {len(v5_sections)}")

    with open('data/seed/original_v5_faculty.json', 'r', encoding='utf-8') as f:
        v5_faculty = json.load(f)
    print(f"V5 Faculty count: {len(v5_faculty)}")

    with open('data/seed/original_v5_rooms.json', 'r', encoding='utf-8') as f:
        v5_rooms = json.load(f)
    print(f"V5 Rooms count: {len(v5_rooms)}")

    with open('data/seed/original_v5_subjects.json', 'r', encoding='utf-8') as f:
        v5_subjects = json.load(f)
    print(f"V5 Subjects count: {len(v5_subjects)}")

    with open('data/seed/original_v5_all_entries.json', 'r', encoding='utf-8') as f:
        v5_entries = json.load(f)
    print(f"V5 Total Timetable Entries: {len(v5_entries)}")

    # Print samples
    print("\n--- SAMPLE SECTION ---")
    if isinstance(v5_sections, dict):
        first_k = next(iter(v5_sections))
        print("Key:", first_k, "Value:", v5_sections[first_k])
    elif isinstance(v5_sections, list):
        print(v5_sections[0])

    print("\n--- SAMPLE FACULTY ---")
    if isinstance(v5_faculty, dict):
        first_k = next(iter(v5_faculty))
        print("Key:", first_k, "Value:", v5_faculty[first_k])

    print("\n--- SAMPLE ROOM ---")
    if isinstance(v5_rooms, dict):
        first_k = next(iter(v5_rooms))
        print("Key:", first_k, "Value:", v5_rooms[first_k])

    print("\n--- SAMPLE ENTRY ---")
    if isinstance(v5_entries, list):
        print(v5_entries[0])

    # Inspect SeedService
    with open('backend/app/services/seed_service.py', 'r', encoding='utf-8') as f:
        seed_code = f.read()
    print(f"\nSeedService code length: {len(seed_code)} chars")

if __name__ == '__main__':
    detailed_audit()
