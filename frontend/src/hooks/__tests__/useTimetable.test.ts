import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { useTimetable } from '../useTimetable';
import { timetableApi } from '@/lib/api';

vi.mock('@/lib/api', () => ({
  timetableApi: {
    getTimetable: vi.fn(),
  },
}));

describe('useTimetable Hook', () => {
  it('returns mapped timetable entries from API', async () => {
    const mockResponse = {
      data: {
        entries: [
          { id: 101, day: 'MON', period: 1, subject: 'DS', room: '601', faculty: ['Dr. Reddy'], entry_type: 'L' },
        ],
      },
    };
    (timetableApi.getTimetable as any).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useTimetable(5, 'II AIML-A'));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.entries.length).toBeGreaterThan(0);
    expect(result.current.entries[0].subjectCode).toBe('DS');
  });

  it('renders default baseline entries if API returns empty array', async () => {
    (timetableApi.getTimetable as any).mockResolvedValue({ data: { entries: [] } });

    const { result } = renderHook(() => useTimetable(5, 'II AIML-A'));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.entries.length).toBe(48); // 6 days * 8 periods
  });
});
