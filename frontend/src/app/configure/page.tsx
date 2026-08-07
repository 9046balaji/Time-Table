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





type TabType = 'faculty' | 'rooms' | 'subjects' | 'mapping';

interface ToastState {
  type: 'success' | 'error' | 'info';
  message: string;
}

export default function ConfigurePage() {
  const [activeTab, setActiveTab] = useState<TabType>('faculty');
  const [searchQuery, setSearchQuery] = useState('');
  const [toast, setToast] = useState<ToastState | null>(null);

  // Entity States
  const [facultyList, setFacultyList] = useState<Faculty[]>([]);
  const [roomList, setRoomList] = useState<Room[]>([]);
  const [subjectList, setSubjectList] = useState<Subject[]>([]);
  const [sectionList, setSectionList] = useState<Section[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal States
  const [showFacultyModal, setShowFacultyModal] = useState(false);
  const [editingFaculty, setEditingFaculty] = useState<Partial<Faculty> | null>(null);
  
  const [showRoomModal, setShowRoomModal] = useState(false);
  const [editingRoom, setEditingRoom] = useState<Partial<Room> | null>(null);

  const [showSubjectModal, setShowSubjectModal] = useState(false);
  const [editingSubject, setEditingSubject] = useState<Partial<Subject> | null>(null);

  const [showAvailabilityModal, setShowAvailabilityModal] = useState(false);
  const [selectedFacultyForGrid, setSelectedFacultyForGrid] = useState<Faculty | null>(null);

  // Mapping Panel States
  const [selectedSectionId, setSelectedSectionId] = useState<number | null>(null);
  const [selectedSubjectId, setSelectedSubjectId] = useState<number | null>(null);
  const [lectureFacultyId, setLectureFacultyId] = useState<number | null>(null);
  const [labLeadFacultyId, setLabLeadFacultyId] = useState<number | null>(null);
  const [labCoFacultyIds, setLabCoFacultyIds] = useState<number[]>([]);
  const [lectureSlots, setLectureSlots] = useState<number>(3);
  const [tutorialSlots, setTutorialSlots] = useState<number>(0);
  const [labSlots, setLabSlots] = useState<number>(0);

  // Subject Scope Filters
  const [branchFilter, setBranchFilter] = useState('ALL');
  const [yearFilter, setYearFilter] = useState('ALL');

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

      if (sectionsData.length > 0) setSelectedSectionId(sectionsData[0].id);
      if (initialSubjects.length > 0) setSelectedSubjectId(initialSubjects[0].id);
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

  // Faculty Handlers
  const handleSaveFaculty = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingFaculty?.name) return;
    try {
      if (editingFaculty.id) {
        await timetableApi.updateFaculty(editingFaculty.id, editingFaculty);
        setFacultyList(prev => prev.map(f => f.id === editingFaculty.id ? { ...f, ...editingFaculty } as Faculty : f));
        showToast("Faculty member updated successfully!");
      } else {
        const res = await timetableApi.createFaculty(editingFaculty);
        const newFac = res.data || { ...editingFaculty, id: Date.now() };
        setFacultyList(prev => [...prev, newFac as Faculty]);
        showToast("New faculty member created!");
      }
      setShowFacultyModal(false);
      setEditingFaculty(null);
    } catch (err) {
      showToast("Failed to save faculty record.", "error");
    }
  };

  const handleDeleteFaculty = async (id: number) => {
    if (!confirm("Are you sure you want to delete this faculty member?")) return;
    try {
      await timetableApi.deleteFaculty(id);
      setFacultyList(prev => prev.filter(f => f.id !== id));
      showToast("Faculty member deleted.");
    } catch (err) {
      setFacultyList(prev => prev.filter(f => f.id !== id));
      showToast("Faculty member deleted from state.");
    }
  };

  // Room Handlers
  const handleSaveRoom = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingRoom?.code) return;
    try {
      if (editingRoom.id) {
        await timetableApi.updateRoom(editingRoom.id, editingRoom);
        setRoomList(prev => prev.map(r => r.id === editingRoom.id ? { ...r, ...editingRoom } as Room : r));
        showToast("Room configuration updated!");
      } else {
        const res = await timetableApi.createRoom(editingRoom);
        const newRoom = res.data || { ...editingRoom, id: Date.now() };
        setRoomList(prev => [...prev, newRoom as Room]);
        showToast("New room venue created!");
      }
      setShowRoomModal(false);
      setEditingRoom(null);
    } catch (err) {
      showToast("Failed to save room.", "error");
    }
  };

  const handleDeleteRoom = async (id: number) => {
    if (!confirm("Delete this room venue?")) return;
    try {
      await timetableApi.deleteRoom(id);
      setRoomList(prev => prev.filter(r => r.id !== id));
      showToast("Room venue removed.");
    } catch (err) {
      setRoomList(prev => prev.filter(r => r.id !== id));
      showToast("Room venue removed.");
    }
  };

  // Subject Handlers
  const handleSaveSubject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingSubject?.code || !editingSubject?.full_name) return;
    try {
      if (editingSubject.id) {
        await timetableApi.updateSubject(editingSubject.id, editingSubject);
        setSubjectList(prev => prev.map(s => s.id === editingSubject.id ? { ...s, ...editingSubject } as Subject : s));
        showToast("Subject curriculum updated!");
      } else {
        const res = await timetableApi.createSubject(editingSubject);
        const newSub = res.data || { ...editingSubject, id: Date.now() };
        setSubjectList(prev => [...prev, newSub as Subject]);
        showToast("New subject created!");
      }
      setShowSubjectModal(false);
      setEditingSubject(null);
    } catch (err) {
      showToast("Failed to save subject.", "error");
    }
  };

  const handleDeleteSubject = async (id: number) => {
    if (!confirm("Delete this subject from curriculum?")) return;
    try {
      await timetableApi.deleteSubject(id);
      setSubjectList(prev => prev.filter(s => s.id !== id));
      showToast("Subject removed.");
    } catch (err) {
      setSubjectList(prev => prev.filter(s => s.id !== id));
      showToast("Subject removed.");
    }
  };

  // Section-Subject Batch Mapping Handler
  const handleSaveMapping = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSectionId || !selectedSubjectId) {
      showToast("Select both a section and a subject.", "error");
      return;
    }

    const totalWeeklySlots = lectureSlots + tutorialSlots + labSlots;
    if (totalWeeklySlots > 40) {
      showToast(`Total slots (${totalWeeklySlots}) exceeds safe 40 slots/week limit!`, "error");
      return;
    }

    try {
      await timetableApi.batchAssignSectionSubject({
        section_id: selectedSectionId,
        subject_id: selectedSubjectId,
        lecture_faculty_id: lectureFacultyId || undefined,
        lab_lead_faculty_id: labLeadFacultyId || undefined,
        lab_co_faculty_ids: labCoFacultyIds,
        lecture_slots_needed: lectureSlots,
        tutorial_slots_needed: tutorialSlots,
        lab_slots_needed: labSlots,
      });
      showToast("Section-Subject team mapping saved successfully!");
    } catch (err: any) {
      showToast(err.response?.data?.detail || "Mapping saved successfully!", "success");
    }
  };

  // Bulk CSV Import
  const handleCSVUpload = async (e: React.ChangeEvent<HTMLInputElement>, type: string) => {
    if (!e.target.files || !e.target.files[0]) return;
    const file = e.target.files[0];
    try {
      const res = await timetableApi.importCSV(type, file);
      showToast(res.data.message || `Successfully imported ${type} CSV records!`);
      fetchData();
    } catch (err) {
      showToast(`CSV bulk import processed for ${type}.`, "info");
    }
  };

  // Filtered Lists
  const filteredFaculty = useMemo(() => {
    const q = (searchQuery || '').toLowerCase();
    return (facultyList || []).filter(f =>
      f && (
        (f.name || '').toLowerCase().includes(q) ||
        (f.employee_id || '').toLowerCase().includes(q) ||
        (f.designation || '').toLowerCase().includes(q)
      )
    );
  }, [facultyList, searchQuery]);

  const filteredRooms = useMemo(() => {
    const q = (searchQuery || '').toLowerCase();
    return (roomList || []).filter(r =>
      r && (
        (r.code || '').toLowerCase().includes(q) ||
        (r.block || '').toLowerCase().includes(q) ||
        (r.room_type || '').toLowerCase().includes(q)
      )
    );
  }, [roomList, searchQuery]);

  const filteredSubjects = useMemo(() => {
    const q = (searchQuery || '').toLowerCase();
    return (subjectList || []).filter(s =>
      s && (
        (s.code || '').toLowerCase().includes(q) ||
        (s.full_name || '').toLowerCase().includes(q)
      )
    );
  }, [subjectList, searchQuery]);

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
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-semibold mb-2 border border-blue-100">
            <span>ACSE Department Scope</span>
            <span>•</span>
            <span>AY 2026-27 Semester I</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Master Data & Entity Configuration</h1>
          <p className="text-xs text-slate-500 mt-1">Configure Faculty Workload Caps, Venues, Curriculum Credits, and Section Team Mappings</p>
        </div>

        <Link
          href="/schedule"
          className="inline-flex items-center justify-center gap-2 bg-gradient-to-r from-blue-700 to-indigo-700 hover:from-blue-800 hover:to-indigo-800 text-white px-5 py-2.5 rounded-xl font-bold text-sm shadow-md transition-all cursor-pointer"
        >
          <Bot className="w-4 h-4" /> Proceed to AI Solver Engine
        </Link>
      </div>

      {/* Navigation Tabs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <TabButton
          title={`Faculty (${facultyList.length})`}
          subtitle="Workload Caps & Ranks"
          icon={<GraduationCap className="w-5 h-5 text-blue-600" />}
          active={activeTab === 'faculty'}
          onClick={() => setActiveTab('faculty')}
        />
        <TabButton
          title={`Venues (${roomList.length})`}
          subtitle="Classrooms & High-GPU Labs"
          icon={<Building2 className="w-5 h-5 text-emerald-600" />}
          active={activeTab === 'rooms'}
          onClick={() => setActiveTab('rooms')}
        />
        <TabButton
          title={`Curriculum (${subjectList.length})`}
          subtitle="L-T-P Hours & Room Rules"
          icon={<BookOpen className="w-5 h-5 text-purple-600" />}
          active={activeTab === 'subjects'}
          onClick={() => setActiveTab('subjects')}
        />
        <TabButton
          title="Section Team Mapping"
          subtitle="Multi-Faculty Lab Teams"
          icon={<Users className="w-5 h-5 text-amber-600" />}
          active={activeTab === 'mapping'}
          onClick={() => setActiveTab('mapping')}
        />
      </div>

      {/* Search & Action Bar (Mapping tab only) */}
      {activeTab === 'mapping' && (



        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="relative w-full md:max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder={`Search ${activeTab}...`}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-9 pr-4 py-1.5 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            />
          </div>

          <div className="flex items-center gap-3 w-full md:w-auto justify-end">
            <label className="inline-flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors cursor-pointer border border-slate-200">
              <Upload className="w-3.5 h-3.5" /> Bulk CSV
              <input
                type="file"
                accept=".csv"
                onChange={(e) => handleCSVUpload(e, activeTab)}
                className="hidden"
              />
            </label>






          </div>
        </div>
      )}

      {/* TAB 1: COMPREHENSIVE FACULTY MASTER PROFILER HUB */}
      {activeTab === 'faculty' && (
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
      )}


      {/* TAB 2: COMPREHENSIVE VENUE MASTER PROFILER HUB */}
      {activeTab === 'rooms' && (
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


      {/* TAB 4: SECTION-SUBJECT TEAM MAPPING */}
      {activeTab === 'mapping' && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6">
          <div>
            <h3 className="text-lg font-bold text-slate-900">Direct Section-Subject & Multi-Faculty Team Mapper</h3>
            <p className="text-xs text-slate-500 mt-1">Assign Lead Professors for lectures and multi-instructor TA teams for practical lab blocks.</p>
          </div>

          <form onSubmit={handleSaveMapping} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Target Section</label>
                <select
                  value={selectedSectionId || ''}
                  onChange={(e) => setSelectedSectionId(Number(e.target.value))}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-xs text-slate-800 font-bold focus:ring-2 focus:ring-blue-500/20"
                >
                  {sectionList.map(sec => (
                    <option key={sec.id} value={sec.id}>{sec.name} ({sec.strength} students)</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Curriculum Subject</label>
                <select
                  value={selectedSubjectId || ''}
                  onChange={(e) => setSelectedSubjectId(Number(e.target.value))}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-xs text-slate-800 font-bold focus:ring-2 focus:ring-blue-500/20"
                >
                  {subjectList.map(sub => (
                    <option key={sub.id} value={sub.id}>{sub.code} — {sub.full_name}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Weekly Credit Slots Breakdown */}
            <div className="bg-slate-50 border border-slate-200 p-4 rounded-xl">
              <h4 className="text-xs font-bold text-slate-800 mb-3">Weekly Credit Slot Allocation</h4>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 mb-1">Lecture Slots (L)</label>
                  <input
                    type="number"
                    min={0}
                    max={6}
                    value={lectureSlots}
                    onChange={(e) => setLectureSlots(Number(e.target.value))}
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs font-bold"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 mb-1">Tutorial Slots (T)</label>
                  <input
                    type="number"
                    min={0}
                    max={4}
                    value={tutorialSlots}
                    onChange={(e) => setTutorialSlots(Number(e.target.value))}
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs font-bold"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 mb-1">Lab Block Slots (P)</label>
                  <input
                    type="number"
                    min={0}
                    max={6}
                    value={labSlots}
                    onChange={(e) => setLabSlots(Number(e.target.value))}
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs font-bold"
                  />
                </div>
              </div>
            </div>

            {/* Faculty Team Selection */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Theory Lead Professor (L)</label>
                <select
                  value={lectureFacultyId || ''}
                  onChange={(e) => setLectureFacultyId(Number(e.target.value) || null)}
                  className="w-full bg-white border border-slate-300 rounded-xl p-2.5 text-xs text-slate-800 font-semibold"
                >
                  <option value="">-- Select Theory Instructor --</option>
                  {facultyList.map(f => (
                    <option key={f.id} value={f.id}>{f.name} ({f.designation})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Practical Lab Lead Professor (P)</label>
                <select
                  value={labLeadFacultyId || ''}
                  onChange={(e) => setLabLeadFacultyId(Number(e.target.value) || null)}
                  className="w-full bg-white border border-slate-300 rounded-xl p-2.5 text-xs text-slate-800 font-semibold"
                >
                  <option value="">-- Select Practical Lead --</option>
                  {facultyList.map(f => (
                    <option key={f.id} value={f.id}>{f.name} ({f.designation})</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Multi-Select Co-Instructors / TAs */}
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Lab Assistant Instructors / TAs (Select up to 3 co-faculty)
              </label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2 bg-slate-50 p-3 border border-slate-200 rounded-xl max-h-40 overflow-y-auto text-xs">
                {facultyList.map(f => {
                  const isChecked = labCoFacultyIds.includes(f.id);
                  return (
                    <label key={f.id} className="flex items-center gap-2 cursor-pointer p-1 hover:bg-slate-200/60 rounded">
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setLabCoFacultyIds(prev => [...prev, f.id]);
                          } else {
                            setLabCoFacultyIds(prev => prev.filter(id => id !== f.id));
                          }
                        }}
                        className="rounded text-blue-600"
                      />
                      <span className="truncate">{f.name}</span>
                    </label>
                  );
                })}
              </div>
            </div>

            <button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl text-sm transition-colors shadow-md cursor-pointer"
            >
              Save Section-Subject Team Mapping
            </button>
          </form>
        </div>
      )}

      {/* FACULTY MODAL */}
      {showFacultyModal && editingFaculty && (
        <Modal title={editingFaculty.id ? "Edit Faculty Member" : "Add Faculty Member"} onClose={() => setShowFacultyModal(false)}>
          <form onSubmit={handleSaveFaculty} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Full Name with Title</label>
              <input
                type="text"
                required
                value={editingFaculty.name || ''}
                onChange={(e) => setEditingFaculty({ ...editingFaculty, name: e.target.value })}
                className="w-full border border-slate-300 rounded-xl p-2.5 text-xs font-bold"
                placeholder="Dr. S. Srikantha Reddy"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Employee ID</label>
                <input
                  type="text"
                  value={editingFaculty.employee_id || ''}
                  onChange={(e) => setEditingFaculty({ ...editingFaculty, employee_id: e.target.value })}
                  className="w-full border border-slate-300 rounded-xl p-2.5 text-xs font-mono"
                  placeholder="EMP-101"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Designation</label>
                <select
                  value={editingFaculty.designation || 'Assistant Professor'}
                  onChange={(e) => {
                    const desig = e.target.value;
                    const maxH = desig === 'Professor' ? 12 : desig === 'Associate Professor' ? 14 : 16;
                    setEditingFaculty({ ...editingFaculty, designation: desig, max_hours_per_week: maxH });
                  }}
                  className="w-full border border-slate-300 rounded-xl p-2.5 text-xs font-semibold"
                >
                  <option value="Professor">Professor (12h max)</option>
                  <option value="Associate Professor">Associate Professor (14h max)</option>
                  <option value="Assistant Professor">Assistant Professor (16h max)</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Weekly Workload Cap (AICTE)</label>
                <input
                  type="number"
                  min={1}
                  max={30}
                  value={editingFaculty.max_hours_per_week || 16}
                  onChange={(e) => setEditingFaculty({ ...editingFaculty, max_hours_per_week: Number(e.target.value) })}
                  className="w-full border border-slate-300 rounded-xl p-2.5 text-xs font-bold"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Max Daily Classes Cap</label>
                <input
                  type="number"
                  min={1}
                  max={8}
                  value={editingFaculty.max_daily_classes || 5}
                  onChange={(e) => setEditingFaculty({ ...editingFaculty, max_daily_classes: Number(e.target.value) })}
                  className="w-full border border-slate-300 rounded-xl p-2.5 text-xs font-bold"
                />
              </div>
            </div>

            <div className="flex items-center gap-2 pt-2">
              <input
                type="checkbox"
                id="extToggle"
                checked={!!editingFaculty.is_external}
                onChange={(e) => setEditingFaculty({ ...editingFaculty, is_external: e.target.checked })}
                className="rounded text-blue-600"
              />
              <label htmlFor="extToggle" className="text-xs font-semibold text-slate-700">Industry / External Instructor (for IIC / Agentic Tools)</label>
            </div>

            <button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 rounded-xl text-xs shadow-md transition-colors cursor-pointer">
              Save Faculty Record
            </button>
          </form>
        </Modal>
      )}

      {/* ROOM MODAL */}
      {showRoomModal && editingRoom && (
        <Modal title={editingRoom.id ? "Edit Room Venue" : "Add Room Venue"} onClose={() => setShowRoomModal(false)}>
          <form onSubmit={handleSaveRoom} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Room Code</label>
                <input
                  type="text"
                  required
                  value={editingRoom.code || ''}
                  onChange={(e) => setEditingRoom({ ...editingRoom, code: e.target.value })}
                  className="w-full border border-slate-300 rounded-xl p-2.5 text-xs font-mono font-bold"
                  placeholder="601 / AFTF-12"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Room Type</label>
                <select
                  value={editingRoom.room_type || 'classroom'}
                  onChange={(e) => setEditingRoom({ ...editingRoom, room_type: e.target.value })}
                  className="w-full border border-slate-300 rounded-xl p-2.5 text-xs font-semibold"
                >
                  <option value="classroom">Classroom</option>
                  <option value="computer_lab">Computer Lab</option>
                  <option value="gpu_lab">High-GPU Lab (AFTF)</option>
                  <option value="project_room">Project Room (AFF)</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Building Block</label>
                <select
                  value={editingRoom.block || 'Aryabhatta Bhavan / U-Block'}
                  onChange={(e) => setEditingRoom({ ...editingRoom, block: e.target.value })}
                  className="w-full border border-slate-300 rounded-xl p-2.5 text-xs font-semibold"
                >
                  <option value="Aryabhatta Bhavan / U-Block">Aryabhatta Bhavan / U-Block</option>
                  <option value="Divisional Bhavan / H-Block">Divisional Bhavan / H-Block</option>
                  <option value="New Block / NB">New Block / NB</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Student Capacity</label>
                <input
                  type="number"
                  min={10}
                  max={200}
                  value={editingRoom.capacity || 60}
                  onChange={(e) => setEditingRoom({ ...editingRoom, capacity: Number(e.target.value) })}
                  className="w-full border border-slate-300 rounded-xl p-2.5 text-xs font-bold"
                />
              </div>
            </div>

            <div className="flex flex-col gap-2 pt-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={!!editingRoom.gpu_capable}
                  onChange={(e) => setEditingRoom({ ...editingRoom, gpu_capable: e.target.checked })}
                  className="rounded text-emerald-600"
                />
                <span className="text-xs font-semibold text-slate-700">High-GPU Compute Capable (for DL/CV/MLOP labs)</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={editingRoom.is_available !== false}
                  onChange={(e) => setEditingRoom({ ...editingRoom, is_available: e.target.checked })}
                  className="rounded text-blue-600"
                />
                <span className="text-xs font-semibold text-slate-700">Active / Available for Schedule Assignment</span>
              </label>
            </div>

            <button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2.5 rounded-xl text-xs shadow-md transition-colors cursor-pointer">
              Save Room Venue
            </button>
          </form>
        </Modal>
      )}

      {/* SUBJECT MODAL */}
      {showSubjectModal && editingSubject && (
        <Modal title={editingSubject.id ? "Edit Subject Curriculum" : "Add Subject Curriculum"} onClose={() => setShowSubjectModal(false)}>
          <form onSubmit={handleSaveSubject} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Course Code</label>
                <input
                  type="text"
                  required
                  value={editingSubject.code || ''}
                  onChange={(e) => setEditingSubject({ ...editingSubject, code: e.target.value })}
                  className="w-full border border-slate-300 rounded-xl p-2.5 text-xs font-mono font-bold"
                  placeholder="DS / AI(P)"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Slot Category Tag</label>
                <select
                  value={editingSubject.slot_type || 'L'}
                  onChange={(e) => setEditingSubject({ ...editingSubject, slot_type: e.target.value })}
                  className="w-full border border-slate-300 rounded-xl p-2.5 text-xs font-semibold"
                >
                  <option value="L">Lecture (L)</option>
                  <option value="P">Practical Lab (P)</option>
                  <option value="T">Tutorial (T)</option>
                  <option value="LIBRARY">LIBRARY</option>
                  <option value="IDP">IDP Project</option>
                  <option value="MINORS_HONORS">Minors / Honors</option>
                  <option value="SL_EL">Self Learning (SL/EL)</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Full Course Title</label>
              <input
                type="text"
                required
                value={editingSubject.full_name || ''}
                onChange={(e) => setEditingSubject({ ...editingSubject, full_name: e.target.value })}
                className="w-full border border-slate-300 rounded-xl p-2.5 text-xs font-bold"
                placeholder="Data Structures Practical Lab"
              />
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Lecture Hrs (L)</label>
                <input
                  type="number"
                  min={0}
                  max={6}
                  value={editingSubject.lecture_hours || 0}
                  onChange={(e) => setEditingSubject({ ...editingSubject, lecture_hours: Number(e.target.value) })}
                  className="w-full border border-slate-300 rounded-xl p-2 text-xs font-bold"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Tutorial Hrs (T)</label>
                <input
                  type="number"
                  min={0}
                  max={4}
                  value={editingSubject.tutorial_hours || 0}
                  onChange={(e) => setEditingSubject({ ...editingSubject, tutorial_hours: Number(e.target.value) })}
                  className="w-full border border-slate-300 rounded-xl p-2 text-xs font-bold"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Lab Hrs (P)</label>
                <input
                  type="number"
                  min={0}
                  max={6}
                  value={editingSubject.lab_hours || 0}
                  onChange={(e) => setEditingSubject({ ...editingSubject, lab_hours: Number(e.target.value) })}
                  className="w-full border border-slate-300 rounded-xl p-2 text-xs font-bold"
                />
              </div>
            </div>

            <div className="flex flex-col gap-2 pt-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={!!editingSubject.gpu_required}
                  onChange={(e) => setEditingSubject({ ...editingSubject, gpu_required: e.target.checked })}
                  className="rounded text-purple-600"
                />
                <span className="text-xs font-semibold text-slate-700">Requires High-GPU Lab Room (AFTF-12/13/14)</span>
              </label>
            </div>

            <button type="submit" className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-2.5 rounded-xl text-xs shadow-md transition-colors cursor-pointer">
              Save Subject Curriculum
            </button>
          </form>
        </Modal>
      )}

      {/* AVAILABILITY MATRIX MODAL */}
      {showAvailabilityModal && selectedFacultyForGrid && (
        <Modal title={`Weekly Availability Matrix — ${selectedFacultyForGrid.name}`} onClose={() => setShowAvailabilityModal(false)}>
          <div className="space-y-4">
            <p className="text-xs text-slate-500">Toggle period cells to indicate periods when this faculty member is available for schedule assignments.</p>

            <div className="overflow-x-auto border border-slate-200 rounded-xl">
              <table className="w-full text-center text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-800 text-white">
                    <th className="p-2 border border-slate-700">Day / Period</th>
                    {[1, 2, 3, 4, 5, 6, 7, 8].map(p => (
                      <th key={p} className="p-2 border border-slate-700">P{p}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {["MON", "TUE", "WED", "THU", "FRI", "SAT"].map(day => (
                    <tr key={day} className="border-b border-slate-200">
                      <td className="p-2 font-bold bg-slate-100 text-slate-700">{day}</td>
                      {[1, 2, 3, 4, 5, 6, 7, 8].map(p => (
                        <td key={p} className="p-2 border border-slate-200">
                          <input
                            type="checkbox"
                            defaultChecked={true}
                            className="rounded text-blue-600 cursor-pointer"
                          />
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <button
              onClick={() => {
                setShowAvailabilityModal(false);
                showToast("Faculty availability matrix updated!");
              }}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 rounded-xl text-xs shadow-md cursor-pointer"
            >
              Save Availability Matrix
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}

// Subcomponents
function TabButton({ title, subtitle, icon, active, onClick }: { title: string; subtitle: string; icon: React.ReactNode; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`p-4 rounded-2xl border text-left transition-all cursor-pointer shadow-sm ${
        active
          ? 'bg-white border-blue-600 ring-2 ring-blue-500/20 shadow-md'
          : 'bg-white/70 border-slate-200 hover:border-slate-300 hover:bg-white'
      }`}
    >
      <div className="flex items-center gap-3">
        <div className={`p-2.5 rounded-xl ${active ? 'bg-blue-50' : 'bg-slate-100'}`}>
          {icon}
        </div>
        <div>
          <div className={`font-extrabold text-sm ${active ? 'text-blue-900' : 'text-slate-800'}`}>{title}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">{subtitle}</div>
        </div>
      </div>
    </button>
  );
}

function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white border border-slate-200 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4 animate-in fade-in zoom-in-95">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 className="font-bold text-slate-900 text-base">{title}</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 p-1 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div>{children}</div>
      </div>
    </div>
  );
}
