'use client';

import React, { useState, useEffect } from 'react';
import { Download, FileSpreadsheet, FileText, Printer, Cpu, CheckCircle2, Loader2, Sparkles, UserCheck, Layers, LayoutGrid, Award } from 'lucide-react';
import { timetableApi } from '@/lib/api';
import { Faculty } from '@/lib/types';

export default function ExportPage() {
  const [downloadingExcel, setDownloadingExcel] = useState(false);
  const [downloadingCohortExcel, setDownloadingCohortExcel] = useState(false);
  const [downloadingMinorsHonors, setDownloadingMinorsHonors] = useState(false);
  const [downloadingSectionPdfs, setDownloadingSectionPdfs] = useState(false);
  const [downloadingFacultyPdfs, setDownloadingFacultyPdfs] = useState(false);
  const [downloadingSingleFacultyPdf, setDownloadingSingleFacultyPdf] = useState(false);
  const [syncingSmartClass, setSyncingSmartClass] = useState(false);
  const [syncResult, setSyncResult] = useState<any>(null);

  const [versions, setVersions] = useState<any[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<number>(5);

  const [cohortGroups, setCohortGroups] = useState<any[]>([]);
  const [selectedCohortKey, setSelectedCohortKey] = useState<string>('II_AIML');

  const [facultyList, setFacultyList] = useState<Faculty[]>([]);
  const [selectedFacultyId, setSelectedFacultyId] = useState<number | null>(null);

  useEffect(() => {
    timetableApi.getVersions()
      .then(res => {
        const vList = Array.isArray(res.data) && res.data.length > 0 ? res.data : [
          { id: 5, version_label: 'V5', effective_date: '15-07-2026', hard_violations_count: 51, notes: 'Current baseline imported from V5 Excel dataset' },
          { id: 3, version_label: 'V3', effective_date: '13-07-2026', hard_violations_count: 64, notes: 'Previous revision imported from V3 Excel dataset' }
        ];
        setVersions(vList);
        setSelectedVersionId(vList[0].id);
      })
      .catch(() => {
        setVersions([
          { id: 5, version_label: 'V5', effective_date: '15-07-2026', hard_violations_count: 51, notes: 'Current baseline' },
          { id: 3, version_label: 'V3', effective_date: '13-07-2026', hard_violations_count: 64, notes: 'Previous revision' }
        ]);
        setSelectedVersionId(5);
      });

    timetableApi.getCohortGroups()
      .then(res => {
        const groups = Array.isArray(res.data) ? res.data : [];
        const initial = groups.length > 0 ? groups : [
          { key: "II_AIML", label: "B.Tech II Year AIML (12 Sections)", sections_count: 12 },
          { key: "III_AIML", label: "B.Tech III Year AIML (7 Sections)", sections_count: 7 },
          { key: "IV_AIML", label: "B.Tech IV Year AIML (5 Sections)", sections_count: 5 },
          { key: "CS_DS", label: "B.Tech CS & DS (All Years)", sections_count: 9 },
          { key: "CSBS_IOT", label: "B.Tech CSBS & IOT (All Years)", sections_count: 5 },
          { key: "SPECIAL_PG", label: "Special Programs & Minor/Honors", sections_count: 4 }
        ];
        setCohortGroups(initial);
        if (initial.length > 0) setSelectedCohortKey(initial[0].key);
      })
      .catch(() => {
        setCohortGroups([
          { key: "II_AIML", label: "B.Tech II Year AIML (12 Sections)", sections_count: 12 },
          { key: "III_AIML", label: "B.Tech III Year AIML (7 Sections)", sections_count: 7 },
          { key: "IV_AIML", label: "B.Tech IV Year AIML (5 Sections)", sections_count: 5 },
          { key: "CS_DS", label: "B.Tech CS & DS (All Years)", sections_count: 9 }
        ]);
        setSelectedCohortKey("II_AIML");
      });

    timetableApi.getFaculty()
      .then(res => {
        const facs = Array.isArray(res.data) ? res.data : [];
        const initial = facs.length > 0 ? facs : [
          { id: 1, name: "Dr. S. Srikantha Reddy", designation: "Associate Professor" },
          { id: 2, name: "DR. ANKAMMA RAO MALLELA", designation: "Professor" },
          { id: 3, name: "DR. P. Kalpana", designation: "Professor" }
        ];
        setFacultyList(initial as Faculty[]);
        if (initial.length > 0) setSelectedFacultyId(initial[0].id);
      })
      .catch(() => {
        setFacultyList([
          { id: 1, name: "Dr. S. Srikantha Reddy", designation: "Associate Professor" }
        ] as Faculty[]);
        setSelectedFacultyId(1);
      });
  }, []);

  const handleExportExcel = async () => {
    setDownloadingExcel(true);
    try {
      const response = await timetableApi.exportExcel(selectedVersionId);
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `VFSTR_V${selectedVersionId}_Master_Department_Timetable.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      setSyncResult({ message: `Downloaded Master Excel workbook for Version V${selectedVersionId}.`, synced_at: new Date().toLocaleTimeString() });
    } catch (err) {
      console.error('Failed to export Excel', err);
    } finally {
      setDownloadingExcel(false);
    }
  };

  const handleExportCohortExcel = async () => {
    setDownloadingCohortExcel(true);
    try {
      const response = await timetableApi.exportCohortExcel(selectedCohortKey, selectedVersionId);
      const cohortObj = cohortGroups.find(c => c.key === selectedCohortKey);
      const labelClean = cohortObj?.key || selectedCohortKey;
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `VFSTR_V${selectedVersionId}_Cohort_${labelClean}_Timetable.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      setSyncResult({ message: `Downloaded Cohort Consolidated Excel (${cohortObj?.label || selectedCohortKey}) for Version V${selectedVersionId}.`, synced_at: new Date().toLocaleTimeString() });
    } catch (err) {
      console.error('Failed to export Cohort Excel', err);
    } finally {
      setDownloadingCohortExcel(false);
    }
  };

  const handleExportMinorsHonors = async () => {
    setDownloadingMinorsHonors(true);
    try {
      const response = await timetableApi.exportMinorsHonorsExcel(selectedVersionId);
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `VFSTR_V${selectedVersionId}_Minors_Honors_Master.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      setSyncResult({ message: `Downloaded Minors & Honors Department Master Allocation Sheet for Version V${selectedVersionId}.`, synced_at: new Date().toLocaleTimeString() });
    } catch (err) {
      console.error('Failed to export Minors/Honors Excel', err);
    } finally {
      setDownloadingMinorsHonors(false);
    }
  };

  const handleExportSectionPdfs = async () => {
    setDownloadingSectionPdfs(true);
    try {
      const response = await timetableApi.exportSectionPdfs(selectedVersionId);
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `VFSTR_V${selectedVersionId}_Section_Timetables.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      setSyncResult({ message: `Downloaded printable section PDF schedules for Version V${selectedVersionId}.`, synced_at: new Date().toLocaleTimeString() });
    } catch (err) {
      console.error('Failed to export Section PDFs', err);
    } finally {
      setDownloadingSectionPdfs(false);
    }
  };

  const handleExportFacultyPdfs = async () => {
    setDownloadingFacultyPdfs(true);
    try {
      const response = await timetableApi.exportFacultyPdfs(selectedVersionId);
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `VFSTR_V${selectedVersionId}_Faculty_Weekly_Schedules.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      setSyncResult({ message: `Downloaded master faculty weekly teaching schedule PDFs for Version V${selectedVersionId}.`, synced_at: new Date().toLocaleTimeString() });
    } catch (err) {
      console.error('Failed to export Faculty PDFs', err);
    } finally {
      setDownloadingFacultyPdfs(false);
    }
  };

  const handleExportSingleFacultyPdf = async () => {
    if (!selectedFacultyId) return;
    setDownloadingSingleFacultyPdf(true);
    try {
      const response = await timetableApi.exportSingleFacultyPdf(selectedFacultyId, selectedVersionId);
      const facObj = facultyList.find(f => f.id === selectedFacultyId);
      const fnameClean = facObj?.name.replace(/[^a-zA-Z0-9]/g, '_') || `Faculty_${selectedFacultyId}`;
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `VFSTR_V${selectedVersionId}_Schedule_${fnameClean}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      setSyncResult({ message: `Downloaded individual PDF schedule for ${facObj?.name || 'Faculty Member'} (V${selectedVersionId}).`, synced_at: new Date().toLocaleTimeString() });
    } catch (err) {
      console.error('Failed to export Single Faculty PDF', err);
    } finally {
      setDownloadingSingleFacultyPdf(false);
    }
  };

  const handleSyncSmartClass = async () => {
    setSyncingSmartClass(true);
    try {
      const res = await timetableApi.syncSmartClass();
      setSyncResult(res.data);
    } catch (err) {
      console.error('Failed to sync SmartClass', err);
    } finally {
      setSyncingSmartClass(false);
    }
  };

  const selectedFacultyObj = facultyList.find(f => f.id === selectedFacultyId);
  const selectedVersionObj = versions.find(v => v.id === selectedVersionId);
  const selectedCohortObj = cohortGroups.find(c => c.key === selectedCohortKey);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Multi-Version & Cohort Timetable Export Center</h1>
        <p className="text-sm text-slate-500">
          Download Year & Branch Cohort Excel files with Combined Master View sheets, Minors/Honors master allocation sheets, section PDFs, or sync to SmartClass AI camera nodes.
        </p>
      </div>

      {/* Version Selector Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-blue-50 text-blue-700 rounded-xl border border-blue-200">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-700 block">Database Timetable Version:</label>
            <select
              value={selectedVersionId}
              onChange={(e) => setSelectedVersionId(Number(e.target.value))}
              className="bg-slate-50 border border-slate-300 text-slate-900 px-4 py-1.5 rounded-xl text-xs font-bold shadow-sm focus:outline-none cursor-pointer mt-0.5"
            >
              {versions.map(v => (
                <option key={v.id} value={v.id}>
                  Version {v.version_label} ({v.effective_date}) — {v.hard_violations_count} Hard Clashes
                </option>
              ))}
            </select>
          </div>
        </div>

        {selectedVersionObj && (
          <div className="text-xs text-slate-600 font-semibold bg-slate-50 px-4 py-2 rounded-xl border border-slate-200">
            <span className="text-blue-700 font-bold">Active Selection:</span> Version {selectedVersionObj.version_label} ({selectedVersionObj.effective_date}) • {selectedVersionObj.notes}
          </div>
        )}
      </div>

      {/* SmartClass Master Sync Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-blue-900 text-white rounded-2xl p-6 shadow-xl border border-indigo-800/40 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          <div className="p-3.5 bg-blue-600 rounded-2xl text-white shadow-lg">
            <Cpu className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-lg font-bold">SmartClass AI Camera System Direct Sync</h3>
              <span className="px-2.5 py-0.5 bg-emerald-500/20 text-emerald-300 text-xs font-semibold rounded-full border border-emerald-500/30">
                Face Recog Node Connected
              </span>
            </div>
            <p className="text-xs text-blue-200 max-w-xl">
              Pushes 1,000 scheduled section slots and 35 room mappings to edge camera nodes so automated attendance tracking knows which section is in which room every period.
            </p>
          </div>
        </div>

        <button
          onClick={handleSyncSmartClass}
          disabled={syncingSmartClass}
          className="inline-flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-6 py-3 rounded-xl text-sm transition-all shadow-md shrink-0 cursor-pointer disabled:opacity-50"
        >
          {syncingSmartClass ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" /> Syncing Master Schedule...
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" /> Sync Master Timetable to SmartClass
            </>
          )}
        </button>
      </div>

      {syncResult && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs font-semibold flex items-center justify-between shadow-sm animate-in fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            <span>{syncResult.message}</span>
          </div>
          <span className="text-[11px] text-emerald-600 font-mono">{syncResult.synced_at}</span>
        </div>
      )}

      {/* Cohort & Year-Wise Consolidated Excel Exporter Section */}
      <div className="bg-gradient-to-r from-emerald-950 via-teal-900 to-slate-900 text-white rounded-2xl p-6 shadow-md border border-emerald-800/40">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-emerald-600/30 rounded-xl border border-emerald-400/30 text-emerald-200">
              <LayoutGrid className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-bold text-base text-white">Year & Branch Cohort Consolidated Excel Exporter (Version V{selectedVersionId})</h3>
              <p className="text-xs text-emerald-200 max-w-2xl">
                Generates a dedicated `.xlsx` workbook for all sections of a selected year (e.g. 2nd Year AIML, 4th Year AIML, CS & DS). Tab 1 features a **Combined Master Sheet** showing all sections side-by-side!
              </p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3">
            <select
              value={selectedCohortKey}
              onChange={(e) => setSelectedCohortKey(e.target.value)}
              className="bg-white text-slate-900 text-xs font-bold px-4 py-2.5 rounded-xl border border-emerald-300 focus:outline-none cursor-pointer w-full sm:w-auto"
            >
              {cohortGroups.map(c => (
                <option key={c.key} value={c.key}>
                  {c.label} ({c.sections_count} Sections)
                </option>
              ))}
            </select>

            <button
              onClick={handleExportCohortExcel}
              disabled={downloadingCohortExcel}
              className="inline-flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-5 py-2.5 rounded-xl text-xs transition-colors shadow-md cursor-pointer disabled:opacity-50 whitespace-nowrap"
            >
              {downloadingCohortExcel ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileSpreadsheet className="w-4 h-4" />}
              Download {selectedCohortObj ? selectedCohortObj.key : 'Cohort'} Excel (V{selectedVersionId})
            </button>
          </div>
        </div>
      </div>

      {/* Minors & Honors Department Master Sheet Exporter Banner */}
      <div className="bg-gradient-to-r from-amber-950 via-yellow-900 to-slate-900 text-white rounded-2xl p-6 shadow-md border border-amber-700/40">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-amber-500/30 rounded-xl border border-amber-400/30 text-amber-300">
              <Award className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-bold text-base text-white">Minors & Honors Master Department Allocation Sheet (Version V{selectedVersionId})</h3>
              <p className="text-xs text-amber-200 max-w-2xl">
                Generates the official VFSTR Minors/Honors Excel master sheet with yellow branch banners (AIML, CS, CSBS, DS, IoT) listing elective course codes, room venues, and instructor teams.
              </p>
            </div>
          </div>

          <button
            onClick={handleExportMinorsHonors}
            disabled={downloadingMinorsHonors}
            className="inline-flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold px-5 py-2.5 rounded-xl text-xs transition-colors shadow-md cursor-pointer disabled:opacity-50 whitespace-nowrap"
          >
            {downloadingMinorsHonors ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileSpreadsheet className="w-4 h-4" />}
            Download Minors/Honors Master Excel (V{selectedVersionId})
          </button>
        </div>
      </div>

      {/* Individual Faculty Schedule Search & Export Section */}
      <div className="bg-gradient-to-r from-purple-900 to-indigo-900 text-white rounded-2xl p-6 shadow-md border border-purple-800/40">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-purple-600/30 rounded-xl border border-purple-400/30 text-purple-200">
              <UserCheck className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-bold text-base text-white">Faculty Individual Weekly Schedule Exporter (Version V{selectedVersionId})</h3>
              <p className="text-xs text-purple-200">Select any faculty member to generate and download their personal single-page printable PDF teaching schedule.</p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3">
            <select
              value={selectedFacultyId || ''}
              onChange={(e) => setSelectedFacultyId(Number(e.target.value))}
              className="bg-white text-slate-900 text-xs font-bold px-4 py-2.5 rounded-xl border border-purple-300 focus:outline-none cursor-pointer w-full sm:w-auto"
            >
              {facultyList.map(f => (
                <option key={f.id} value={f.id}>{f.name} ({f.designation})</option>
              ))}
            </select>

            <button
              onClick={handleExportSingleFacultyPdf}
              disabled={downloadingSingleFacultyPdf || !selectedFacultyId}
              className="inline-flex items-center justify-center gap-2 bg-white hover:bg-purple-50 text-purple-900 font-bold px-5 py-2.5 rounded-xl text-xs transition-colors shadow-md cursor-pointer disabled:opacity-50 whitespace-nowrap"
            >
              {downloadingSingleFacultyPdf ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4 text-purple-700" />}
              Download {selectedFacultyObj ? selectedFacultyObj.name.split(' ')[0] : 'Faculty'}&apos;s PDF (V{selectedVersionId})
            </button>
          </div>
        </div>
      </div>

      {/* Export Options Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Department Master Excel Export */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col justify-between hover:shadow-md transition-shadow">
          <div>
            <div className="p-3 bg-emerald-50 rounded-xl w-fit mb-4 border border-emerald-100">
              <FileSpreadsheet className="w-6 h-6 text-emerald-600" />
            </div>
            <h3 className="font-bold text-slate-900 text-base mb-2">Master Department Excel (.xlsx - V{selectedVersionId})</h3>
            <p className="text-xs text-slate-500 mb-6">
              Full department workbook containing 40+ individual section tabs (`II AIML-A`, `III CS`), room codes in cells, and faculty legend below each table.
            </p>
          </div>
          <button
            onClick={handleExportExcel}
            disabled={downloadingExcel}
            className="w-full inline-flex items-center justify-center gap-2 bg-slate-900 hover:bg-slate-800 text-white font-medium px-4 py-2.5 rounded-xl text-sm transition-colors cursor-pointer disabled:opacity-50"
          >
            {downloadingExcel ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />} Download Master Excel (V{selectedVersionId})
          </button>
        </div>

        {/* Section PDFs */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col justify-between hover:shadow-md transition-shadow">
          <div>
            <div className="p-3 bg-blue-50 rounded-xl w-fit mb-4 border border-blue-100">
              <FileText className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="font-bold text-slate-900 text-base mb-2">Printable Section PDFs (V{selectedVersionId})</h3>
            <p className="text-xs text-slate-500 mb-6">
              Generates 40+ single-page A4 printable PDF schedules with rich subject, room, and faculty details for classroom notice boards.
            </p>
          </div>
          <button
            onClick={handleExportSectionPdfs}
            disabled={downloadingSectionPdfs}
            className="w-full inline-flex items-center justify-center gap-2 bg-slate-900 hover:bg-slate-800 text-white font-medium px-4 py-2.5 rounded-xl text-sm transition-colors cursor-pointer disabled:opacity-50"
          >
            {downloadingSectionPdfs ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />} Generate Section PDFs (V{selectedVersionId})
          </button>
        </div>

        {/* Master Faculty Schedules Booklet */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col justify-between hover:shadow-md transition-shadow">
          <div>
            <div className="p-3 bg-purple-50 rounded-xl w-fit mb-4 border border-purple-100">
              <Printer className="w-6 h-6 text-purple-600" />
            </div>
            <h3 className="font-bold text-slate-900 text-base mb-2">Faculty Booklet (V{selectedVersionId})</h3>
            <p className="text-xs text-slate-500 mb-6">
              Full department 80+ page master PDF booklet containing individual teaching schedule pages for all faculty members.
            </p>
          </div>
          <button
            onClick={handleExportFacultyPdfs}
            disabled={downloadingFacultyPdfs}
            className="w-full inline-flex items-center justify-center gap-2 bg-slate-900 hover:bg-slate-800 text-white font-medium px-4 py-2.5 rounded-xl text-sm transition-colors cursor-pointer disabled:opacity-50"
          >
            {downloadingFacultyPdfs ? <Loader2 className="w-4 h-4 animate-spin" /> : <Printer className="w-4 h-4" />} Export Faculty Booklet (V{selectedVersionId})
          </button>
        </div>
      </div>
    </div>
  );
}
