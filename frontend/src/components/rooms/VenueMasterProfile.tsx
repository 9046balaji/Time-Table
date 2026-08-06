"use client";

import React, { useState, useMemo } from "react";
import {
  Building2,
  Search,
  Filter,
  Plus,
  Edit,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  Layers,
  X,
  Sparkles,
  Cpu,
  Monitor,
  Users,
  Grid,
  List,
  Calendar,
  Check,
  Building,
  Maximize2,
  Wrench
} from "lucide-react";
import { Room } from "@/lib/types";

interface VenueMasterProfileProps {
  roomList: Room[];
  onAddRoom?: (newRoom: Partial<Room>) => void;
  onUpdateRoom?: (id: number, updatedRoom: Partial<Room>) => void;
  onDeleteRoom?: (id: number) => void;
}

const DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT"];
const PERIODS = [1, 2, 3, 4, 5, 6, 7, 8];

type SubTab = "inventory" | "labs" | "occupancy";

export const VenueMasterProfile: React.FC<VenueMasterProfileProps> = ({
  roomList,
  onAddRoom,
  onUpdateRoom,
  onDeleteRoom
}) => {
  // Sub-Tab Navigation
  const [activeSubTab, setActiveSubTab] = useState<SubTab>("inventory");

  // Roster Controls
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [blockFilter, setBlockFilter] = useState("ALL");
  const [viewMode, setViewMode] = useState<"CARDS" | "TABLE">("CARDS");

  // Selected Room for Dossier Drawer & Occupancy Matrix
  const [selectedRoomCode, setSelectedRoomCode] = useState<string>(roomList[0]?.code || "601");

  // Add/Edit Form Modal State
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingRoom, setEditingRoom] = useState<Partial<Room> | null>(null);

  // Form Fields State
  const [formData, setFormData] = useState({
    code: "",
    room_type: "classroom",
    capacity: 66,
    floor: "6",
    block: "Aryabhatta Bhavan / U-Block",
    gpu_capable: false,
    is_available: true
  });

  const selectedRoom = useMemo(() => {
    return roomList.find((r) => r.code === selectedRoomCode) || roomList[0] || null;
  }, [roomList, selectedRoomCode]);

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
      type: formData.room_type,
      capacity: Number(formData.capacity),
      floor: formData.floor,
      block: formData.block,
      gpu_capable: formData.gpu_capable || formData.room_type === "gpu_lab",
      is_available: formData.is_available
    };

    if (editingRoom && editingRoom.id && onUpdateRoom) {
      onUpdateRoom(editingRoom.id, payload);
    } else if (onAddRoom) {
      onAddRoom(payload);
    }
    setShowEditModal(false);
  };

  // Filtered Room Inventory
  const filteredRooms = useMemo(() => {
    return roomList.filter((rm) => {
      // Search Filter (Code, Floor, Block, Capacity)
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const matchCode = rm.code.toLowerCase().includes(q);
        const matchFloor = String(rm.floor || "").toLowerCase().includes(q);
        const matchBlock = (rm.block || "").toLowerCase().includes(q);
        const matchCap = String(rm.capacity || "").includes(q);
        if (!matchCode && !matchFloor && !matchBlock && !matchCap) return false;
      }

      // Room Type Filter
      const rType = rm.room_type || rm.type || "classroom";
      if (typeFilter !== "ALL" && rType !== typeFilter) {
        return false;
      }

      // Block Filter
      if (blockFilter !== "ALL" && !(rm.block || "").includes(blockFilter)) {
        return false;
      }

      return true;
    });
  }, [roomList, searchQuery, typeFilter, blockFilter]);

  // High-GPU & Computer Labs subset
  const labRooms = useMemo(() => {
    return roomList.filter((rm) => {
      const rType = rm.room_type || rm.type || "";
      return rType === "computer_lab" || rType === "gpu_lab" || rm.gpu_capable || rm.code.includes("AFTF");
    });
  }, [roomList]);

  return (
    <div className="space-y-6">

      {/* TOP SUB-TAB NAVIGATION SWITCHER */}
      <div className="bg-white dark:bg-slate-900 p-2 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto p-1 bg-slate-100 dark:bg-slate-800/80 rounded-xl">
          <button
            onClick={() => setActiveSubTab("inventory")}
            className={`px-4 py-2 rounded-lg text-xs font-extrabold transition-all inline-flex items-center gap-2 shrink-0 ${
              activeSubTab === "inventory"
                ? "bg-white dark:bg-slate-900 text-emerald-600 dark:text-emerald-400 shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            <Building2 className="w-4 h-4" /> Venue Directory & Inventory ({roomList.length})
          </button>

          <button
            onClick={() => setActiveSubTab("labs")}
            className={`px-4 py-2 rounded-lg text-xs font-extrabold transition-all inline-flex items-center gap-2 shrink-0 ${
              activeSubTab === "labs"
                ? "bg-white dark:bg-slate-900 text-purple-600 dark:text-purple-400 shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            <Cpu className="w-4 h-4" /> High-GPU & Computer Labs ({labRooms.length})
          </button>

          <button
            onClick={() => setActiveSubTab("occupancy")}
            className={`px-4 py-2 rounded-lg text-xs font-extrabold transition-all inline-flex items-center gap-2 shrink-0 ${
              activeSubTab === "occupancy"
                ? "bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            <Calendar className="w-4 h-4" /> Room Occupancy Inspector
          </button>
        </div>

        {/* Global Action Button */}
        <button
          onClick={handleOpenAddModal}
          className="w-full sm:w-auto px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm inline-flex items-center justify-center gap-1.5 shrink-0"
        >
          <Plus className="w-4 h-4" /> Add New Venue
        </button>
      </div>

      {/* SUB-VIEW 1: VENUE DIRECTORY & INVENTORY */}
      {activeSubTab === "inventory" && (
        <div className="space-y-6">
          {/* Search & Filter Toolbar */}
          <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="relative flex-1 w-full">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search venue by Code (601, AFTF-12, N-301), Floor (6th, 2nd), or Seating Capacity..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 font-medium"
              />
            </div>

            <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto justify-end">
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-xs font-bold text-slate-900 dark:text-white shrink-0"
              >
                <option value="ALL">All Venue Types</option>
                <option value="classroom">Classroom</option>
                <option value="computer_lab">Computer Lab</option>
                <option value="gpu_lab">GPU Compute Lab</option>
                <option value="seminar_hall">Seminar Hall</option>
              </select>

              <select
                value={blockFilter}
                onChange={(e) => setBlockFilter(e.target.value)}
                className="px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-xs font-bold text-slate-900 dark:text-white shrink-0"
              >
                <option value="ALL">All Blocks</option>
                <option value="U-Block">U-Block (Aryabhatta)</option>
                <option value="H-Block">H-Block (Divisional)</option>
                <option value="NB">New Block (NB)</option>
              </select>

              <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl shrink-0">
                <button
                  onClick={() => setViewMode("CARDS")}
                  className={`p-1.5 rounded-lg text-xs font-bold transition-all ${
                    viewMode === "CARDS" ? "bg-white dark:bg-slate-900 text-emerald-600 shadow-sm" : "text-slate-500"
                  }`}
                >
                  <Grid className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode("TABLE")}
                  className={`p-1.5 rounded-lg text-xs font-bold transition-all ${
                    viewMode === "TABLE" ? "bg-white dark:bg-slate-900 text-emerald-600 shadow-sm" : "text-slate-500"
                  }`}
                >
                  <List className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          {/* CARDS VIEW */}
          {viewMode === "CARDS" && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
              {filteredRooms.map((rm) => {
                const rType = rm.room_type || rm.type || "classroom";
                const isGpu = rm.gpu_capable || rType === "gpu_lab" || rm.code.includes("AFTF");
                const isLab = rType === "computer_lab" || rType === "gpu_lab";

                return (
                  <div
                    key={rm.id}
                    className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md transition-all flex flex-col justify-between gap-4"
                  >
                    <div className="space-y-3">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <span className={`px-2.5 py-0.5 rounded text-[10px] font-extrabold uppercase font-mono border ${
                            isGpu
                              ? "bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-800"
                              : isLab
                              ? "bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800"
                              : "bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800"
                          }`}>
                            {isGpu ? "High-GPU Lab" : isLab ? "Computer Lab" : "Lecture Classroom"}
                          </span>
                          <h3 className="text-xl font-black text-slate-900 dark:text-white mt-1.5 font-mono">
                            {rm.code}
                          </h3>
                        </div>

                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => handleOpenEditModal(rm)}
                            className="p-1.5 text-slate-400 hover:text-emerald-600 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                          >
                            <Edit className="w-3.5 h-3.5" />
                          </button>
                          {onDeleteRoom && (
                            <button
                              onClick={() => onDeleteRoom(rm.id)}
                              className="p-1.5 text-slate-400 hover:text-red-600 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Room Details Grid */}
                      <div className="space-y-2 bg-slate-50 dark:bg-slate-800/60 p-3 rounded-xl border border-slate-100 dark:border-slate-700/60 text-xs">
                        <div className="flex items-center justify-between font-medium">
                          <span className="text-slate-400">Seating Capacity:</span>
                          <span className="font-extrabold text-slate-900 dark:text-white">{rm.capacity || 66} Students</span>
                        </div>
                        <div className="flex items-center justify-between font-medium">
                          <span className="text-slate-400">Floor Level:</span>
                          <span className="font-bold text-slate-800 dark:text-slate-200">Floor {rm.floor || "6"}</span>
                        </div>
                        <div className="flex items-center justify-between font-medium">
                          <span className="text-slate-400">Building Block:</span>
                          <span className="font-bold text-slate-800 dark:text-slate-200 truncate max-w-[130px]" title={rm.block || "U-Block"}>
                            {rm.block || "U-Block"}
                          </span>
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={() => {
                        setSelectedRoomCode(rm.code);
                        setActiveSubTab("occupancy");
                      }}
                      className="w-full py-2 bg-slate-100 dark:bg-slate-800 hover:bg-emerald-600 hover:text-white dark:hover:bg-emerald-600 text-slate-700 dark:text-slate-300 font-bold text-xs rounded-xl transition-all inline-flex items-center justify-center gap-1.5"
                    >
                      <Calendar className="w-3.5 h-3.5" /> View Period Occupancy Grid
                    </button>
                  </div>
                );
              })}
            </div>
          )}

          {/* TABLE VIEW */}
          {viewMode === "TABLE" && (
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[800px] border-collapse text-xs text-left">
                  <thead>
                    <tr className="bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 font-bold border-b border-slate-200 dark:border-slate-700">
                      <th className="p-3">Venue Code</th>
                      <th className="p-3">Type</th>
                      <th className="p-3">Seating Capacity</th>
                      <th className="p-3">Floor</th>
                      <th className="p-3">Building Block</th>
                      <th className="p-3">Status</th>
                      <th className="p-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {filteredRooms.map((rm) => {
                      const rType = rm.room_type || rm.type || "classroom";
                      const isGpu = rm.gpu_capable || rType === "gpu_lab" || rm.code.includes("AFTF");

                      return (
                        <tr key={rm.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                          <td className="p-3 font-mono font-extrabold text-emerald-600 dark:text-emerald-400 text-sm">{rm.code}</td>
                          <td className="p-3">
                            <span className={`px-2.5 py-0.5 rounded text-[10px] font-extrabold uppercase ${
                              isGpu ? "bg-purple-100 text-purple-800" : "bg-emerald-100 text-emerald-800"
                            }`}>
                              {isGpu ? "GPU Lab" : rType.replace("_", " ")}
                            </span>
                          </td>
                          <td className="p-3 font-bold text-slate-900 dark:text-slate-100">{rm.capacity || 66} Seats</td>
                          <td className="p-3 font-medium text-slate-600 dark:text-slate-400">Floor {rm.floor || "6"}</td>
                          <td className="p-3 font-bold text-slate-800 dark:text-slate-200">{rm.block || "U-Block"}</td>
                          <td className="p-3">
                            <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold text-[10px]">Active</span>
                          </td>
                          <td className="p-3 text-right">
                            <button
                              onClick={() => {
                                setSelectedRoomCode(rm.code);
                                setActiveSubTab("occupancy");
                              }}
                              className="px-3 py-1 bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 font-bold rounded-lg hover:bg-emerald-100 text-[11px]"
                            >
                              Occupancy
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* SUB-VIEW 2: HIGH-GPU & COMPUTER LABS HUB */}
      {activeSubTab === "labs" && (
        <div className="space-y-6">
          <div className="bg-purple-900/10 border border-purple-300 dark:border-purple-800 p-4 rounded-2xl flex items-center justify-between">
            <div>
              <h3 className="text-sm font-extrabold text-purple-900 dark:text-purple-200">High-GPU Compute & Specialized Lab Network</h3>
              <p className="text-xs text-purple-700 dark:text-purple-300 mt-0.5">Venues dedicated for Deep Learning (DL), Computer Vision (CV), and Practical Programming Courses</p>
            </div>
            <span className="px-3 py-1 bg-purple-600 text-white font-extrabold text-xs rounded-xl">{labRooms.length} Active Labs</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {labRooms.map((rm) => (
              <div key={rm.id} className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-purple-200 dark:border-purple-900/60 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <span className="px-2.5 py-0.5 rounded bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300 font-mono text-xs font-black">
                    {rm.code}
                  </span>
                  <Cpu className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <h4 className="text-base font-extrabold text-slate-900 dark:text-white">
                    {rm.code.includes("AFTF") ? "High-Capacity GPU Workstation Lab" : "Computer Programming Lab"}
                  </h4>
                  <p className="text-xs text-slate-500 mt-0.5">Floor {rm.floor || "6"} • {rm.capacity || 60} Workstation Stations</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SUB-VIEW 3: ROOM OCCUPANCY & FREE SLOT INSPECTOR */}
      {activeSubTab === "occupancy" && (
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
            <div>
              <h3 className="text-base font-extrabold text-slate-900 dark:text-white">
                Weekly Period Occupancy Grid ({selectedRoom?.code})
              </h3>
              <p className="text-xs text-slate-500">Inspect occupied vs available periods across the 6-day academic timetable</p>
            </div>

            <select
              value={selectedRoomCode}
              onChange={(e) => setSelectedRoomCode(e.target.value)}
              className="px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-xs font-bold text-slate-900 dark:text-white"
            >
              {roomList.map((r) => (
                <option key={r.id} value={r.code}>{r.code} ({r.room_type || r.type || "classroom"} - {r.capacity} seats)</option>
              ))}
            </select>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-center text-xs min-w-[700px]">
              <thead>
                <tr className="bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 font-bold border-b border-slate-200 dark:border-slate-700">
                  <th className="p-3 text-left">Day / Period</th>
                  {PERIODS.map((p) => (
                    <th key={p} className="p-3">Period {p}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {DAYS.map((d) => (
                  <tr key={d} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                    <td className="p-3 font-extrabold text-slate-900 dark:text-white text-left">{d}</td>
                    {PERIODS.map((p) => (
                      <td key={p} className="p-2">
                        <button className="w-full py-2 rounded-lg text-xs font-bold bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700">
                          Vacant / Free
                        </button>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ADD / EDIT VENUE FORM MODAL */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <h3 className="text-base font-extrabold text-slate-900 dark:text-white">
                {editingRoom ? "Edit Venue Specifications" : "Add New Room / Venue"}
              </h3>
              <button onClick={() => setShowEditModal(false)} className="text-slate-400 hover:text-white font-bold">
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveForm} className="space-y-3 text-xs">
              <div>
                <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Venue Code / Room Number:</label>
                <input
                  type="text"
                  required
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  placeholder="e.g. 601, 604, AFTF-12, N-301"
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white font-mono font-bold"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Venue Type:</label>
                  <select
                    value={formData.room_type}
                    onChange={(e) => setFormData({ ...formData, room_type: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white font-bold"
                  >
                    <option value="classroom">Lecture Classroom</option>
                    <option value="computer_lab">Computer Lab</option>
                    <option value="gpu_lab">GPU Compute Lab</option>
                    <option value="seminar_hall">Seminar Hall</option>
                  </select>
                </div>

                <div>
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Seating Capacity:</label>
                  <input
                    type="number"
                    min={10}
                    max={300}
                    value={formData.capacity}
                    onChange={(e) => setFormData({ ...formData, capacity: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white font-bold"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Floor Level:</label>
                  <input
                    type="text"
                    value={formData.floor}
                    onChange={(e) => setFormData({ ...formData, floor: e.target.value })}
                    placeholder="Floor 6, 2nd Floor, AFTF"
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white font-bold"
                  />
                </div>

                <div>
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Building Block:</label>
                  <input
                    type="text"
                    value={formData.block}
                    onChange={(e) => setFormData({ ...formData, block: e.target.value })}
                    placeholder="Aryabhatta Bhavan / U-Block"
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white font-bold"
                  />
                </div>
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowEditModal(false)}
                  className="px-4 py-2 border border-slate-300 text-slate-600 rounded-xl font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold shadow-md"
                >
                  Save Venue Specifications
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
