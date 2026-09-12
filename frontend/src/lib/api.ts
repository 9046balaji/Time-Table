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
  ValidationMoveResult,
  TimetableVersionInfo,
  CohortGroupInfo,
  WizardDefaultsResponse
} from './types';

export function getApiBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_API_URL && process.env.NEXT_PUBLIC_API_URL.startsWith('http')) {
    return process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, '');
  }
  if (typeof window !== 'undefined') {
    return window.location.origin;
  }
  return 'http://localhost:8000';
}

export function getWsBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_WS_URL && process.env.NEXT_PUBLIC_WS_URL.startsWith('ws')) {
    return process.env.NEXT_PUBLIC_WS_URL.replace(/\/$/, '');
  }
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}`;
  }
  return 'ws://localhost:8000';
}

const api = axios.create({
  headers: {
    'Content-Type': 'application/json',
  },
});

// Dynamic Base URL Interceptor
api.interceptors.request.use((config) => {
  if (!config.baseURL || config.baseURL === 'http://localhost:8000') {
    config.baseURL = getApiBaseUrl();
  }
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});



// In-memory Request Cache & Promise Deduplication Layer (30s TTL)
interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

const cacheStore = new Map<string, CacheEntry<unknown>>();
const pendingRequests = new Map<string, Promise<unknown>>();
const DEFAULT_TTL_MS = 30000;

export function invalidateApiCache(prefix?: string): void {
  if (!prefix) {
    cacheStore.clear();
    return;
  }
  for (const key of cacheStore.keys()) {
    if (key.startsWith(prefix)) {
      cacheStore.delete(key);
    }
  }
}

async function cachedGet<T>(url: string, ttlMs: number = DEFAULT_TTL_MS): Promise<{ data: T }> {
  const now = Date.now();
  const cached = cacheStore.get(url);
  if (cached && now - cached.timestamp < ttlMs) {
    return { data: cached.data as T };
  }

  if (pendingRequests.has(url)) {
    return pendingRequests.get(url) as Promise<{ data: T }>;
  }

  const promise = api.get<T>(url).then((res) => {
    cacheStore.set(url, { data: res.data, timestamp: Date.now() });
    pendingRequests.delete(url);
    return { data: res.data };
  }).catch((err) => {
    pendingRequests.delete(url);
    throw err;
  });

  pendingRequests.set(url, promise);
  return promise;
}

export const timetableApi = {
  getSections: () => cachedGet<{ total: number; count: number; items: Section[] }>('/api/v1/sections'),
  getFaculty: () => cachedGet<Faculty[]>('/api/v1/configure/faculty'),
  getRooms: () => cachedGet<Room[]>('/api/v1/configure/rooms'),
  getSubjects: () => cachedGet<Subject[]>('/api/v1/configure/subjects'),
  getWizardDefaults: () => cachedGet<WizardDefaultsResponse>('/api/v1/configure/wizard-defaults'),
  
  createFaculty: (data: Partial<Faculty>) => {
    invalidateApiCache('/api/v1/configure/faculty');
    return api.post<Faculty>('/api/v1/configure/faculty', data);
  },
  updateFaculty: (id: number, data: Partial<Faculty>) => {
    invalidateApiCache('/api/v1/configure/faculty');
    return api.put<Faculty>(`/api/v1/configure/faculty/${id}`, data);
  },
  deleteFaculty: (id: number) => {
    invalidateApiCache('/api/v1/configure/faculty');
    return api.delete(`/api/v1/configure/faculty/${id}`);
  },

  createRoom: (data: Partial<Room>) => {
    invalidateApiCache('/api/v1/configure/rooms');
    return api.post<Room>('/api/v1/configure/rooms', data);
  },
  updateRoom: (id: number, data: Partial<Room>) => {
    invalidateApiCache('/api/v1/configure/rooms');
    return api.put<Room>(`/api/v1/configure/rooms/${id}`, data);
  },
  deleteRoom: (id: number) => {
    invalidateApiCache('/api/v1/configure/rooms');
    return api.delete(`/api/v1/configure/rooms/${id}`);
  },

  createSubject: (data: Partial<Subject>) => {
    invalidateApiCache('/api/v1/configure/subjects');
    return api.post<Subject>('/api/v1/configure/subjects', data);
  },
  updateSubject: (id: number, data: Partial<Subject>) => {
    invalidateApiCache('/api/v1/configure/subjects');
    return api.put<Subject>(`/api/v1/configure/subjects/${id}`, data);
  },
  deleteSubject: (id: number) => {
    invalidateApiCache('/api/v1/configure/subjects');
    return api.delete(`/api/v1/configure/subjects/${id}`);
  },

  batchAssignSectionSubject: (data: SectionSubjectMapRequest) => {
    invalidateApiCache('/api/v1/configure');
    return api.post('/api/v1/configure/section-subjects/batch-assign', data);
  },

  importCSV: (entityType: string, file: File) => {
    invalidateApiCache('/api/v1/configure');
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/api/v1/configure/import-csv?entity_type=${entityType}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  getVersions: () => cachedGet<TimetableVersionInfo[]>('/api/v1/timetable/versions', 10000),
  getTimetable: (versionId: number = 5, sectionName?: string) =>
    api.get(`/api/v1/timetable/version/${versionId}`, { params: { section_name: sectionName } }),
  validate: (versionId: number = 5) => api.get<ValidationReport>(`/api/v1/validate/${versionId}`),
  validateSlotMove: (req: DragDropSwapRequest) =>
    api.post<ValidationMoveResult>('/api/v1/timetable/validate-move', req),
  updateSlotAssignment: (entryId: string | number, newTimeSlotId: number, newRoomId?: number) => {
    invalidateApiCache('/api/v1/timetable');
    return api.post('/api/v1/timetable/update-slot', { entry_id: entryId, time_slot_id: newTimeSlotId, room_id: newRoomId });
  },
  deleteSlot: (entryId: string | number, versionId: number = 5) => {
    invalidateApiCache('/api/v1/timetable');
    return api.delete(`/api/v1/timetable/slot/${entryId}?version_id=${versionId}`);
  },
  importExcel: (file: File) => {
    invalidateApiCache();
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/v1/import/excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  generateFromWizard: (payload: TimetableGenerationRequest) => {
    invalidateApiCache();
    return api.post<WizardGenerationResponse>('/api/v1/solve/generate-from-wizard', payload);
  },
  exportExcel: (versionId: number = 5) =>
    api.post(`/api/v1/export/excel?version_id=${versionId}`, {}, { responseType: 'blob' }),
  getCohortGroups: () =>
    cachedGet<CohortGroupInfo[]>('/api/v1/export/excel/cohorts', 60000),
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
  getRoomTimetable: (roomCode: string, versionId: number = 5) =>
    api.get(`/api/v1/timetable/room/${roomCode}`, { params: { version_id: versionId } }),
  exportSingleFacultyPdf: (facultyId: number, versionId: number = 5) =>
    api.get(`/api/v1/export/pdf/faculty/${facultyId}`, { params: { version_id: versionId }, responseType: 'blob' }),
  syncSmartClass: () => api.post('/api/v1/timetable/sync-master'),
  updateSlot: (data: unknown) => {
    invalidateApiCache('/api/v1/timetable');
    return api.post('/api/v1/timetable/update-slot', data);
  },
  exportJson: (versionId: number = 5) => api.get(`/api/v1/export/json?version_id=${versionId}`),
  exportRoomUtilization: (versionId: number = 5) =>
    api.get(`/api/v1/export/room-utilization?version_id=${versionId}`, { responseType: 'blob' }),
  exportMasterIcal: (versionId: number = 5) =>
    api.get(`/api/v1/export/ical/master`, { params: { version_id: versionId }, responseType: 'blob' }),
  exportCohortIcal: (cohortKey: string, versionId: number = 5) =>
    api.get(`/api/v1/export/ical/cohort/${cohortKey}`, { params: { version_id: versionId }, responseType: 'blob' }),
  exportSectionIcal: (sectionIdentifier: string, versionId: number = 5) =>
    api.get(`/api/v1/export/ical/section/${sectionIdentifier}`, { params: { version_id: versionId }, responseType: 'blob' }),
  exportFacultyIcal: (facultyId: number, versionId: number = 5) =>
    api.get(`/api/v1/export/ical/faculty/${facultyId}`, { params: { version_id: versionId }, responseType: 'blob' }),
  getTelemetryMetrics: () => api.get('/api/v1/telemetry/metrics'),
};
