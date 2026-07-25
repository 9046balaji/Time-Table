import { create } from 'zustand';

export type ScheduleViewMode = 'matrix' | 'stack' | 'faculty' | 'wizard';

interface AppState {
  // Navigation & Selection state
  selectedSection: string;
  selectedCohort: string;
  selectedVersionId: number;
  viewMode: ScheduleViewMode;
  selectedFacultyId: string | null;

  // Actions
  setSelectedSection: (section: string) => void;
  setSelectedCohort: (cohort: string) => void;
  setSelectedVersionId: (versionId: number) => void;
  setViewMode: (mode: ScheduleViewMode) => void;
  setSelectedFacultyId: (facultyId: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  selectedSection: 'II AIML-A',
  selectedCohort: 'II_AIML',
  selectedVersionId: 5,
  viewMode: 'matrix',
  selectedFacultyId: null,

  setSelectedSection: (section) => set({ selectedSection: section }),
  setSelectedCohort: (cohort) => set({ selectedCohort: cohort }),
  setSelectedVersionId: (versionId) => set({ selectedVersionId: versionId }),
  setViewMode: (mode) => set({ viewMode: mode }),
  setSelectedFacultyId: (facultyId) => set({ selectedFacultyId: facultyId }),
}));
