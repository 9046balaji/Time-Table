'use client';

import React, { useState } from 'react';
import { Upload, FileSpreadsheet, Loader2, AlertCircle } from 'lucide-react';
import { timetableApi } from '@/lib/api';
import { ClashInspector } from '@/components/clash/ClashInspector';

export default function ImportPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [importResult, setImportResult] = useState<any>(null);

  const handleFileUpload = async (file: File) => {
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      setError('Please upload a valid Excel file (.xlsx or .xls)');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await timetableApi.importExcel(file);
      setImportResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to parse Excel file. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileUpload(e.target.files[0]);
    }
  };

  return (
    <div className="space-y-6 w-full max-w-full">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Excel Timetable Ingestion & Clash Inspector</h1>
        <p className="text-sm text-slate-500">
          Upload any VFSTR university timetable spreadsheet (.xlsx) for real-time conflict inspection and diagnostic reporting.
        </p>
      </div>

      {/* File Drag and Drop Upload Area */}
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        className="border-2 border-dashed border-slate-300 bg-white hover:border-blue-500 rounded-2xl p-10 text-center transition-all cursor-pointer shadow-sm relative"
      >
        <input
          type="file"
          accept=".xlsx, .xls"
          onChange={handleFileSelect}
          className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
        />

        {loading ? (
          <div className="flex flex-col items-center justify-center py-4 space-y-3">
            <Loader2 className="w-10 h-10 text-blue-600 animate-spin" />
            <div className="font-bold text-slate-800 text-sm">Parsing Timetable Sheets & Checking Conflicts...</div>
            <div className="text-xs text-slate-500">Extracting sections, rooms, periods, and faculty assignments</div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center space-y-3">
            <div className="w-14 h-14 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center border border-blue-100 shadow-sm">
              <Upload className="w-7 h-7" />
            </div>
            <div>
              <h3 className="font-bold text-slate-800 text-base">Drag & Drop Timetable Excel File Here</h3>
              <p className="text-xs text-slate-500 mt-1">Supports multi-tab files (e.g., ACSE_TIMETABLE_V5.xlsx)</p>
            </div>
            <div className="pt-2">
              <span className="inline-flex items-center gap-2 bg-blue-600 text-white px-5 py-2.5 rounded-xl text-sm font-semibold hover:bg-blue-700 shadow-md transition-colors">
                <FileSpreadsheet className="w-4 h-4" /> Browse Excel File
              </span>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-xs font-semibold flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-600" />
          <span>{error}</span>
        </div>
      )}

      {/* Render Live Clash Inspector when file is uploaded */}
      {importResult && (
        <ClashInspector
          filename={importResult.filename}
          totalSections={importResult.total_sections}
          totalSlots={importResult.total_slots}
          hardViolations={importResult.hard_violations}
          roomClashes={importResult.room_clashes}
          facultyClashes={importResult.faculty_clashes}
          clashDetails={importResult.clash_details}
        />
      )}
    </div>
  );
}
