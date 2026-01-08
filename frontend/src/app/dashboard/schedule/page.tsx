/**
 * Schedule Page
 *
 * Mission scheduling and task management interface with calendar view
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import {
  ChevronLeft, ChevronRight, Calendar as CalendarIcon,
  Clock, Plus, Zap, AlertCircle, Calendar
} from 'lucide-react';
import BacklogSidebar from '@/components/widgets/BacklogSidebar';

export default function SchedulePage() {
  const { user, isLoading: authLoading } = useAuth();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Calendar dates calculate karne ki logic
  const daysInMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0).getDate();
  const firstDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1).getDay();
  const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

  const days = Array.from({ length: daysInMonth }, (_, i) => i + 1);
  const blanks = Array.from({ length: firstDayOfMonth }, (_, i) => i);

  // API base URL from environment
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  // Fetch real tasks from the database
  useEffect(() => {
    const fetchTasks = async () => {
      if (!user?.id) {
        console.log('[Calendar] No user ID available');
        return;
      }

      try {
        setLoading(true);
        console.log('[Calendar] Fetching tasks for user:', user.id);

        // Use the same API as My Tasks page
        const response = await fetch(`${API_BASE_URL}/api/tasks/?user_id=${user.id}`, {
          credentials: 'include'
        });

        console.log('[Calendar] Response status:', response.status);

        if (response.ok) {
          const data = await response.json();
          console.log('[Calendar] Fetched Tasks for Calendar:', data);
          console.log('[Calendar] Tasks count:', data.length);
          console.log('[Calendar] Tasks with due_date:', data.filter((t: any) => t.due_date));
          setTasks(data);
        } else {
          console.error('[Calendar] Failed to fetch tasks:', response.status);
          setTasks([]);
        }
      } catch (error) {
        console.error('[Calendar] Error fetching tasks:', error);
        setTasks([]);
      } finally {
        setLoading(false);
      }
    };

    if (!authLoading && user?.id) {
      fetchTasks();
    }
  }, [user, authLoading, API_BASE_URL]);

  // Handle task date update (for BacklogSidebar)
  const handleScheduleTask = async (taskId: string, date: string) => {
    if (!date || !user?.id) return;

    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/tasks/${taskId}?user_id=${user.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          due_date: new Date(date).toISOString()
        }),
        credentials: 'include'
      });

      if (response.ok) {
        // Update local tasks state
        setTasks(prev => prev.map(t =>
          t.id === taskId ? { ...t, due_date: date } : t
        ));
        console.log('[Calendar] Task scheduled successfully');
      } else {
        console.error('[Calendar] Failed to schedule task:', response.status);
      }
    } catch (error) {
      console.error('[Calendar] Error scheduling task:', error);
    } finally {
      setLoading(false);
    }
  };

  // Filter tasks for the current month and map to calendar dates
  const getTasksForDay = (day: number) => {
    if (!tasks || tasks.length === 0) {
      return [];
    }

    const currentYear = currentDate.getFullYear();
    const currentMonth = currentDate.getMonth();

    const filtered = tasks.filter(task => {
      if (!task.due_date) {
        return false;
      }

      const taskDate = new Date(task.due_date);
      return taskDate.getDate() === day &&
             taskDate.getMonth() === currentMonth &&
             taskDate.getFullYear() === currentYear;
    });

    return filtered;
  };

  // Get upcoming tasks (next 7 days)
  const getUpcomingTasks = () => {
    if (!tasks || tasks.length === 0) {
      return [];
    }

    const today = new Date();
    const nextWeek = new Date();
    nextWeek.setDate(today.getDate() + 7);

    const upcoming = tasks
      .filter(task => {
        if (!task.due_date) return false;
        const taskDate = new Date(task.due_date);
        const isUpcoming = taskDate >= today && taskDate <= nextWeek;
        return isUpcoming;
      })
      .sort((a, b) => new Date(a.due_date).getTime() - new Date(b.due_date).getTime())
      .slice(0, 5); // Limit to 5 upcoming tasks

    return upcoming;
  };

  const navigateMonth = (direction: 'prev' | 'next') => {
    setCurrentDate(prev => {
      const newDate = new Date(prev);
      newDate.setMonth(prev.getMonth() + (direction === 'next' ? 1 : -1));
      return newDate;
    });
  };

  return (
    <div className="min-h-screen bg-[#09090b] text-slate-200">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* HEADER */}
        <header className="mb-8">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-white mb-2">Mission Schedule</h1>
              <p className="text-sm text-slate-400">Temporal objective tracking and task management</p>
            </div>
            <div className="flex gap-2">
              <button className="px-4 py-2 bg-purple-600/20 border border-purple-500/30 text-purple-300 rounded-md text-sm font-medium hover:bg-purple-600 hover:text-white transition-colors">
                <Plus size={16} className="inline mr-2" /> New Entry
              </button>
            </div>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* LEFT: CALENDAR GRID */}
          <div className="lg:col-span-2 bg-white/5 border border-white/10 rounded-lg p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <CalendarIcon className="text-purple-400" size={24} />
                <div>
                  <h2 className="font-semibold text-white">{monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}</h2>
                  <p className="text-sm text-slate-400">Drag tasks to schedule</p>
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => navigateMonth('prev')}
                  className="p-2 hover:bg-white/10 rounded-md border border-white/20 text-slate-400 hover:text-white transition-colors"
                >
                  <ChevronLeft size={20} />
                </button>
                <button
                  onClick={() => navigateMonth('next')}
                  className="p-2 hover:bg-white/10 rounded-md border border-white/20 text-slate-400 hover:text-white transition-colors"
                >
                  <ChevronRight size={20} />
                </button>
              </div>
            </div>

            {/* DAYS NAME */}
            <div className="grid grid-cols-7 gap-2 mb-3">
              {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(d => (
                <div key={d} className="text-xs text-slate-400 font-medium text-center">{d}</div>
              ))}
            </div>

            {/* DATES GRID */}
            <div className="grid grid-cols-7 gap-2">
              {blanks.map(b => <div key={`b-${b}`} className="aspect-square"></div>)}
              {days.map(d => {
                const dayTasks = getTasksForDay(d);
                const hasTasks = dayTasks.length > 0;
                const today = new Date();
                const isToday = d === today.getDate() &&
                               currentDate.getMonth() === today.getMonth() &&
                               currentDate.getFullYear() === today.getFullYear();

                return (
                  <div
                    key={d}
                    className={`aspect-square border border-white/[0.03] rounded-lg flex flex-col items-center justify-center relative cursor-pointer transition-all hover:bg-purple-600/10 hover:border-purple-500/30 ${
                      isToday ? 'bg-purple-600/10 border-purple-500/50' : 'bg-white/5'
                    }`}
                  >
                    <span className={`text-sm font-medium ${
                      isToday ? 'text-purple-400' : hasTasks ? 'text-white' : 'text-slate-400'
                    }`}>
                      {d}
                    </span>
                    {hasTasks && (
                      <div className="flex items-center gap-1 mt-1">
                        {dayTasks.slice(0, 2).map((task, idx) => (
                          <div
                            key={idx}
                            className={`w-2 h-2 rounded-full ${
                              task.completed
                                ? 'bg-green-500'
                                : 'bg-purple-500'
                            }`}
                            title={task.title}
                          ></div>
                        ))}
                        {dayTasks.length > 2 && (
                          <span className="text-[10px] text-slate-400">+{dayTasks.length - 2}</span>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* RIGHT: WIDGETS PANEL */}
          <div className="space-y-6">
            {/* BACKLOG SIDEBAR WIDGET */}
            <div className="bg-white/5 border border-white/10 rounded-lg p-4">
              <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
                <AlertCircle size={18} className="text-orange-400" />
                Backlog
              </h3>
              <BacklogSidebar
                tasks={tasks}
                onScheduleTask={handleScheduleTask}
                isLoading={loading}
              />
            </div>

            {/* UPCOMING BRIEFING */}
            <div className="bg-white/5 border border-white/10 rounded-lg p-4">
              <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
                <Clock size={18} className="text-purple-400" />
                Upcoming Intel
              </h3>
              <div className="space-y-3">
                {getUpcomingTasks().length > 0 ? getUpcomingTasks().map((task, i) => {
                  const taskDate = new Date(task.due_date);
                  const day = taskDate.getDate();
                  const month = taskDate.toLocaleString('default', { month: 'short' });

                  return (
                    <div key={task.id || i} className="border border-white/20 rounded-md p-3 hover:border-purple-500/40 transition-all">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-xs text-slate-400">{month} {day}, {taskDate.getFullYear()}</p>
                          <h4 className="text-sm font-medium text-white mt-1">{task.title}</h4>
                        </div>
                        <div className={`w-2 h-2 rounded-full ${task.completed ? 'bg-green-500' : 'bg-purple-500'}`}></div>
                      </div>
                    </div>
                  );
                }) : (
                  <p className="text-sm text-slate-400 italic">No upcoming tasks</p>
                )}
              </div>
            </div>

            {/* OPERATIONAL TIP */}
            <div className="bg-gradient-to-br from-purple-600/10 to-indigo-600/10 border border-purple-500/20 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <Zap className="text-purple-400 mt-0.5" size={18} />
                <div>
                  <p className="text-xs font-semibold text-purple-400 uppercase tracking-wider">Operational Tip</p>
                  <p className="text-xs text-slate-400 mt-1 leading-relaxed">Drag unscheduled tasks from the Backlog widget onto calendar dates to quickly schedule them.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}