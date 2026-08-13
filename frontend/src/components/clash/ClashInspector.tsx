'use client';

import React, { useState, useMemo } from 'react';
import {
  AlertTriangle,
  Filter,
  Search,
  ShieldAlert,
  Building2,
  UserCheck,
  Calendar,
  BookOpen,
  Layers,
  Users,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { ClashDetail } from '@/lib/types';

interface ClashInspectorProps {
  filename: string;
  totalSections: number;
  totalSlots: number;
  hardViolations: number;
  roomClashes: number;
  facultyClashes: number;
  clashDetails: ClashDetail[];
  totalFaculty?: number;
  totalRooms?: number;
  totalSubjects?: number;
  sectionsReport?: any[];
  facultyReport?: any[];
  roomsReport?: any[];
  subjectsReport?: any[];
}

export function ClashInspector({
  filename,
  totalSections,
  totalSlots,
  hardViolations,
  roomClashes,
  facultyClashes,
  clashDetails,
  totalFaculty = 0,
  totalRooms = 0,
  totalSubjects = 0,
  sectionsReport = [],
  facultyReport = [],
  roomsReport = [],
  subjectsReport = [],
}: ClashInspectorProps) {
  const [activeTab, setActiveTab] = useState<'clashes' | 'sections' | 'faculty' | 'rooms' | 'subjects'>('clashes');

  // Filters for Clash Tab
  const [selectedDay, setSelectedDay] = useState<string>('ALL');
  const [selectedPeriod, setSelectedPeriod] = useState<string>('ALL');
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [clashSearchQuery, setClashSearchQuery] = useState<string>('');

  // Generic Search for Entity Tabs
  const [entitySearch, setEntitySearch] = useState<string>('');

  const filteredClashes = useMemo(() => {
    return clashDetails.filter((clash) => {
      if (selectedDay !== 'ALL' && clash.day.toUpperCase() !== selectedDay) return false;
      if (selectedPeriod !== 'ALL' && String(clash.period) !== selectedPeriod) return false;
      if (selectedType !== 'ALL' && clash.clash_type !== selectedType) return false;
      if (clashSearchQuery.trim() !== '') {
        const query = clashSearchQuery.toLowerCase();
        const roomMatch = clash.room?.toLowerCase().includes(query);
        const sectionAMatch = clash.section_a.toLowerCase().includes(query);
        const sectionBMatch = clash.section_b.toLowerCase().includes(query);
        const subjectAMatch = clash.subject_a.toLowerCase().includes(query);
        const subjectBMatch = clash.subject_b.toLowerCase().includes(query);
        if (!roomMatch && !sectionAMatch && !sectionBMatch && !subjectAMatch && !subjectBMatch) {
          return false;
        }
      }
      return true;
    });
  }, [clashDetails, selectedDay, selectedPeriod, selectedType, clashSearchQuery]);

  const filteredSections = useMemo(() => {
    if (!entitySearch.trim()) return sectionsReport;
    const q = entitySearch.toLowerCase();
    return sectionsReport.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        (s.class_teacher && s.class_teacher.toLowerCase().includes(q)) ||
        s.subjects.some((sub: string) => sub.toLowerCase().includes(q))
    );
  }, [sectionsReport, entitySearch]);

  const filteredFaculty = useMemo(() => {
    if (!entitySearch.trim()) return facultyReport;
    const q = entitySearch.toLowerCase();
    return facultyReport.filter(
      (f) =>
        f.name.toLowerCase().includes(q) ||
        f.sections.some((sec: string) => sec.toLowerCase().includes(q)) ||
        f.subjects.some((sub: string) => sub.toLowerCase().includes(q))
    );
  }, [facultyReport, entitySearch]);

  const filteredRooms = useMemo(() => {
    if (!entitySearch.trim()) return roomsReport;
    const q = entitySearch.toLowerCase();
    return roomsReport.filter(
      (r) =>
        r.code.toLowerCase().includes(q) ||
        r.sections.some((sec: string) => sec.toLowerCase().includes(q)) ||
        r.subjects.some((sub: string) => sub.toLowerCase().includes(q))
    );
  }, [roomsReport, entitySearch]);

  const filteredSubjects = useMemo(() => {
    if (!entitySearch.trim()) return subjectsReport;
    const q = entitySearch.toLowerCase();
    return subjectsReport.filter(
      (s) =>
        s.code.toLowerCase().includes(q) ||
        s.sections.some((sec: string) => sec.toLowerCase().includes(q)) ||
        s.faculty.some((fac: string) => fac.toLowerCase().includes(q))
    );
  }, [subjectsReport, entitySearch]);

  const computedFacultyCount = totalFaculty || facultyReport.length;
  const computedRoomsCount = totalRooms || roomsReport.length;
  const computedSubjectsCount = totalSubjects || subjectsReport.length;

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-blue-950 text-white rounded-2xl p-6 shadow-xl border border-indigo-800/40">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className={`p-3 rounded-xl text-white shadow-md ${hardViolations > 0 ? "bg-red-600" : "bg-emerald-600"}`}>
              {hardViolations > 0 ? <ShieldAlert className="w-6 h-6" /> : <CheckCircle2 className="w-6 h-6" />}
            </div>
            <div>
              <h2 className="text-xl font-bold">Ingestion Audit & Diagnostic Inspector</h2>
              <p className="text-xs text-slate-300">File: <strong className="text-white">{filename}</strong></p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={`px-3 py-1 text-xs font-extrabold rounded-full border ${hardViolations > 0 ? "bg-red-500/20 border-red-400/40 text-red-300" : "bg-emerald-500/20 border-emerald-400/40 text-emerald-300"}`}>
              {hardViolations} HARD CONFLICTS
            </span>
          </div>
        </div>

        {/* Dynamic Metric Badges */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mt-5 pt-4 border-t border-indigo-800/50 text-xs">
          <div className="bg-white/5 rounded-xl p-2.5 border border-white/10">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Sections Parsed</span>
            <strong className="text-white font-extrabold text-base">{totalSections}</strong>
          </div>
          <div className="bg-white/5 rounded-xl p-2.5 border border-white/10">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Scheduled Slots</span>
            <strong className="text-white font-extrabold text-base">{totalSlots.toLocaleString()}</strong>
          </div>
          <div className="bg-white/5 rounded-xl p-2.5 border border-white/10">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Faculty Dossiers</span>
            <strong className="text-white font-extrabold text-base">{computedFacultyCount}</strong>
          </div>
          <div className="bg-white/5 rounded-xl p-2.5 border border-white/10">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Venues Mapped</span>
            <strong className="text-white font-extrabold text-base">{computedRoomsCount}</strong>
          </div>
          <div className="bg-white/5 rounded-xl p-2.5 border border-white/10">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Subjects Tracked</span>
            <strong className="text-white font-extrabold text-base">{computedSubjectsCount}</strong>
          </div>
          <div className="bg-white/5 rounded-xl p-2.5 border border-white/10">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Conflict Summary</span>
            <strong className={`${hardViolations > 0 ? "text-red-400" : "text-emerald-400"} font-extrabold text-base`}>
              {roomClashes} Room • {facultyClashes} Fac
            </strong>
          </div>
        </div>
      </div>

      {/* Navigation Report Tabs */}
      <div className="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800/80 p-1.5 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-x-auto">
        <button
          onClick={() => { setActiveTab('clashes'); setEntitySearch(''); }}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
            activeTab === 'clashes' ? 'bg-red-600 text-white shadow-md' : 'text-slate-600 dark:text-slate-300 hover:text-slate-900'
          }`}
        >
          <ShieldAlert className="w-4 h-4" /> Conflict Log ({hardViolations})
        </button>

        <button
          onClick={() => { setActiveTab('sections'); setEntitySearch(''); }}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
            activeTab === 'sections' ? 'bg-blue-600 text-white shadow-md' : 'text-slate-600 dark:text-slate-300 hover:text-slate-900'
          }`}
        >
          <Layers className="w-4 h-4" /> Sections Report ({totalSections})
        </button>

        <button
          onClick={() => { setActiveTab('faculty'); setEntitySearch(''); }}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
            activeTab === 'faculty' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-600 dark:text-slate-300 hover:text-slate-900'
          }`}
        >
          <UserCheck className="w-4 h-4" /> Faculty Dossiers ({computedFacultyCount})
        </button>

        <button
          onClick={() => { setActiveTab('rooms'); setEntitySearch(''); }}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
            activeTab === 'rooms' ? 'bg-purple-600 text-white shadow-md' : 'text-slate-600 dark:text-slate-300 hover:text-slate-900'
          }`}
        >
          <Building2 className="w-4 h-4" /> Venues Report ({computedRoomsCount})
        </button>

        <button
          onClick={() => { setActiveTab('subjects'); setEntitySearch(''); }}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
            activeTab === 'subjects' ? 'bg-emerald-600 text-white shadow-md' : 'text-slate-600 dark:text-slate-300 hover:text-slate-900'
          }`}
        >
          <BookOpen className="w-4 h-4" /> Subjects Report ({computedSubjectsCount})
        </button>
      </div>

      {/* TAB 1: CONFLICT LOG */}
      {activeTab === 'clashes' && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-1.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-1.5 text-xs">
                <Calendar className="w-3.5 h-3.5 text-slate-500" />
                <span className="font-semibold text-slate-600 dark:text-slate-300">Day:</span>
                <select
                  value={selectedDay}
                  onChange={(e) => setSelectedDay(e.target.value)}
                  className="bg-transparent font-bold text-slate-900 dark:text-white focus:outline-none cursor-pointer"
                >
                  <option value="ALL">All Days</option>
                  <option value="MON">Monday</option>
                  <option value="TUE">Tuesday</option>
                  <option value="WED">Wednesday</option>
                  <option value="THU">Thursday</option>
                  <option value="FRI">Friday</option>
                  <option value="SAT">Saturday</option>
                </select>
              </div>

              <div className="flex items-center gap-1.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-1.5 text-xs">
                <Filter className="w-3.5 h-3.5 text-slate-500" />
                <span className="font-semibold text-slate-600 dark:text-slate-300">Period:</span>
                <select
                  value={selectedPeriod}
                  onChange={(e) => setSelectedPeriod(e.target.value)}
                  className="bg-transparent font-bold text-slate-900 dark:text-white focus:outline-none cursor-pointer"
                >
                  <option value="ALL">All Periods</option>
                  {[1, 2, 3, 4, 5, 6, 7, 8].map((p) => (
                    <option key={p} value={String(p)}>Period {p}</option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-1.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-1.5 text-xs">
                <span className="font-semibold text-slate-600 dark:text-slate-300">Type:</span>
                <select
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value)}
                  className="bg-transparent font-bold text-slate-900 dark:text-white focus:outline-none cursor-pointer"
                >
                  <option value="ALL">All Conflict Types</option>
                  <option value="ROOM">Room Conflict</option>
                  <option value="FACULTY">Faculty Conflict</option>
                </select>
              </div>
            </div>

            <div className="relative flex-1 max-w-xs">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search room, section, or subject..."
                value={clashSearchQuery}
                onChange={(e) => setClashSearchQuery(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white rounded-xl pl-9 pr-4 py-1.5 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
            </div>
          </div>

          <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 px-1">
            <span>
              Showing <strong className="text-slate-900 dark:text-white font-bold">{filteredClashes.length}</strong> of{' '}
              <strong className="text-slate-900 dark:text-white font-bold">{clashDetails.length}</strong> conflicts detected
            </span>
          </div>

          <div className="space-y-3">
            {filteredClashes.length === 0 ? (
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-12 text-center text-slate-500">
                <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
                <div className="font-bold text-slate-800 dark:text-slate-200 text-sm">No conflicts match filter criteria</div>
                <div className="text-xs text-slate-400 mt-1">If overall conflicts are 0, this dataset is valid!</div>
              </div>
            ) : (
              filteredClashes.map((clash, idx) => (
                <div
                  key={idx}
                  role="alert"
                  className="bg-white dark:bg-slate-900 border border-red-200 dark:border-red-900/60 border-l-4 border-l-red-600 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="px-2 py-0.5 bg-red-100 dark:bg-red-950/80 text-red-800 dark:text-red-300 text-[11px] font-bold rounded">
                        {clash.day} Period-{clash.period}
                      </span>
                      {clash.room && (
                        <span className="inline-flex items-center gap-1 text-xs font-semibold text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded">
                          <Building2 className="w-3 h-3 text-slate-500" /> Room {clash.room}
                        </span>
                      )}
                      <span className="text-xs font-bold text-red-600 dark:text-red-400">{clash.clash_type} COLLISION</span>
                    </div>
                    <div className="text-sm font-semibold text-slate-900 dark:text-white pt-1">{clash.message}</div>
                  </div>

                  <div className="flex items-center gap-3 bg-red-50/70 dark:bg-red-950/40 p-3 rounded-lg border border-red-100 dark:border-red-900/50 shrink-0 text-xs">
                    <div className="text-center">
                      <div className="font-bold text-slate-900 dark:text-white">{clash.section_a}</div>
                      <div className="text-slate-500 dark:text-slate-400">{clash.subject_a}</div>
                    </div>
                    <div className="font-extrabold text-red-500 px-1">VS</div>
                    <div className="text-center">
                      <div className="font-bold text-slate-900 dark:text-white">{clash.section_b}</div>
                      <div className="text-slate-500 dark:text-slate-400">{clash.subject_b}</div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* TAB 2: SECTIONS AUDIT REPORT */}
      {activeTab === 'sections' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search section name or class teacher..."
                value={entitySearch}
                onChange={(e) => setEntitySearch(e.target.value)}
                className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
            </div>
            <span className="text-xs text-slate-500 font-semibold">
              Showing {filteredSections.length} of {sectionsReport.length} sections
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredSections.map((sec, idx) => (
              <div key={idx} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm space-y-3">
                <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
                  <span className="font-extrabold text-sm text-slate-900 dark:text-white">{sec.name}</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${sec.has_clash ? "bg-red-100 text-red-700 border border-red-200" : "bg-emerald-100 text-emerald-700 border border-emerald-200"}`}>
                    {sec.has_clash ? "⚠️ Has Conflict" : "✓ 0 Clashes"}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="bg-blue-50 dark:bg-blue-950/60 p-2 rounded-lg">
                    <span className="text-[10px] text-blue-700 dark:text-blue-300 block font-bold">Lecture</span>
                    <strong className="text-blue-950 dark:text-blue-100 font-extrabold">{sec.lecture_slots || 0} slots</strong>
                  </div>
                  <div className="bg-purple-50 dark:bg-purple-950/60 p-2 rounded-lg">
                    <span className="text-[10px] text-purple-700 dark:text-purple-300 block font-bold">Lab / Prac</span>
                    <strong className="text-purple-950 dark:text-purple-100 font-extrabold">{sec.lab_slots || 0} slots</strong>
                  </div>
                  <div className="bg-amber-50 dark:bg-amber-950/60 p-2 rounded-lg">
                    <span className="text-[10px] text-amber-700 dark:text-amber-300 block font-bold">Tutorial</span>
                    <strong className="text-amber-950 dark:text-amber-100 font-extrabold">{sec.tutorial_slots || 0} slots</strong>
                  </div>
                </div>

                {sec.class_teacher && (
                  <div className="text-xs text-slate-600 dark:text-slate-400">
                    <span className="font-semibold text-slate-800 dark:text-slate-200">Class Teacher:</span> {sec.class_teacher}
                  </div>
                )}

                <div className="space-y-1 text-xs text-slate-500">
                  <div>
                    <span className="font-semibold text-slate-700 dark:text-slate-300">Assigned Rooms:</span>{" "}
                    {(sec.rooms || []).join(", ") || "None"}
                  </div>
                  <div>
                    <span className="font-semibold text-slate-700 dark:text-slate-300">Subjects Mapped:</span>{" "}
                    {(sec.subjects || []).join(", ") || "None"}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: FACULTY DOSSIERS REPORT */}
      {activeTab === 'faculty' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search faculty name or assigned section..."
                value={entitySearch}
                onChange={(e) => setEntitySearch(e.target.value)}
                className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
              />
            </div>
            <span className="text-xs text-slate-500 font-semibold">
              Showing {filteredFaculty.length} of {facultyReport.length} faculty dossiers
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredFaculty.map((fac, idx) => (
              <div key={idx} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm space-y-3">
                {/* Faculty Header */}
                <div className="flex items-start justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
                  <div>
                    <div className="font-extrabold text-sm text-slate-900 dark:text-white" title={fac.name}>{fac.name}</div>
                    <div className="text-[11px] text-slate-400 mt-0.5">{fac.sections_count} section{fac.sections_count !== 1 ? 's' : ''} · {(fac.subjects || []).length} subject{(fac.subjects || []).length !== 1 ? 's' : ''}</div>
                  </div>
                  <div className="flex flex-col items-end gap-1 shrink-0">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${fac.has_clash ? "bg-red-100 dark:bg-red-950/70 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800" : "bg-indigo-100 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"}`}>
                      {fac.has_clash ? '⚠️ Has Clash' : `${fac.total_hours} hrs/wk`}
                    </span>
                  </div>
                </div>

                {/* Workload bar */}
                <div className="space-y-1">
                  <div className="flex justify-between text-[10px] text-slate-500">
                    <span className="font-semibold">Weekly Workload</span>
                    <span>{fac.total_hours} / 16 hrs</span>
                  </div>
                  <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        fac.total_hours >= 16 ? 'bg-red-500' :
                        fac.total_hours >= 12 ? 'bg-amber-500' : 'bg-indigo-500'
                      }`}
                      style={{ width: `${Math.min(100, Math.round((fac.total_hours / 16) * 100))}%` }}
                    />
                  </div>
                </div>

                {/* Subjects taught */}
                <div>
                  <div className="text-[11px] font-bold text-slate-700 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Subjects Taught</div>
                  <div className="flex flex-wrap gap-1">
                    {(fac.subjects || []).length > 0 ? (
                      (fac.subjects || []).map((subj: string, i: number) => (
                        <span key={i} className="px-2 py-0.5 bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-100 dark:border-blue-800 rounded-full text-[11px] font-semibold">
                          {subj}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-400 italic">No subjects</span>
                    )}
                  </div>
                </div>

                {/* Sections assigned */}
                <div>
                  <div className="text-[11px] font-bold text-slate-700 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Sections Assigned</div>
                  <div className="flex flex-wrap gap-1">
                    {(fac.sections || []).length > 0 ? (
                      (fac.sections || []).map((sec: string, i: number) => (
                        <span key={i} className="px-2 py-0.5 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 rounded text-[11px] font-medium">
                          {sec}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-400 italic">No sections</span>
                    )}
                  </div>
                </div>

                {/* Venues assigned */}
                {(fac.rooms || []).length > 0 && (
                  <div>
                    <div className="text-[11px] font-bold text-slate-700 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Venues Used</div>
                    <div className="flex flex-wrap gap-1">
                      {(fac.rooms || []).map((rm: string, i: number) => (
                        <span key={i} className="px-2 py-0.5 bg-purple-50 dark:bg-purple-950/60 text-purple-700 dark:text-purple-300 border border-purple-100 dark:border-purple-800 rounded text-[11px] font-medium">
                          {rm}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 4: VENUES & ROOMS REPORT */}
      {activeTab === 'rooms' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search venue room code..."
                value={entitySearch}
                onChange={(e) => setEntitySearch(e.target.value)}
                className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-purple-500/20"
              />
            </div>
            <span className="text-xs text-slate-500 font-semibold">
              Showing {filteredRooms.length} of {roomsReport.length} venue rooms
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {filteredRooms.map((rm, idx) => (
              <div key={idx} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm space-y-2">
                <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
                  <span className="font-extrabold text-sm text-slate-900 dark:text-white">Room {rm.code}</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${rm.has_clash ? "bg-red-100 text-red-700" : "bg-purple-50 text-purple-700 dark:bg-purple-950 dark:text-purple-300"}`}>
                    {rm.has_clash ? "⚠️ Clash" : `${rm.occupancy_rate}% Occupied`}
                  </span>
                </div>

                <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${rm.has_clash ? "bg-red-500" : "bg-purple-600"}`}
                    style={{ width: `${rm.occupancy_rate}%` }}
                  />
                </div>

                <div className="text-xs text-slate-500 space-y-1">
                  <div className="flex justify-between">
                    <span>Weekly Slots:</span>
                    <strong className="text-slate-800 dark:text-slate-200">{rm.total_slots} / 48</strong>
                  </div>
                  <div>
                    <span className="font-semibold text-slate-700 dark:text-slate-300">Sections:</span>{" "}
                    {(rm.sections || []).join(", ")}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 5: SUBJECTS REPORT */}
      {activeTab === 'subjects' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search subject code..."
                value={entitySearch}
                onChange={(e) => setEntitySearch(e.target.value)}
                className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
              />
            </div>
            <span className="text-xs text-slate-500 font-semibold">
              Showing {filteredSubjects.length} of {subjectsReport.length} subjects
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredSubjects.map((sub, idx) => (
              <div key={idx} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm space-y-3">
                {/* Subject Header */}
                <div className="flex items-start justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
                  <div>
                    <div className="font-extrabold text-sm text-slate-900 dark:text-white">{sub.code}</div>
                    <div className="text-[11px] text-slate-400 mt-0.5">{sub.total_slots} slots/wk · {sub.sections_count} section{sub.sections_count !== 1 ? 's' : ''} · {sub.faculty_count} faculty</div>
                  </div>
                  <span className={`shrink-0 px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                    sub.type === "P" || sub.type === "T&P"
                      ? "bg-purple-100 text-purple-700 dark:bg-purple-950/70 dark:text-purple-300 border border-purple-200 dark:border-purple-800"
                      : sub.type === "T"
                      ? "bg-amber-100 text-amber-700 dark:bg-amber-950/70 dark:text-amber-300 border border-amber-200 dark:border-amber-800"
                      : "bg-blue-100 text-blue-700 dark:bg-blue-950/70 dark:text-blue-300 border border-blue-200 dark:border-blue-800"
                  }`}>
                    {sub.type === "P" || sub.type === "T&P" ? "Practical Lab" : sub.type === "T" ? "Tutorial" : "Lecture"}
                  </span>
                </div>

                {/* Teaching Faculty */}
                <div>
                  <div className="text-[11px] font-bold text-slate-700 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Teaching Faculty</div>
                  <div className="flex flex-wrap gap-1">
                    {(sub.faculty || []).length > 0 ? (
                      (sub.faculty || []).map((f: string, i: number) => (
                        <span key={i} className="px-2 py-0.5 bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-100 dark:border-indigo-800 rounded-full text-[11px] font-medium">
                          {f}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-400 italic">No faculty mapped</span>
                    )}
                  </div>
                </div>

                {/* Sections enrolled */}
                <div>
                  <div className="text-[11px] font-bold text-slate-700 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Sections Enrolled</div>
                  <div className="flex flex-wrap gap-1">
                    {(sub.sections || []).length > 0 ? (
                      (sub.sections || []).map((sec: string, i: number) => (
                        <span key={i} className="px-2 py-0.5 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 rounded text-[11px] font-medium">
                          {sec}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-400 italic">No sections</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

