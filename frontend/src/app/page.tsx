'use client';

import React from 'react';
import Link from 'next/link';
import {
  Users,
  GraduationCap,
  Building2,
  Calendar,
  AlertTriangle,
  ArrowRight,
  Upload,
  Bot,
  Settings,
  Download,
  History
} from 'lucide-react';

export default function DashboardPage() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-blue-900 via-indigo-900 to-purple-900 text-white rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/10 backdrop-blur border border-white/20 rounded-full text-xs font-semibold mb-3 text-blue-200">
            <span>VFSTR ACSE Department</span>
            <span>•</span>
            <span>AY 2026-27 Semester I</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight mb-2">Automated Timetable Generation & Optimization</h1>
          <p className="text-blue-200 text-sm max-w-2xl">
            Constraint satisfaction engine replacing manual Excel scheduling. Eliminates room overlaps, faculty double-bookings, and enforces AICTE workload policies.
          </p>
        </div>
      </div>

      {/* KPI Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard label="Total Sections" value="44" subtext="Across AIML, CS, DS, CSBS, IOT" icon={<Users className="w-5 h-5 text-blue-600" />} />
        <StatCard label="Faculty Members" value="80+" subtext="AICTE Workload Rules Enforced" icon={<GraduationCap className="w-5 h-5 text-purple-600" />} />
        <StatCard label="Available Rooms" value="35" subtext="Classrooms & High-GPU Labs" icon={<Building2 className="w-5 h-5 text-emerald-600" />} />
        <StatCard label="Weekly Slots" value="1,000" subtext="48 Slots / Section / Week" icon={<Calendar className="w-5 h-5 text-amber-600" />} />
      </div>

      {/* Main Grid: Clash Summary & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Clash Summary Card */}
        <div className="lg:col-span-2 bg-red-50/70 border border-red-200 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-red-600 text-white rounded-xl shadow-md">
                  <AlertTriangle className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="font-bold text-lg text-slate-900">V5 Baseline Violation Report</h3>
                  <p className="text-xs text-slate-600">Generated from ACSE_TIMETABLE_V5.xlsx</p>
                </div>
              </div>
              <span className="px-3 py-1 bg-red-600 text-white text-xs font-bold rounded-full">
                NEEDS_FIX
              </span>
            </div>

            <div className="bg-white rounded-xl p-4 border border-red-100 mb-4 shadow-sm flex items-center justify-between">
              <div>
                <div className="text-3xl font-extrabold text-red-600">51</div>
                <div className="text-xs font-medium text-slate-500">Room Conflicts Detected</div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-emerald-600">0</div>
                <div className="text-xs font-medium text-slate-500">Faculty Double-Bookings</div>
              </div>
            </div>

            <div className="space-y-2 text-xs text-slate-700 mb-6">
              <div className="font-semibold text-slate-900">Critical Sample Violations in V5:</div>
              <ul className="space-y-1.5 list-disc pl-4 text-slate-600">
                <li><span className="font-mono bg-red-100 text-red-800 px-1 rounded">WED P-1</span> Room 606 → II AIML-E: OOPS(P) AND II CSBS: DS(P)</li>
                <li><span className="font-mono bg-red-100 text-red-800 px-1 rounded">FRI P-6</span> Room 616 → II AIML-F: AI(P) AND II BS(DS): DHV</li>
                <li><span className="font-mono bg-red-100 text-red-800 px-1 rounded">MON P-1</span> Room AFTF-12 → III AIML-F: FIP(P) AND II MSC(DS): FIP(P)</li>
              </ul>
            </div>
          </div>

          <div className="flex gap-3">
            <Link
              href="/schedule"
              className="flex-1 inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2.5 rounded-xl text-sm transition-colors shadow-md"
            >
              <Bot className="w-4 h-4" />
              Run CP-SAT Solver to Resolve
            </Link>
            <Link
              href="/import"
              className="inline-flex items-center justify-center gap-2 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-medium px-4 py-2.5 rounded-xl text-sm transition-colors"
            >
              View Full Report
            </Link>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="font-bold text-slate-900 mb-1">Quick Actions</h3>
            <p className="text-xs text-slate-500 mb-4">Common timetable workflows</p>

            <div className="space-y-3">
              <QuickActionButton href="/import" icon={<Upload className="w-4 h-4 text-blue-600" />} title="Import Excel" desc="Upload new XLSX revision" />
              <QuickActionButton href="/schedule" icon={<Bot className="w-4 h-4 text-purple-600" />} title="Run Solver" desc="Execute OR-Tools CP-SAT" highlight />
              <QuickActionButton href="/configure" icon={<Settings className="w-4 h-4 text-slate-600" />} title="Configure Data" desc="Faculty, Rooms, & Subjects" />
              <QuickActionButton href="/export" icon={<Download className="w-4 h-4 text-emerald-600" />} title="Export Timetable" desc="Generate Excel / PDF tabs" />
            </div>
          </div>
        </div>
      </div>

      {/* Version History Timeline */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <History className="w-5 h-5 text-slate-700" />
            <h3 className="font-bold text-slate-900">Timetable Revision History (V1 → V6 AUTO)</h3>
          </div>
          <span className="text-xs text-slate-500">Target: V6 AUTO with 0 clashes</span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
          <VersionCard label="V1" date="10 Jul" violations={67} />
          <VersionCard label="V2" date="11 Jul" violations={58} />
          <VersionCard label="V3" date="13 Jul" violations={51} />
          <VersionCard label="V4" date="14 Jul" violations={51} />
          <VersionCard label="V5" date="15 Jul" violations={51} current />
          <VersionCard label="V6 AUTO" date="Pending" violations={0} pending />
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, subtext, icon }: { label: string; value: string; subtext: string; icon: React.ReactNode }) {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{label}</span>
        <div className="p-2 bg-slate-50 rounded-xl border border-slate-100">{icon}</div>
      </div>
      <div className="text-3xl font-extrabold text-slate-900 mb-1">{value}</div>
      <div className="text-xs text-slate-500">{subtext}</div>
    </div>
  );
}

