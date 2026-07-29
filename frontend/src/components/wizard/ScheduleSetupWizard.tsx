"use client";

import React, { useState, useEffect } from "react";
import { Sparkles, ChevronRight, ChevronLeft, AlertCircle, X, ShieldAlert, Loader2 } from "lucide-react";
import { CourseAssignmentInput, TimetableGenerationRequest, WizardGenerationResponse } from "@/lib/types";
import { timetableApi } from "@/lib/api";
import { TimetableGrid } from "@/components/timetable/TimetableGrid";

// Import Modular Wizard Step Components
import { WizardStepScope } from "./WizardStepScope";
import { WizardStepCurriculum } from "./WizardStepCurriculum";
import { WizardStepVenues } from "./WizardStepVenues";
import { WizardStepSolve } from "./WizardStepSolve";

interface ScheduleSetupWizardProps {
  onSuccess?: (response: WizardGenerationResponse) => void;
}

export const ScheduleSetupWizard: React.FC<ScheduleSetupWizardProps> = ({ onSuccess }) => {
  const [step, setStep] = useState<number>(1);
  const [branch, setBranch] = useState<string>("AIML");
  const [yearLevel, setYearLevel] = useState<string>("II Year");
  const [selectedSections, setSelectedSections] = useState<string[]>([]);
  const [preferredBlock, setPreferredBlock] = useState<string>("Block-VI (601-619)");
  const [maxDailyHours, setMaxDailyHours] = useState<number>(4);
  const [assignments, setAssignments] = useState<CourseAssignmentInput[]>([]);

  // Live Department Defaults from API
  const [facultyPool, setFacultyPool] = useState<string[]>([]);
  const [availableSections, setAvailableSections] = useState<string[]>([]);
  const [roomsPool, setRoomsPool] = useState<any[]>([]);
  const [curriculaMap, setCurriculaMap] = useState<Record<string, CourseAssignmentInput[]>>({});

  const [loadingDefaults, setLoadingDefaults] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [generatedResult, setGeneratedResult] = useState<WizardGenerationResponse | null>(null);

  // Faculty Schedule Modal State
  const [inspectFacultyName, setInspectFacultyName] = useState<string | null>(null);
  const [facultyTtData, setFacultyTtData] = useState<any | null>(null);
  const [loadingFacultyTt, setLoadingFacultyTt] = useState<boolean>(false);

  // Auto-Load Department Live Defaults on Mount
  useEffect(() => {
    setLoadingDefaults(true);
    timetableApi.getWizardDefaults()
      .then((res) => {
        const d = res.data;
        const facs = (d.faculty || []).map((f: any) => f.name);
        const secs = d.sections || [];
        setFacultyPool(facs);
        setAvailableSections(secs);
        setRoomsPool(d.rooms || []);
        setCurriculaMap(d.curricula || {});

        // Set default selections
        setSelectedSections(secs.slice(0, 12)); // Default II AIML A-L
        if (d.curricula?.["II Year"]) {
          setAssignments(d.curricula["II Year"]);
        }
      })
      .catch((err) => {
        console.error("Failed to load wizard defaults:", err);
      })
      .finally(() => setLoadingDefaults(false));
  }, []);

  // Update curriculum when year level changes
  useEffect(() => {
    if (curriculaMap[yearLevel]) {
      setAssignments(curriculaMap[yearLevel]);
    }
  }, [yearLevel, curriculaMap]);

  const openFacultySchedule = async (facName: string) => {
    setInspectFacultyName(facName);
    setLoadingFacultyTt(true);
    setFacultyTtData(null);
    try {
      const facRes = await timetableApi.getFaculty();
      const match = (facRes.data || []).find((f: any) =>
        f.name.toLowerCase().includes(facName.toLowerCase()) || facName.toLowerCase().includes(f.name.toLowerCase())
      );
      const facId = match ? match.id : 1;
      const ttRes = await timetableApi.getFacultyTimetable(facId, 5);
      setFacultyTtData(ttRes.data);
    } catch (e) {
      console.error("Failed to load faculty timetable", e);
    } finally {
      setLoadingFacultyTt(false);
    }
  };

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setGeneratedResult(null);

    const payload: TimetableGenerationRequest = {
      branch,
      year_level: yearLevel,
      sections: selectedSections,
      preferred_block: preferredBlock,
      max_daily_teaching_hours: maxDailyHours,
      max_classes_per_teacher_per_day: maxDailyHours,
      assignments,
    };

    try {
      const res = await timetableApi.generateFromWizard(payload);
      if (res.data.status === "INFEASIBLE") {
        setError("Generation Infeasible: Over-subscribed period quotas or tight teacher daily caps. Try increasing max daily teacher cap or selecting additional venue blocks.");
      } else {
        setGeneratedResult(res.data);
        onSuccess?.(res.data);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to generate timetable. Please check backend solver server.");
    } finally {
      setLoading(false);
    }
  };

  if (loadingDefaults) {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-3 rounded-2xl border border-slate-200 bg-white">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        <span className="text-xs font-bold text-slate-600">Loading VFSTR Department Faculty, Rooms & Curricula...</span>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      {/* Wizard Header */}
      <div className="mb-6 border-b border-slate-200 pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-blue-600 p-3 text-white shadow-sm">
              <Sparkles className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">Advanced AI Timetable Rule Configurator</h2>
              <p className="text-xs text-slate-500">Configure multi-faculty lab mappings, daily teacher class limits, and continuous period locks.</p>
            </div>
          </div>
          <span className="rounded-full border border-blue-200 bg-blue-50 px-3.5 py-1 text-xs font-bold text-blue-700">
            Step {step} of 4
          </span>
        </div>

        {/* Step Navigation Tabs */}
        <div className="mt-4 grid grid-cols-4 gap-2 text-center text-xs font-bold">
          <button onClick={() => setStep(1)} className={`rounded-lg p-2.5 transition-all cursor-pointer ${step >= 1 ? "bg-blue-700 text-white shadow-sm" : "bg-slate-100 text-slate-400"}`}>
            1. Scope & Teacher Caps
          </button>
          <button onClick={() => setStep(2)} className={`rounded-lg p-2.5 transition-all cursor-pointer ${step >= 2 ? "bg-blue-700 text-white shadow-sm" : "bg-slate-100 text-slate-400"}`}>
            2. Multi-Faculty & Labs
          </button>
          <button onClick={() => setStep(3)} className={`rounded-lg p-2.5 transition-all cursor-pointer ${step >= 3 ? "bg-blue-700 text-white shadow-sm" : "bg-slate-100 text-slate-400"}`}>
            3. Venue Matrix & Locks
          </button>
          <button onClick={() => setStep(4)} className={`rounded-lg p-2.5 transition-all cursor-pointer ${step >= 4 ? "bg-blue-700 text-white shadow-sm" : "bg-slate-100 text-slate-400"}`}>
            4. 0-Clash AI Solve
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-xs font-semibold text-red-700">
          <AlertCircle className="h-4 w-4 shrink-0 text-red-600" />
          <span>{error}</span>
        </div>
      )}

      {/* STEP 1: Academic Scope & Teacher Workload Cap */}
      {step === 1 && (
        <WizardStepScope
          branch={branch}
          setBranch={setBranch}
          yearLevel={yearLevel}
          setYearLevel={setYearLevel}
          selectedSections={selectedSections}
          setSelectedSections={setSelectedSections}
          availableSections={availableSections}
          preferredBlock={preferredBlock}
          setPreferredBlock={setPreferredBlock}
          maxDailyHours={maxDailyHours}
          setMaxDailyHours={setMaxDailyHours}
        />
      )}

      {/* STEP 2: Auto-Loaded Curriculum & Multi-Faculty Mapping */}
      {step === 2 && (
        <WizardStepCurriculum
          assignments={assignments}
          setAssignments={setAssignments}
          facultyPool={facultyPool}
          openFacultySchedule={openFacultySchedule}
        />
      )}

      {/* STEP 3: Venue Pool & Global Locks */}
      {step === 3 && (
        <WizardStepVenues roomsPool={roomsPool} preferredBlock={preferredBlock} />
      )}

      {/* STEP 4: CP-SAT Solver Launcher */}
      {step === 4 && (
        <WizardStepSolve
          loading={loading}
          onGenerate={handleGenerate}
          generatedResult={generatedResult}
          selectedSections={selectedSections}
          maxDailyHours={maxDailyHours}
        />
      )}

      {/* Wizard Footer Navigation Controls */}
      <div className="mt-8 flex items-center justify-between border-t border-slate-200 pt-4">
        <button
          onClick={() => setStep((s) => Math.max(1, s - 1))}
          disabled={step === 1 || loading}
          className="flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-4 py-2 text-xs font-bold text-slate-700 shadow-sm hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
        >
          <ChevronLeft className="h-4 w-4" /> Back
        </button>

        <div className="flex items-center gap-2">
          {step < 4 ? (
            <button
              onClick={() => setStep((s) => Math.min(4, s + 1))}
              className="flex items-center gap-1.5 rounded-xl bg-blue-600 px-5 py-2 text-xs font-bold text-white shadow-md hover:bg-blue-700 cursor-pointer"
            >
              Continue to Step {step + 1} <ChevronRight className="h-4 w-4" />
            </button>
          ) : (
            <button
              onClick={handleGenerate}
              disabled={loading}
              className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-2.5 text-xs font-extrabold text-white shadow-lg hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 cursor-pointer"
            >
              <Sparkles className="h-4 w-4" /> {loading ? "Solving Engine Running..." : "Run AI Master Solver"}
            </button>
          )}
        </div>
      </div>

      {/* Faculty Schedule Modal */}
      {inspectFacultyName && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-xs">
          <div className="w-full max-w-4xl rounded-3xl border border-slate-200 bg-white p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900">Faculty Schedule: {inspectFacultyName}</h3>
                <p className="text-xs text-slate-500">Live Weekly Teaching Load & Section Assignments</p>
              </div>
              <button
                onClick={() => setInspectFacultyName(null)}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 cursor-pointer"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {loadingFacultyTt ? (
              <div className="flex items-center justify-center p-12 gap-2 text-xs font-bold text-slate-600">
                <Loader2 className="h-5 w-5 animate-spin text-purple-600" /> Fetching Faculty Timetable...
              </div>
            ) : facultyTtData ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between rounded-xl bg-purple-50 p-3 text-xs font-bold text-purple-900">
                  <span>Total Teaching Load: {facultyTtData.total_hours || 0} Hours / Week</span>
                  <span>Assigned Sections: {(facultyTtData.sections || []).join(", ") || "None"}</span>
                </div>
                <TimetableGrid
                  sectionName={inspectFacultyName}
                  entries={(facultyTtData.entries || []).map((e: any) => ({
                    id: String(e.id),
                    day: e.day,
                    period: e.period,
                    subjectCode: e.subject || "LECTURE",
                    roomCode: e.room || "",
                    facultyName: inspectFacultyName,
                    subjectType: e.entry_type || "L",
                  }))}
                />
              </div>
            ) : (
              <div className="p-8 text-center text-xs font-semibold text-slate-500">
                No schedule data found for this faculty member.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
