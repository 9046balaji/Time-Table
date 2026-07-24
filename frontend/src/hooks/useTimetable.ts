'use client';

import { useState, useEffect, useCallback } from 'react';
import { timetableApi } from '@/lib/api';
import { SlotEntry } from '@/components/timetable/TimetableGrid';

export function useTimetable(versionId: number = 5, sectionName: string = 'II AIML-A') {
  const [entries, setEntries] = useState<SlotEntry[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTimetable = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await timetableApi.getTimetable(versionId, sectionName);
      const rawEntries = res.data?.entries || [];

      if (rawEntries.length > 0) {
        const mapped: SlotEntry[] = rawEntries.map((e: any) => ({
          id: String(e.id || `${sectionName}_${e.day}_${e.period}`),
          day: e.day,
          period: e.period,
          subjectCode: e.subject || 'DS',
          roomCode: e.room || '601',
          facultyName: Array.isArray(e.faculty) ? e.faculty.join(', ') : (e.faculty || 'Dr. Reddy'),
          subjectType: e.entry_type || 'L',
          hasClash: e.has_clash || false,
          clashReason: e.clash_reason,
        }));
        setEntries(mapped);
      } else {
        // Default initial baseline section entries if DB query returned 0 rows
        setEntries(generateDefaultSectionEntries(sectionName));
      }
    } catch (err) {
      console.warn('Backend timetable fetch failed, rendering baseline dataset', err);
      setEntries(generateDefaultSectionEntries(sectionName));
    } finally {
      setIsLoading(false);
    }
  }, [versionId, sectionName]);

  useEffect(() => {
    fetchTimetable();
  }, [fetchTimetable]);

  return { entries, setEntries, isLoading, error, refreshTimetable: fetchTimetable };
}

function generateDefaultSectionEntries(sectionName: string): SlotEntry[] {
  const entries: SlotEntry[] = [];
  const days: ("MON" | "TUE" | "WED" | "THU" | "FRI" | "SAT")[] = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];

  days.forEach((day) => {
    [1, 2, 3, 4, 5, 6, 7, 8].forEach((period) => {
      const isLab = period === 4 || period === 5;
      const isTutorial = period === 8;
      const isClashCell = day === 'WED' && period === 1 && sectionName === 'II AIML-E';

      entries.push({
        id: `${sectionName}_${day}_${period}`,
        day,
        period,
        subjectCode: isClashCell ? 'OOPS(P)' : isLab ? 'AI(P)' : isTutorial ? 'DS(T)' : 'DS',
        roomCode: isClashCell ? '606' : isLab ? '604' : '619',
        facultyName: 'Dr. S. Srikantha Reddy',
        subjectType: isLab ? 'P' : isTutorial ? 'T' : 'L',
        hasClash: isClashCell,
        clashReason: isClashCell ? 'Room 606 occupied by III CS in Period-1 WED' : undefined
      });
    });
  });

  return entries;
}