function QuickActionButton({ href, icon, title, desc, highlight }: { href: string; icon: React.ReactNode; title: string; desc: string; highlight?: boolean }) {
  return (
    <Link
      href={href}
      className={`flex items-center justify-between p-3 rounded-xl border transition-all ${
        highlight
          ? 'bg-purple-50/70 border-purple-200 hover:bg-purple-100/70'
          : 'bg-slate-50/70 border-slate-200 hover:bg-slate-100/70'
      }`}
    >
      <div className="flex items-center gap-3">
        <div className="p-2 bg-white rounded-lg shadow-sm">{icon}</div>
        <div>
          <div className="text-sm font-semibold text-slate-900">{title}</div>
          <div className="text-xs text-slate-500">{desc}</div>
        </div>
      </div>
      <ArrowRight className="w-4 h-4 text-slate-400" />
    </Link>
  );
}

function VersionCard({ label, date, violations, current, pending }: { label: string; date: string; violations: number; current?: boolean; pending?: boolean }) {
  return (
    <div
      className={`p-4 rounded-xl border flex flex-col justify-between text-center transition-all ${
        current
          ? 'bg-blue-50 border-blue-300 ring-2 ring-blue-500/20'
          : pending
          ? 'bg-purple-50 border-purple-200 border-dashed'
          : 'bg-slate-50 border-slate-200'
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="font-bold text-sm text-slate-900">{label}</span>
        {current && <span className="text-[10px] font-bold bg-blue-600 text-white px-1.5 py-0.5 rounded">Active</span>}
        {pending && <span className="text-[10px] font-bold bg-purple-600 text-white px-1.5 py-0.5 rounded">Target</span>}
      </div>

      <div className="my-2">
        <div className={`text-xl font-extrabold ${pending ? 'text-purple-600' : violations > 0 ? 'text-red-600' : 'text-emerald-600'}`}>
          {violations}
        </div>
        <div className="text-[11px] text-slate-500">hard clashes</div>
      </div>

      <div className="text-[11px] text-slate-400 border-t border-slate-200/60 pt-2">{date}</div>
    </div>
  );
}
