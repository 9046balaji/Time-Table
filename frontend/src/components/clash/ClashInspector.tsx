'use client';

import React, { useState, useMemo } from 'react';
import { AlertTriangle, Filter, Search, ShieldAlert, Building2, UserCheck, Calendar } from 'lucide-react';
import { ClashDetail } from '@/lib/types';

interface ClashInspectorProps {
  filename: string;
  totalSections: number;
  totalSlots: number;
  hardViolations: number;
  roomClashes: number;
  facultyClashes: number;
  clashDetails: ClashDetail[];
}

export function ClashInspector({
  filename,
  totalSections,
  totalSlots,
  hardViolations,
  roomClashes,
  facultyClashes,
  clashDetails,
}: ClashInspectorProps) {
  const [selectedDay, setSelectedDay] = useState<string>('ALL');
  const [selectedPeriod, setSelectedPeriod] = useState<string>('ALL');
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const filteredClashes = useMemo(() => {
    return clashDetails.filter((clash) => {
      if (selectedDay !== 'ALL' && clash.day.toUpperCase() !== selectedDay) return false;
      if (selectedPeriod !== 'ALL' && String(clash.period) !== selectedPeriod) return false;
      if (selectedType !== 'ALL' && clash.clash_type !== selectedType) return false;
      if (searchQuery.trim() !== '') {
        const query = searchQuery.toLowerCase();
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
  }, [clashDetails, selectedDay, selectedPeriod, selectedType, searchQuery]);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-red-900 via-slate-900 to-red-950 text-white rounded-2xl p-6 shadow-lg border border-red-800/40">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-red-600 rounded-xl text-white shadow-md">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold">Interactive Conflict Inspector</h2>
              <p className="text-xs text-red-200">Inspecting file: {filename}</p>
            </div>
          </div>
          <div className="text-right">
            <span className="px-3 py-1 bg-red-600 text-white text-xs font-bold rounded-full">
              {hardViolations} HARD CLASHES
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 pt-4 border-t border-red-800/50 text-xs">
          <div>
            <span className="text-red-300">Sections Parsed:</span> <strong className="text-white font-bold">{totalSections}</strong>
          </div>
          <div>
            <span className="text-red-300">Scheduled Slots:</span> <strong className="text-white font-bold">{totalSlots}</strong>
          </div>
          <div>
            <span className="text-red-300">Room Conflicts:</span> <strong className="text-white font-bold">{roomClashes}</strong>
          </div>
          <div>
            <span className="text-red-300">Faculty Conflicts:</span> <strong className="text-white font-bold">{facultyClashes}</strong>
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          {/* Day Filter */}
          <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 text-xs">
            <Calendar className="w-3.5 h-3.5 text-slate-500" />
            <span className="font-semibold text-slate-600">Day:</span>
            <select
              value={selectedDay}
              onChange={(e) => setSelectedDay(e.target.value)}
              className="bg-transparent font-bold text-slate-900 focus:outline-none cursor-pointer"
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

          {/* Period Filter */}
          <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 text-xs">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            <span className="font-semibold text-slate-600">Period:</span>
            <select
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(e.target.value)}
              className="bg-transparent font-bold text-slate-900 focus:outline-none cursor-pointer"
            >
              <option value="ALL">All Periods</option>
              {[1, 2, 3, 4, 5, 6, 7, 8].map((p) => (
                <option key={p} value={String(p)}>
                  Period {p}
                </option>
              ))}
            </select>
          </div>

          {/* Type Filter */}
          <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 text-xs">
            <span className="font-semibold text-slate-600">Type:</span>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="bg-transparent font-bold text-slate-900 focus:outline-none cursor-pointer"
            >
              <option value="ALL">All Types</option>
              <option value="ROOM">Room Conflict</option>
              <option value="FACULTY">Faculty Conflict</option>
            </select>
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative flex-1 max-w-xs">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search room, section, or subject..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-9 pr-4 py-1.5 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Results Count Bar */}
      <div className="flex items-center justify-between text-xs text-slate-500 px-1">
        <span>
          Showing <strong className="text-slate-900">{filteredClashes.length}</strong> of{' '}
          <strong className="text-slate-900">{clashDetails.length}</strong> conflicts detected
        </span>
        {(selectedDay !== 'ALL' || selectedPeriod !== 'ALL' || selectedType !== 'ALL' || searchQuery !== '') && (
          <button
            onClick={() => {
              setSelectedDay('ALL');
              setSelectedPeriod('ALL');
              setSelectedType('ALL');
              setSearchQuery('');
            }}
            className="text-blue-600 font-semibold hover:underline"
          >
            Reset Filters
          </button>
        )}
      </div>

      {/* Clash Cards Grid */}
      <div className="space-y-3">
        {filteredClashes.length === 0 ? (
          <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center text-slate-500">
            <AlertTriangle className="w-10 h-10 text-slate-300 mx-auto mb-2" />
            <div className="font-bold text-slate-700 text-sm">No conflicts match filter criteria</div>
            <div className="text-xs text-slate-400 mt-1">Try resetting filters or adjusting search terms</div>
          </div>
        ) : (
          filteredClashes.map((clash, idx) => (
            <div
              key={idx}
              role="alert"
              className="bg-white border border-red-200 border-l-4 border-l-red-600 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 bg-red-100 text-red-800 text-[11px] font-bold rounded">
                    {clash.day} Period-{clash.period}
                  </span>
                  {clash.room && (
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-slate-700 bg-slate-100 px-2 py-0.5 rounded">
                      <Building2 className="w-3 h-3 text-slate-500" /> Room {clash.room}
                    </span>
                  )}
                  <span className="text-xs font-bold text-red-600">{clash.clash_type} COLLISION</span>
                </div>

                <div className="text-sm font-semibold text-slate-900 pt-1">{clash.message}</div>
              </div>

              <div className="flex items-center gap-3 bg-red-50/70 p-3 rounded-lg border border-red-100 shrink-0 text-xs">
                <div className="text-center">
                  <div className="font-bold text-slate-900">{clash.section_a}</div>
                  <div className="text-slate-500">{clash.subject_a}</div>
                </div>
                <div className="font-extrabold text-red-500 px-1">VS</div>
                <div className="text-center">
                  <div className="font-bold text-slate-900">{clash.section_b}</div>
                  <div className="text-slate-500">{clash.subject_b}</div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
