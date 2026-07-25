import axios from 'axios';
import {
  Section,
  Faculty,
  Room,
  Subject,
  SectionSubjectMapRequest,
  ValidationReport,
  TimetableGenerationRequest,
  WizardGenerationResponse,
  DragDropSwapRequest,
  ValidationResult
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach Authorization Bearer token to mutating requests if available
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

export const timetableApi = {
  getSections: () => api.get<{ total: number; count: number; items: Section[] }>('/api/v1/sections'),
  getFaculty: () => api.get<Faculty[]>('/api/v1/configure/faculty'),
  getRooms: () => api.get<Room[]>('/api/v1/configure/rooms'),
  getSubjects: () => api.get<Subject[]>('/api/v1/configure/subjects'),
  
  createFaculty: (data: Partial<Faculty>) => api.post<Faculty>('/api/v1/configure/faculty', data),
  updateFaculty: (id: number, data: Partial<Faculty>) => api.put<Faculty>(`/api/v1/configure/faculty/${id}`, data),
  deleteFaculty: (id: number) => api.delete(`/api/v1/configure/faculty/${id}`),

  createRoom: (data: Partial<Room>) => api.post<Room>('/api/v1/configure/rooms', data),
  updateRoom: (id: number, data: Partial<Room>) => api.put<Room>(`/api/v1/configure/rooms/${id}`, data),
  deleteRoom: (id: number) => api.delete(`/api/v1/configure/rooms/${id}`),

  createSubject: (data: Partial<Subject>) => api.post<Subject>('/api/v1/configure/subjects', data),
  updateSubject: (id: number, data: Partial<Subject>) => api.put<Subject>(`/api/v1/configure/subjects/${id}`, data),
  deleteSubject: (id: number) => api.delete(`/api/v1/configure/subjects/${id}`),

  batchAssignSectionSubject: (data: SectionSubjectMapRequest) =>
    api.post('/api/v1/configure/section-subjects/batch-assign', data),

  importCSV: (entityType: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/api/v1/configure/import-csv?entity_type=${entityType}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  getVersions: () => api.get<any[]>('/api/v1/timetable/versions'),
  getTimetable: (versionId: number = 5, sectionName?: string) =>
    api.get(`/api/v1/timetable/version/${versionId}`, { params: { section_name: sectionName } }),
  validate: (versionId: number = 5) => api.get<ValidationReport>(`/api/v1/validate/${versionId}`),
  validateSlotMove: (req: DragDropSwapRequest) =>
    api.post<ValidationResult>('/api/v1/timetable/validate-move', req),
  updateSlotAssignment: (entryId: string | number, newTimeSlotId: number, newRoomId?: number) =>
    api.patch(`/api/v1/timetable/entries/${entryId}`, { new_time_slot_id: newTimeSlotId, new_room_id: newRoomId }),
  importExcel: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/v1/import/excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  generateFromWizard: (payload: TimetableGenerationRequest) =>
    api.post<WizardGenerationResponse>('/api/v1/solve/generate-from-wizard', payload),
  exportExcel: (versionId: number = 5) =>
    api.post(`/api/v1/export/excel?version_id=${versionId}`, {}, { responseType: 'blob' }),
  getCohortGroups: () =>
    api.get<any[]>('/api/v1/export/excel/cohorts'),
  exportCohortExcel: (cohortKey: string, versionId: number = 5) =>
    api.post(`/api/v1/export/excel/cohort/${cohortKey}?version_id=${versionId}`, {}, { responseType: 'blob' }),
  exportMinorsHonorsExcel: (versionId: number = 5) =>
    api.post(`/api/v1/export/excel/minors-honors?version_id=${versionId}`, {}, { responseType: 'blob' }),
  exportSectionPdfs: (versionId: number = 5) =>
    api.post(`/api/v1/export/pdf/sections?version_id=${versionId}`, {}, { responseType: 'blob' }),
  exportFacultyPdfs: (versionId: number = 5) =>
    api.post(`/api/v1/export/pdf/faculty?version_id=${versionId}`, {}, { responseType: 'blob' }),
  exportFacultyPdf: (versionId: number = 5) =>
    api.post(`/api/v1/export/pdf/faculty?version_id=${versionId}`, {}, { responseType: 'blob' }),
  getFacultyTimetable: (facultyId: number, versionId: number = 5) =>
    api.get(`/api/v1/timetable/faculty/${facultyId}`, { params: { version_id: versionId } }),
  exportSingleFacultyPdf: (facultyId: number, versionId: number = 5) =>
    api.get(`/api/v1/export/pdf/faculty/${facultyId}`, { params: { version_id: versionId }, responseType: 'blob' }),
  syncSmartClass: () => api.post('/api/v1/timetable/sync-master'),
};
