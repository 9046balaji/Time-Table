"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  Building2,
  Search,
  Plus,
  Edit,
  Trash2,
  X,
  Cpu,
  Monitor,
  Users,
  Calendar,
  CheckCircle2,
  Building,
  Loader2
} from "lucide-react";
import { Room } from "@/lib/types";
import { timetableApi } from "@/lib/api";

interface VenueMasterProfileProps {
  roomList: Room[];
  onAddRoom?: (newRoom: Partial<Room>) => void;
  onUpdateRoom?: (id: number, updatedRoom: Partial<Room>) => void;
  onDeleteRoom?: (id: number) => void;
}

const DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT"];
const PERIODS = [1, 2, 3, 4, 5, 6, 7, 8];

export const VenueMasterProfile: React.FC<VenueMasterProfileProps> = ({
  roomList,
  onAddRoom,
  onUpdateRoom,
  onDeleteRoom
}) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [quickFilter, setQuickFilter] = useState<"ALL" | "CLASS" | "LAB" | "GPU">("ALL");

  // Selected Room for Slide-Over Drawer
  const [selectedRoom, setSelectedRoom] = useState<Room | null>(null);
  const [roomSchedule, setRoomSchedule] = useState<any[]>([]);
  const [loadingSchedule, setLoadingSchedule] = useState(false);

  // Edit Modal State
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingRoom, setEditingRoom] = useState<Partial<Room> | null>(null);

  const [formData, setFormData] = useState({
    code: "",
    room_type: "classroom",
    capacity: 66,
    floor: "6",
    block: "Aryabhatta Bhavan / U-Block",
    gpu_capable: false,
    is_available: true
  });

  // Fetch room occupancy schedule whenever selectedRoom changes
  useEffect(() => {
    if (selectedRoom && selectedRoom.code) {
      setLoadingSchedule(true);
      timetableApi.getRoomTimetable(selectedRoom.code)
        .then((res) => {
          const items = Array.isArray(res.data) ? res.data : (res.data as any)?.entries || (res.data as any)?.items || [];
          setRoomSchedule(items);
        })
        .catch(() => setRoomSchedule([]))
        .finally(() => setLoadingSchedule(false));
    } else {
      setRoomSchedule([]);
    }
  }, [selectedRoom]);

  const handleOpenAddModal = () => {
    setEditingRoom(null);
    setFormData({
      code: "",
      room_type: "classroom",
      capacity: 66,
      floor: "6",
      block: "Aryabhatta Bhavan / U-Block",
      gpu_capable: false,
      is_available: true
    });
    setShowEditModal(true);
  };

  const handleOpenEditModal = (rm: Room) => {
    setEditingRoom(rm);
    setFormData({
      code: rm.code || "",
      room_type: rm.room_type || rm.type || "classroom",
      capacity: rm.capacity || 66,
      floor: String(rm.floor || "6"),
      block: rm.block || "Aryabhatta Bhavan / U-Block",
      gpu_capable: rm.gpu_capable || rm.code.includes("AFTF"),
      is_available: rm.is_available ?? true
    });
    setShowEditModal(true);
  };

  const handleSaveForm = (e: React.FormEvent) => {
    e.preventDefault();
    const payload: Partial<Room> = {
      code: formData.code,
      room_type: formData.room_type,
      capacity: Number(formData.capacity),
      floor: formData.floor,
      block: formData.block,
      gpu_capable: formData.gpu_capable,
      is_available: formData.is_available
    };

    if (editingRoom && editingRoom.id && onUpdateRoom) {
      onUpdateRoom(editingRoom.id, payload);
    } else if (onAddRoom) {
      onAddRoom(payload);
    }
    setShowEditModal(false);
  };

  // Filtered Rooms
  const filteredRooms = useMemo(() => {
    return roomList.filter((rm) => {
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const matchCode = rm.code.toLowerCase().includes(q);
        const matchBlock = (rm.block || "").toLowerCase().includes(q);
        if (!matchCode && !matchBlock) return false;
      }

      return true;
    });
  }, [roomList, searchQuery, quickFilter]);

  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 9;

  const paginatedRooms = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return filteredRooms.slice(start, start + itemsPerPage);
  }, [filteredRooms, currentPage]);

  const totalPages = Math.ceil(filteredRooms.length / itemsPerPage) || 1;



  // Helper to find room occupied slot
  const getScheduledSlot = (day: string, period: number) => {
    return roomSchedule.find((s) => s.day === day && Number(s.period) === period);
  };

  return (
    <div className="space-y-6">

      {/* 1. Header Action Bar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Venues & Computer Labs Registry</h2>
            <span className="px-2.5 py-0.5 bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 text-xs font-bold rounded-full border border-emerald-200 dark:border-emerald-800">
              {roomList.length} Active Venues
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Click any venue card to view room occupancy matrix, seating capacity, and GPU hardware tags.
          </p>
        </div>

        <button
          onClick={handleOpenAddModal}
          className="inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2.5 rounded-xl font-bold text-xs shadow-sm transition-all cursor-pointer"
        >
          <Plus className="w-4 h-4" /> Add Venue
        </button>
      </div>

      {/* 2. Search & Quick Filters Bar */}
      <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search venue code or building block..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
          />
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider shrink-0">Filters:</span>

          <button
            onClick={() => setQuickFilter("ALL")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all shrink-0 cursor-pointer ${
              quickFilter === "ALL"
                ? "bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 shadow-sm"
                : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
            }`}
          >
            All Venues ({roomList.length})
          </button>

          <button
            onClick={() => setQuickFilter("CLASS")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all shrink-0 cursor-pointer ${
              quickFilter === "CLASS"
                ? "bg-blue-600 text-white shadow-sm"
                : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
            }`}
          >
            Classrooms
          </button>

          <button
            onClick={() => setQuickFilter("LAB")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all shrink-0 cursor-pointer ${
              quickFilter === "LAB"
                ? "bg-purple-600 text-white shadow-sm"
                : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
            }`}
          >
            Computer Labs
          </button>

          <button
            onClick={() => setQuickFilter("GPU")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all shrink-0 cursor-pointer ${
              quickFilter === "GPU"
                ? "bg-emerald-600 text-white shadow-sm"
                : "bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800"
            }`}
          >
            High-GPU Compute Labs
          </button>
        </div>
      </div>

      {/* 3. Card Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {paginatedRooms.map((rm) => {
          const isGpu = rm.gpu_capable || rm.code.includes("AFTF");
          const isLab = (rm.room_type || rm.type || "").toLowerCase().includes("lab") || isGpu;
          const cap = rm.capacity || (isGpu ? 72 : isLab ? 60 : 66);

          return (
            <div
              key={rm.id || rm.code}
              onClick={() => setSelectedRoom(rm)}
              className="group bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 hover:border-emerald-400 dark:hover:border-emerald-500 hover:shadow-lg transition-all cursor-pointer relative flex flex-col justify-between"
            >
              <div>
                {/* Header Tag */}
                <div className="flex justify-between items-start mb-2">
                  <span className="text-[11px] font-bold text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/80 px-2.5 py-0.5 rounded-lg border border-emerald-200 dark:border-emerald-800">
                    Room {rm.code}
                  </span>

                  {isGpu ? (
                    <span className="inline-flex items-center gap-1 text-[11px] font-bold text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/60 px-2 py-0.5 rounded-md border border-amber-200 dark:border-amber-800">
                      <Cpu className="w-3 h-3 text-amber-600" /> High GPU Lab
                    </span>
                  ) : (
                    <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                      {isLab ? "Computer Lab" : "Classroom"}
                    </span>
                  )}
                </div>

                <h3 className="font-bold text-slate-900 dark:text-white text-base group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                  Venue {rm.code}
                </h3>

                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  {rm.block || "Aryabhatta Bhavan / U-Block"} • Floor {rm.floor || "6"}
                </p>

                {/* Specs Pill List */}
                <div className="mt-4 flex items-center gap-3 text-xs font-bold">
                  <div className="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700">
                    <Users className="w-3.5 h-3.5 text-slate-500" />
                    <span>{cap} Seats</span>
                  </div>

                  <div className="flex items-center gap-1.5 bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 px-3 py-1.5 rounded-xl border border-emerald-200 dark:border-emerald-800">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Available</span>
                  </div>
                </div>
              </div>

              {/* Action Hint */}
              <div className="mt-5 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-emerald-600 dark:text-emerald-400 font-bold group-hover:translate-x-0.5 transition-transform">
                <span>Inspect Occupancy & Hardware</span>
                <span>→</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Pagination Controls Bar */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm text-xs font-medium">
          <span className="text-slate-500 dark:text-slate-400">
            Showing {paginatedRooms.length} of {filteredRooms.length} active department venues
          </span>
          <div className="flex items-center gap-1.5">
            <button
              disabled={currentPage === 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              className="px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 disabled:opacity-40 font-bold transition-all"
            >
              Prev
            </button>
            <span className="px-3 font-bold text-slate-800 dark:text-slate-200">
              Page {currentPage} of {totalPages}
            </span>
            <button
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              className="px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 disabled:opacity-40 font-bold transition-all"
            >
              Next
            </button>
          </div>
        </div>
      )}


      {/* 4. Slide-Over Venue Master Dossier Drawer */}
      {selectedRoom && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-black/40 backdrop-blur-sm flex justify-end animate-in fade-in">
          <div className="w-full max-w-xl bg-white dark:bg-slate-900 h-full shadow-2xl p-6 flex flex-col justify-between overflow-y-auto animate-in slide-in-from-right duration-200 border-l border-slate-200 dark:border-slate-800">
            <div className="space-y-6">

              {/* Drawer Top Header */}
              <div className="flex justify-between items-start pb-4 border-b border-slate-200 dark:border-slate-800">
                <div>
                  <span className="text-xs text-emerald-600 dark:text-emerald-400 font-bold">VENUE CODE {selectedRoom.code}</span>
                  <h2 className="text-xl font-bold text-slate-900 dark:text-white">Venue {selectedRoom.code} Specifications</h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400">{selectedRoom.block || "Aryabhatta Bhavan / U-Block"} • Floor {selectedRoom.floor || "6"}</p>
                </div>

                <button
                  onClick={() => setSelectedRoom(null)}
                  className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Specs Grid */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-4 bg-slate-50 dark:bg-slate-800/60 rounded-2xl border border-slate-200 dark:border-slate-800">
                  <span className="text-[11px] text-slate-500 dark:text-slate-400 font-bold uppercase">Seating Capacity</span>
                  <p className="text-base font-extrabold text-slate-900 dark:text-white mt-1">
                    {selectedRoom.capacity || 66} Students
                  </p>
                </div>

                <div className="p-4 bg-emerald-50 dark:bg-emerald-950/40 rounded-2xl border border-emerald-100 dark:border-emerald-800/60">
                  <span className="text-[11px] text-emerald-700 dark:text-emerald-300 font-bold uppercase">Hardware Type</span>
                  <p className="text-base font-extrabold text-emerald-950 dark:text-emerald-100 mt-1">
                    {selectedRoom.gpu_capable || selectedRoom.code.includes("AFTF") ? "GPU Compute Rig Lab" : "Standard Venue"}
                  </p>
                </div>
              </div>

              {/* Room Weekly Occupancy Schedule Grid */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Weekly Occupancy Matrix ({roomSchedule.length} / 48 Slots Occupied)</h4>
                  {loadingSchedule && <Loader2 className="w-3.5 h-3.5 text-emerald-600 animate-spin" />}
                </div>

                <div className="grid grid-cols-6 gap-1.5 bg-slate-50 dark:bg-slate-800/60 p-3 rounded-2xl border border-slate-200 dark:border-slate-800">
                  {DAYS.map((day) => (
                    <div key={day} className="text-center">
                      <span className="text-[11px] font-extrabold text-slate-700 dark:text-slate-300 block mb-1.5">{day}</span>
                      <div className="space-y-1.5">
                        {PERIODS.map((p) => {
                          const slot = getScheduledSlot(day, p);
                          if (slot) {
                            return (
                              <div
                                key={p}
                                title={`${slot.subject || "Class"} (${slot.section || ""}) - ${slot.faculty || ""}`}
                                className="w-full py-1.5 px-1 rounded-lg bg-emerald-600 text-white text-[9px] font-extrabold shadow-sm border border-emerald-700 leading-tight truncate"
                              >
                                <span className="block font-black">{slot.subject || `P${p}`}</span>
                                <span className="block opacity-90 text-[8px] font-medium">{slot.section || ""}</span>
                                <span className="block opacity-75 text-[7.5px] font-mono">{Array.isArray(slot.faculty) ? slot.faculty[0] : slot.faculty || ""}</span>
                              </div>
                            );
                          }

                          return (
                            <div
                              key={p}
                              className="w-full py-1.5 px-1 rounded-lg bg-slate-200/60 dark:bg-slate-700/50 text-slate-500 dark:text-slate-400 text-[9px] font-semibold flex items-center justify-center border border-slate-300/40 dark:border-slate-600/40"
                            >
                              Free
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Footer Buttons */}
            <div className="pt-6 mt-6 border-t border-slate-200 dark:border-slate-800 flex gap-3">
              <button
                onClick={() => setSelectedRoom(null)}
                className="flex-1 py-3 border border-slate-300 dark:border-slate-700 rounded-xl text-xs font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
              >
                Close
              </button>

              <button
                onClick={() => {
                  const rm = selectedRoom;
                  setSelectedRoom(null);
                  handleOpenEditModal(rm);
                }}
                className="flex-1 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-md cursor-pointer inline-flex items-center justify-center gap-2"
              >
                <Edit className="w-4 h-4" /> Edit Venue Specs
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add / Edit Modal */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl p-6 w-full max-w-md space-y-4">
            <div className="flex justify-between items-center pb-3 border-b border-slate-200 dark:border-slate-800">
              <h3 className="font-bold text-slate-900 dark:text-white text-base">
                {editingRoom ? "Edit Venue Specifications" : "Add New Venue"}
              </h3>
              <button onClick={() => setShowEditModal(false)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveForm} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Room Code</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. 601, AFTF-12"
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-xs font-bold text-slate-900 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Room Type</label>
                  <select
                    value={formData.room_type}
                    onChange={(e) => setFormData({ ...formData, room_type: e.target.value })}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-xs font-bold text-slate-900 dark:text-white"
                  >
                    <option value="classroom">Classroom</option>
                    <option value="computer_lab">Computer Lab</option>
                    <option value="gpu_lab">GPU Compute Lab</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Capacity (Seats)</label>
                  <input
                    type="number"
                    min={20}
                    max={120}
                    value={formData.capacity}
                    onChange={(e) => setFormData({ ...formData, capacity: Number(e.target.value) })}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-xs font-bold text-slate-900 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Floor Level</label>
                  <input
                    type="text"
                    value={formData.floor}
                    onChange={(e) => setFormData({ ...formData, floor: e.target.value })}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-xs font-bold text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Building Block Name</label>
                <input
                  type="text"
                  value={formData.block}
                  onChange={(e) => setFormData({ ...formData, block: e.target.value })}
                  className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-xs font-bold text-slate-900 dark:text-white"
                />
              </div>

              <div className="flex items-center gap-2 pt-2">
                <input
                  type="checkbox"
                  id="gpu_check"
                  checked={formData.gpu_capable}
                  onChange={(e) => setFormData({ ...formData, gpu_capable: e.target.checked })}
                  className="rounded border-slate-300 text-emerald-600 focus:ring-emerald-500 cursor-pointer"
                />
                <label htmlFor="gpu_check" className="text-xs font-bold text-slate-700 dark:text-slate-300 cursor-pointer">
                  Equipped with High-GPU Compute Rigs (for DL/AI practicals)
                </label>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowEditModal(false)}
                  className="px-4 py-2 border border-slate-300 dark:border-slate-700 rounded-xl text-xs font-bold text-slate-700 dark:text-slate-300"
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-md"
                >
                  Save Venue Specs
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
