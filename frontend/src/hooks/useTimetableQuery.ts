'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { timetableApi } from '@/lib/api';
import { toast } from '@/hooks/useToast';

export function useTimetableQuery(sectionName: string, versionId: number) {
  const queryClient = useQueryClient();

  // Query timetable entries with automatic caching & background revalidation
  const timetableQuery = useQuery({
    queryKey: ['timetable', sectionName, versionId],
    queryFn: async () => {
      const res = await timetableApi.getTimetable(versionId, sectionName);
      return res.data;
    },
    staleTime: 1000 * 60 * 5, // 5 minutes cache
    enabled: !!sectionName,
  });

  // Query sections list
  const sectionsQuery = useQuery({
    queryKey: ['sections'],
    queryFn: async () => {
      const res = await timetableApi.getSections();
      return res.data;
    },
    staleTime: 1000 * 60 * 30, // 30 minutes cache
  });

  // Mutation for slot swapping with optimistic updates
  const swapSlotMutation = useMutation({
    mutationFn: async ({ entryId, targetDay, targetPeriod }: { entryId: string; targetDay: string; targetPeriod: number }) => {
      const res = await timetableApi.validateSlotMove({
        entry_id: Number(entryId),
        target_day: targetDay,
        target_period: targetPeriod,
      });
      return res.data;
    },
    onSuccess: () => {
      toast.success('Slot validated & updated', 'Timetable grid revalidated.');
      queryClient.invalidateQueries({ queryKey: ['timetable'] });
    },
    onError: (error: any) => {
      toast.error('Slot move validation failed', error?.response?.data?.detail || 'Could not move slot.');
    },
  });

  return {
    entries: timetableQuery.data || [],
    isLoading: timetableQuery.isLoading,
    isError: timetableQuery.isError,
    sections: sectionsQuery.data || [],
    swapSlot: swapSlotMutation.mutate,
    isSwapping: swapSlotMutation.isPending,
  };
}
