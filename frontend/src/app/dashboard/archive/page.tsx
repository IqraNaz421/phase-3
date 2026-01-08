'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import {
  CheckCircle, RotateCcw, Trash2,
  History, Zap, Search, Database, ShieldCheck,
  Calendar, Clock, Filter, Archive, Download
} from 'lucide-react';

export default function MissionArchive() {
  const { user, isLoading } = useAuth();
  const [archivedTasks, setArchivedTasks] = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortBy, setSortBy] = useState("date");
  const [filterStatus, setFilterStatus] = useState("all");

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/tasks";

  // Load from localStorage
  useEffect(() => {
    const loadArchive = () => {
      const data = JSON.parse(localStorage.getItem('missionArchive') || '[]');
      // Sort: Latest first
      setArchivedTasks(data.sort((a: any, b: any) =>
        new Date(b.completedAt || 0).getTime() - new Date(a.completedAt || 0).getTime()
      ));
    };
    loadArchive();
  }, []);

  const handleRestore = async (task: any) => {
    if (!user?.id) return;

    try {
      // 1. Update backend state (Using PUT for task update) - fixed API endpoint
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/api/tasks/${task.id}?user_id=${user.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
           title: task.title,
           description: task.description || "",
           completed: false,
           due_date: task.due_date || null
        })
      });

      if (res.ok) {
        // 2. Remove from local archive
        const updatedArchive = archivedTasks.filter(t => t.id !== task.id);
        localStorage.setItem('missionArchive', JSON.stringify(updatedArchive));
        setArchivedTasks(updatedArchive);
        console.log(`Mission RESTORED: ${task.title}`);
      } else {
        // If backend update fails, at least update locally
        const updatedArchive = archivedTasks.filter(t => t.id !== task.id);
        localStorage.setItem('missionArchive', JSON.stringify(updatedArchive));
        setArchivedTasks(updatedArchive);
        console.log(`Mission RESTORED locally: ${task.title}`);
      }
    } catch (err) {
      console.error("Restore error:", err);
      alert("Failed to reactivate task. Please try again.");
    }
  };

  const purgeArchive = () => {
    if (confirm("SECURITY PROTOCOL: Are you sure you want to permanently WIPE the mission history?")) {
      localStorage.removeItem('missionArchive');
      setArchivedTasks([]);
    }
  };

  const exportArchive = () => {
    const dataStr = JSON.stringify(archivedTasks, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `mission-archive-${user?.email?.split('@')[0] || 'user'}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // Filter and sort logic
  const filteredTasks = archivedTasks
    .filter(t =>
      (t.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
       t.description?.toLowerCase().includes(searchTerm.toLowerCase())) &&
      (filterStatus === "all" || (filterStatus === "recent" && t.completedAt && new Date(t.completedAt) > new Date(Date.now() - 30*24*60*60*1000)))
    )
    .sort((a, b) => {
      if (sortBy === "date") {
        return new Date(b.completedAt || 0).getTime() - new Date(a.completedAt || 0).getTime();
      } else if (sortBy === "title") {
        return (a.title || "").localeCompare(b.title || "");
      }
      return 0;
    });

  if (isLoading) return (
    <div className="min-h-screen bg-gradient-to-br from-[#09090b] via-[#0b0b0d] to-[#09090b] flex items-center justify-center">
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-purple-500/30 border-t-purple-500 rounded-full animate-spin mx-auto mb-6"></div>
        <h2 className="text-2xl font-black text-white uppercase italic tracking-[0.2em]">LOADING MISSION ARCHIVE</h2>
        <p className="text-sm text-purple-400 mt-2">Authenticating temporal data stream...</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#09090b] text-slate-200">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* HEADER SECTION */}
        <header className="mb-8">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-white mb-2">Mission Archive</h1>
              <p className="text-sm text-slate-400">Historical data repository and mission recovery system</p>
            </div>

            <div className="flex gap-2">
              <button
                onClick={exportArchive}
                className="px-4 py-2 bg-white/10 border border-white/20 text-white rounded-md text-sm font-medium hover:bg-white/20 transition-colors"
              >
                Export Data
              </button>
              <button
                onClick={purgeArchive}
                className="px-4 py-2 bg-red-500/20 border border-red-500/30 text-red-400 rounded-md text-sm font-medium hover:bg-red-500/30 transition-colors"
              >
                Purge Records
              </button>
            </div>
          </div>
        </header>

        {/* SORT & FILTER SECTION */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-400">Sort by:</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="bg-white/10 border border-white/20 text-white rounded-md px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
                >
                  <option value="date" className="bg-[#111114] text-white">Date</option>
                  <option value="title" className="bg-[#111114] text-white">Title</option>
                </select>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-400">Filter:</span>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="bg-white/10 border border-white/20 text-white rounded-md px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
                >
                  <option value="all" className="bg-[#111114] text-white">All Missions</option>
                  <option value="recent" className="bg-[#111114] text-white">Recent (30 days)</option>
                </select>
              </div>
            </div>

            <div className="text-right">
              <p className="text-sm text-slate-400">Active Filters</p>
              <p className="text-sm font-semibold text-purple-400">{filteredTasks.length} records found</p>
            </div>
          </div>
        </div>

        {/* MISSION LIST */}
        <div className="space-y-4">
          {filteredTasks.length > 0 ? (
            filteredTasks.map((task, i) => (
              <div
                key={task.id || i}
                className="bg-white/5 border border-white/10 rounded-lg p-4 hover:border-purple-500/50 transition-all"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                      <h4 className="font-medium text-white">{task.title}</h4>
                      <span className="px-2 py-1 bg-purple-500/20 text-purple-300 text-xs rounded border border-purple-500/30">
                        ARCHIVED
                      </span>
                    </div>

                    <div className="flex items-center gap-4 text-sm text-slate-400">
                      <span>Completed: {task.completedAt ? new Date(task.completedAt).toLocaleDateString() : 'Legacy Data'}</span>
                      {task.due_date && (
                        <span>Target: {new Date(task.due_date).toLocaleDateString()}</span>
                      )}
                    </div>

                    {task.description && (
                      <p className="mt-2 text-sm text-slate-300 line-clamp-2">{task.description}</p>
                    )}
                  </div>

                  <button
                    onClick={() => handleRestore(task)}
                    className="ml-4 px-4 py-2 bg-purple-600 text-white rounded-md text-sm font-medium hover:bg-purple-700 transition-colors"
                  >
                    Re-Activate
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-12 bg-white/5 border border-white/10 rounded-lg">
              <div className="flex justify-center mb-4">
                <div className="w-12 h-12 bg-gradient-to-br from-purple-600 to-indigo-600 rounded-lg border border-purple-500/30 flex items-center justify-center">
                  <Database className="text-white" size={24} />
                </div>
              </div>
              <h3 className="text-lg font-medium text-white mb-2">No Mission Records Found</h3>
              <p className="text-sm text-slate-400 mb-4">No archived missions match your current filters</p>
              <div className="flex justify-center gap-3">
                <button
                  onClick={() => { setSearchTerm(''); setFilterStatus('all'); }}
                  className="px-4 py-2 bg-purple-600/20 border border-purple-500/30 text-purple-300 rounded-md text-sm font-medium hover:bg-purple-600 hover:text-white transition-colors"
                >
                  Clear Filters
                </button>
                <button
                  onClick={() => setFilterStatus('all')}
                  className="px-4 py-2 bg-white/10 border border-white/20 text-slate-300 rounded-md text-sm font-medium hover:bg-white/20 hover:text-white transition-colors"
                >
                  Show All
                </button>
              </div>
            </div>
          )}
        </div>

        {/* FOOTER INFO */}
        {archivedTasks.length > 0 && (
          <div className="mt-8 text-center text-slate-500">
            <p className="text-sm">Archive contains {archivedTasks.length} mission records • Last updated: {new Date().toLocaleDateString()}</p>
          </div>
        )}
      </div>
    </div>
  );
}