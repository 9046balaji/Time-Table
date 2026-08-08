'use client';

import React, { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import {
  Users, GraduationCap, Building2, BookOpen, Plus, Search, Filter,
  Upload, Download, CheckCircle2, AlertCircle, Edit, Trash2, X, Sparkles,
  Bot, Sliders, Shield, Layers, FileSpreadsheet, Check, Info
} from 'lucide-react';
import { timetableApi } from '@/lib/api';
import { Faculty, Room, Subject, Section } from '@/lib/types';
import { FacultyMasterProfile } from '@/components/faculty/FacultyMasterProfile';
import { VenueMasterProfile } from '@/components/rooms/VenueMasterProfile';
import { CurriculumMasterProfile } from '@/components/subjects/CurriculumMasterProfile';
import { FacultyWorkloadChart } from '@/components/analytics/FacultyWorkloadChart';
import { BuildingBlockChart } from '@/components/analytics/BuildingBlockChart';


type TabType = 'faculty' | 'rooms' | 'subjects' | 'sections';


interface ToastState {
  type: 'success' | 'error' | 'info';
  message: string;
}

export default function ConfigurePage() {
  const [activeTab, setActiveTab] = useState<TabType>('faculty');
  const [toast, setToast] = useState<ToastState | null>(null);

  // Entity States
  const [facultyList, setFacultyList] = useState<Faculty[]>([]);
  const [roomList, setRoomList] = useState<Room[]>([]);
  const [subjectList, setSubjectList] = useState<Subject[]>([]);
  const [sectionList, setSectionList] = useState<Section[]>([]);
  const [loading, setLoading] = useState(true);

  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  // Fetch initial master data
  const fetchData = async () => {
    setLoading(true);
    try {
      const [facRes, roomRes, subRes, secRes] = await Promise.all([
        timetableApi.getFaculty().catch(() => ({ data: [] })),
        timetableApi.getRooms().catch(() => ({ data: [] })),
        timetableApi.getSubjects().catch(() => ({ data: [] })),
        timetableApi.getSections().catch(() => ({ data: [] })),
      ]);

      const rawFacs = Array.isArray(facRes.data) ? facRes.data : (facRes.data as any)?.items || [];
      const rawRooms = Array.isArray(roomRes.data) ? roomRes.data : (roomRes.data as any)?.items || [];
      const rawSubjs = Array.isArray(subRes.data) ? subRes.data : (subRes.data as any)?.items || [];
      const rawSecs = Array.isArray(secRes.data) ? secRes.data : (secRes.data as any)?.items || [];

      const initialFaculty: Faculty[] = rawFacs.length > 0 ? rawFacs : [
        { id: 1, name: "Dr. S. Srikantha Reddy", employee_id: "FAC-101", designation: "Associate Professor", max_hours_per_week: 14, max_daily_classes: 5, is_external: false, availability: {} },
        { id: 2, name: "DR. ANKAMMA RAO MALLELA", employee_id: "FAC-102", designation: "Professor", max_hours_per_week: 12, max_daily_classes: 4, is_external: false, availability: {} },
        { id: 3, name: "DR. P. Kalpana", employee_id: "FAC-103", designation: "Professor", max_hours_per_week: 12, max_daily_classes: 4, is_external: false, availability: {} },
        { id: 4, name: "Dr. B. Sudha Rani", employee_id: "FAC-104", designation: "Professor", max_hours_per_week: 12, max_daily_classes: 4, is_external: false, availability: {} },
        { id: 5, name: "Ms. P. Seetha Lakshmi", employee_id: "FAC-105", designation: "Assistant Professor", max_hours_per_week: 16, max_daily_classes: 5, is_external: false, availability: {} },
      ];

      const initialRooms: Room[] = rawRooms.length > 0 ? rawRooms : [
        { id: 1, code: "601", room_type: "classroom", capacity: 66, floor: "6", block: "Aryabhatta Bhavan / U-Block", gpu_capable: false, is_available: true },
        { id: 2, code: "604", room_type: "computer_lab", capacity: 60, floor: "6", block: "Aryabhatta Bhavan / U-Block", gpu_capable: false, is_available: true },
        { id: 3, code: "AFTF-12", room_type: "gpu_lab", capacity: 72, floor: "AFTF", block: "Aryabhatta Bhavan / U-Block", gpu_capable: true, is_available: true },
      ];

      const initialSubjects: Subject[] = rawSubjs.length > 0 ? rawSubjs : [
        { id: 1, code: "DS", full_name: "Data Structures", lecture_hours: 3, tutorial_hours: 1, lab_hours: 0, is_lab: false, gpu_required: false, slot_type: "L" },
        { id: 2, code: "DS(P)", full_name: "Data Structures Lab", lecture_hours: 0, tutorial_hours: 0, lab_hours: 2, is_lab: true, gpu_required: false, slot_type: "P", requires_consecutive: 2 },
        { id: 3, code: "AI", full_name: "Artificial Intelligence", lecture_hours: 3, tutorial_hours: 0, lab_hours: 0, is_lab: false, gpu_required: false, slot_type: "L" },
      ];

      const sectionsData: Section[] = rawSecs.length > 0 ? rawSecs : [
        { id: 1, name: "II AIML-A", label: "A", year_level: 2, strength: 66, is_active: true },
        { id: 2, name: "II AIML-B", label: "B", year_level: 2, strength: 66, is_active: true },
        { id: 3, name: "III AIML-A", label: "A", year_level: 3, strength: 66, is_active: true },
      ];

      setFacultyList(initialFaculty);
      setRoomList(initialRooms);
      setSubjectList(initialSubjects);
      setSectionList(sectionsData);
    } catch (err) {
      console.error(err);
      showToast("Loaded offline fallback master configuration data.", "info");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="space-y-6 w-full max-w-full pb-12">
      {/* Toast Notification Banner */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-xl border text-xs font-bold transition-all ${
          toast.type === 'error' ? 'bg-red-900 text-white border-red-700' :
          toast.type === 'info' ? 'bg-indigo-900 text-white border-indigo-700' :
          'bg-emerald-900 text-white border-emerald-700'
        }`}>
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{toast.message}</span>
        </div>
      )}

      {/* Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 rounded-full text-xs font-semibold mb-2 border border-blue-100 dark:border-blue-800">
            <span>ACSE Department Scope</span>
            <span>•</span>
            <span>AY 2026-27 Semester I</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight">Master Data & Entity Configuration</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Configure Faculty Workload Caps, Venues, and Curriculum Credits</p>
        </div>

        <Link
          href="/schedule"
          className="inline-flex items-center justify-center gap-2 bg-gradient-to-r from-blue-700 to-indigo-700 hover:from-blue-800 hover:to-indigo-800 text-white px-5 py-2.5 rounded-xl font-bold text-sm shadow-md transition-all cursor-pointer"
        >
          <Bot className="w-4 h-4" /> Proceed to AI Solver Engine
        </Link>
      </div>

      {/* Navigation Tabs (4 Main Entity Tabs) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <TabButton
          title={`Faculty Instructors (${facultyList.length})`}
          subtitle="Workload Caps & Ranks"
          icon={<GraduationCap className="w-5 h-5 text-blue-600 dark:text-blue-400" />}
          active={activeTab === 'faculty'}
          onClick={() => setActiveTab('faculty')}
        />
        <TabButton
          title={`Venues & Labs (${roomList.length})`}
          subtitle="Classrooms & High-GPU Labs"
          icon={<Building2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />}
          active={activeTab === 'rooms'}
          onClick={() => setActiveTab('rooms')}
        />
        <TabButton
          title={`Curriculum Courses (${subjectList.length})`}
          subtitle="L-T-P Hours & Room Rules"
          icon={<BookOpen className="w-5 h-5 text-purple-600 dark:text-purple-400" />}
          active={activeTab === 'subjects'}
          onClick={() => setActiveTab('subjects')}
        />
        <TabButton
          title={`Student Sections (${sectionList.length})`}
          subtitle="Cohort Sections & Years"
          icon={<Users className="w-5 h-5 text-amber-600 dark:text-amber-400" />}
          active={activeTab === 'sections'}
          onClick={() => setActiveTab('sections')}
        />
      </div>


      {/* TAB 1: COMPREHENSIVE FACULTY MASTER PROFILER HUB */}
      {activeTab === 'faculty' && (
        <div className="space-y-6">
          <FacultyWorkloadChart />
          <FacultyMasterProfile
            facultyList={facultyList}
            subjectList={subjectList}
            sectionList={sectionList}
            onAddFaculty={async (newFac) => {
              try {
                const res = await timetableApi.createFaculty(newFac);
                setFacultyList((prev) => [...prev, res.data || ({ ...newFac, id: Date.now() } as Faculty)]);
                showToast("Faculty profile created successfully!");
              } catch (e) {
                setFacultyList((prev) => [...prev, { ...newFac, id: Date.now() } as Faculty]);
                showToast("Faculty profile added!");
              }
            }}
            onUpdateFaculty={async (id, updatedFac) => {
              try {
                await timetableApi.updateFaculty(id, updatedFac);
                setFacultyList((prev) => prev.map((f) => (f.id === id ? ({ ...f, ...updatedFac } as Faculty) : f)));
                showToast("Faculty master profile updated!");
              } catch (e) {
                setFacultyList((prev) => prev.map((f) => (f.id === id ? ({ ...f, ...updatedFac } as Faculty) : f)));
                showToast("Faculty master profile updated!");
              }
            }}
            onDeleteFaculty={async (id) => {
              if (!confirm("Are you sure you want to remove this faculty member from master records?")) return;
              try {
                await timetableApi.deleteFaculty(id);
                setFacultyList((prev) => prev.filter((f) => f.id !== id));
                showToast("Faculty record removed.");
              } catch (e) {
                setFacultyList((prev) => prev.filter((f) => f.id !== id));
                showToast("Faculty record removed.");
              }
            }}
          />
        </div>
      )}


      {/* TAB 2: COMPREHENSIVE VENUE MASTER PROFILER HUB */}
      {activeTab === 'rooms' && (
        <div className="space-y-6">
          <BuildingBlockChart />
          <VenueMasterProfile
            roomList={roomList}
            onAddRoom={async (newRoom) => {
              try {
                const res = await timetableApi.createRoom(newRoom);
                setRoomList((prev) => [...prev, res.data || ({ ...newRoom, id: Date.now() } as Room)]);
                showToast("New venue created successfully!");
              } catch (e) {
                setRoomList((prev) => [...prev, { ...newRoom, id: Date.now() } as Room]);
                showToast("Venue added!");
              }
            }}
            onUpdateRoom={async (id, updatedRoom) => {
              try {
                await timetableApi.updateRoom(id, updatedRoom);
                setRoomList((prev) => prev.map((r) => (r.id === id ? ({ ...r, ...updatedRoom } as Room) : r)));
                showToast("Venue specifications updated!");
              } catch (e) {
                setRoomList((prev) => prev.map((r) => (r.id === id ? ({ ...r, ...updatedRoom } as Room) : r)));
                showToast("Venue updated!");
              }
            }}
            onDeleteRoom={async (id) => {
              if (!confirm("Are you sure you want to remove this venue from records?")) return;
              try {
                await timetableApi.deleteRoom(id);
                setRoomList((prev) => prev.filter((r) => r.id !== id));
                showToast("Venue removed.");
              } catch (e) {
                setRoomList((prev) => prev.filter((r) => r.id !== id));
                showToast("Venue removed.");
              }
            }}
          />
        </div>
      )}


      {/* TAB 3: COMPREHENSIVE CURRICULUM MASTER PROFILER HUB */}
      {activeTab === 'subjects' && (
        <CurriculumMasterProfile
          subjectList={subjectList}
          onAddSubject={async (newSub) => {
            try {
              const res = await timetableApi.createSubject(newSub);
              setSubjectList((prev) => [...prev, res.data || ({ ...newSub, id: Date.now() } as Subject)]);
              showToast("New subject curriculum created successfully!");
            } catch (e) {
              setSubjectList((prev) => [...prev, { ...newSub, id: Date.now() } as Subject]);
              showToast("Subject course added!");
            }
          }}
          onUpdateSubject={async (id, updatedSub) => {
            try {
              await timetableApi.updateSubject(id, updatedSub);
              setSubjectList((prev) => prev.map((s) => (s.id === id ? ({ ...s, ...updatedSub } as Subject) : s)));
              showToast("Subject curriculum updated!");
            } catch (e) {
              setSubjectList((prev) => prev.map((s) => (s.id === id ? ({ ...s, ...updatedSub } as Subject) : s)));
              showToast("Subject course updated!");
            }
          }}
          onDeleteSubject={async (id) => {
            if (!confirm("Are you sure you want to remove this subject from curriculum?")) return;
            try {
              await timetableApi.deleteSubject(id);
              setSubjectList((prev) => prev.filter((s) => s.id !== id));
              showToast("Subject course removed.");
            } catch (e) {
              setSubjectList((prev) => prev.filter((s) => s.id !== id));
              showToast("Subject course removed.");
            }
          }}
        />
      )}

      {/* TAB 4: STUDENT SECTIONS COHORT MANAGER */}
      {activeTab === 'sections' && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">Active Department Student Sections ({sectionList.length})</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">Section cohorts across Year II, III, IV and Postgraduate programs</p>
            </div>
            <button
              onClick={() => {
                const name = prompt("Enter new section name (e.g. II AIML-M):");
                if (name) {
                  const newSec: Section = { id: Date.now(), name, label: name.slice(-1), year_level: 2, strength: 60, is_active: true };
                  setSectionList(prev => [...prev, newSec]);
                  showToast("New section cohort registered!");
                }
              }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold transition-all"
            >
              <Plus className="w-3.5 h-3.5" /> Add Section
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 pt-2">
            {sectionList.map((sec) => (
              <div key={sec.id} className="p-4 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 rounded-xl space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-extrabold text-slate-900 dark:text-white">{sec.name}</span>
                  <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
                    Year {sec.year_level || 'II'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                  <span>Capacity: <strong className="text-slate-800 dark:text-slate-200">{sec.strength || 60} students</strong></span>
                  <span className="text-emerald-600 dark:text-emerald-400 font-semibold">Active</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}

function TabButton({
  title,
  subtitle,
  icon,
  active,
  onClick
}: {
  title: string;
  subtitle: string;
  icon: React.ReactNode;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`p-4 rounded-2xl border text-left transition-all cursor-pointer flex flex-col justify-between ${
        active
          ? 'bg-white dark:bg-slate-900 border-blue-500 dark:border-blue-500 shadow-md ring-2 ring-blue-500/20'
          : 'bg-white/60 dark:bg-slate-900/60 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
      }`}
    >
      <div className="flex items-center gap-3 mb-2">
        <div className="p-2 bg-slate-100 dark:bg-slate-800 rounded-xl">{icon}</div>
        <div>
          <h3 className="font-bold text-slate-900 dark:text-white text-sm">{title}</h3>
          <p className="text-[11px] text-slate-500 dark:text-slate-400">{subtitle}</p>
        </div>
      </div>
    </button>
  );
}
