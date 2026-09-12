export interface Section {
  id: number;
  name: string;
  label?: string;
  branch_id?: number;
  year_level?: number;
  branch?: string;
  year?: number;
  strength: number;
  is_active?: boolean;
}

export interface Faculty {
  id: number;
  name: string;
  employee_id?: string;
  designation: string;
  phone?: string;
  email?: string;
  max_hours_per_week?: number;
  max_daily_classes?: number;
  is_external?: boolean;
  max_hours?: number;
  hours_this_week?: number;
  current_weekly_hours?: number;
  subjects_taught?: string[];
  assigned_sections?: string[];
  availability?: Record<string, number[]>;
}

export interface Room {
  id: number;
  code: string;
  room_type?: string;
  type?: string;
  capacity: number;
  floor?: string | number;
  block?: string;
  gpu_capable?: boolean;
  is_available?: boolean;
}

export interface Subject {
  id: number;
  code: string;
  full_name: string;
  lecture_hours: number;
  tutorial_hours: number;
  lab_hours: number;
  is_lab: boolean;
  gpu_required: boolean;
  slot_type: string;
  year_level?: string | number;
  branch?: string;
  requires_consecutive?: number;
}

export interface SectionSubjectMapRequest {
  section_id: number;
  subject_id: number;
  lecture_faculty_id?: number;
  tutorial_faculty_id?: number;
  lab_lead_faculty_id?: number;
  lab_co_faculty_ids?: number[];
  lecture_slots_needed: number;
  tutorial_slots_needed: number;
  lab_slots_needed: number;
}

export interface DragDropSwapRequest {
  entry_id: string | number;
  version_id?: number;
  from_day?: string;
  from_period?: number;
  to_day?: string;
  to_period?: number;
  target_day?: string;
  target_period?: number;
  target_room_code?: string;
  room_code?: string;
  section_name?: string;
  faculty_names?: string[];
}

export interface ValidationMoveResult {
  is_valid: boolean;
  conflict_reason?: string;
  hard_violations_count?: number;
}

export interface ClashDetail {
  clash_type: 'ROOM' | 'FACULTY' | 'STUDENT' | 'BREAK';
  day: string;
  period: number;
  room?: string;
  room_id?: number;
  section_a: string;
  section_a_id?: number;
  subject_a: string;
  section_b: string;
  section_b_id?: number;
  subject_b: string;
  message: string;
}

export interface ValidationReport {
  version_id: number;
  version_label: string;
  hard_violations: number;
  soft_violations: number;
  status: 'VALID' | 'NEEDS_FIX';
  faculty_clashes?: number;
  physical_room_clashes?: number;
  joint_section_slots?: number;
  details: ClashDetail[];
}

export interface VersionInfo {
  label: string;
  date: string;
  violations: number;
  current: boolean;
  pending?: boolean;
}

export interface CourseAssignmentInput {
  subject_code: string;
  subject_name: string;
  subject_type: "L" | "P" | "T";
  faculty_name: string;
  co_faculty?: string[];
  weekly_hours: number;
  continuous_slots?: number;
}

export interface TimetableGenerationRequest {
  branch: string;
  year_level: string;
  sections: string[];
  preferred_block: string;
  max_daily_teaching_hours: number;
  max_classes_per_teacher_per_day?: number;
  assignments: CourseAssignmentInput[];
}

export interface WizardGenerationResponse {
  status: string;
  runtime_seconds: number;
  entries_count: number;
  hard_violations: number;
  soft_violations: number;
  message: string;
  version_id?: number;
  entries: Array<{
    section_id: string;
    subject_id: string;
    room_id: string;
    time_slot_id: string;
  }>;
}

export interface TimetableVersionInfo {
  id: number;
  version_label: string;
  effective_date?: string;
  hard_violations_count?: number;
  notes?: string;
  created_at?: string;
  is_current?: boolean;
}

export interface CohortGroupInfo {
  key: string;
  label: string;
  sections_count: number;
}

export interface WizardDefaultsResponse {
  faculty: Array<{ name: string }>;
  sections: Array<string | Section>;
  rooms: Room[];
  curricula: Record<string, CourseAssignmentInput[]>;
}
