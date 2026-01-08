/**
 * BacklogSidebar Widget
 *
 * Displays unscheduled tasks that can be quickly scheduled via drag-drop or click.
 * Part of the Phase 3 widget requirements.
 */

'use client';

import React, { useState, useCallback } from 'react';
import { Calendar, Clock, GripVertical, Plus, Sparkles, AlertCircle, ChevronUp, ChevronDown } from 'lucide-react';

interface Task {
  id: string;
  title: string;
  description?: string;
  completed: boolean;
  due_date?: string;
  created_at?: string;
}

interface BacklogSidebarProps {
  tasks: Task[];
  onScheduleTask: (taskId: string, date: string) => Promise<void>;
  onCreateTask?: () => void;
  isLoading?: boolean;
}

export default function BacklogSidebar({ tasks, onScheduleTask, onCreateTask, isLoading = false }: BacklogSidebarProps) {
  const [expanded, setExpanded] = useState(true);
  const [draggingTask, setDraggingTask] = useState<string | null>(null);
  const [schedulingTask, setSchedulingTask] = useState<string | null>(null);

  // Filter unscheduled tasks (no due_date)
  const unscheduledTasks = tasks.filter(task => !task.due_date && !task.completed);
  const scheduledCount = tasks.filter(task => task.due_date && !task.completed).length;

  // Handle quick schedule to today
  const handleQuickSchedule = useCallback(async (taskId: string) => {
    if (!onScheduleTask) return;
    setSchedulingTask(taskId);
    try {
      const today = new Date().toISOString().split('T')[0];
      await onScheduleTask(taskId, today);
    } finally {
      setSchedulingTask(null);
    }
  }, [onScheduleTask]);

  // Handle drag start
  const handleDragStart = (e: React.DragEvent, taskId: string) => {
    setDraggingTask(taskId);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', taskId);
  };

  // Handle drag end
  const handleDragEnd = () => {
    setDraggingTask(null);
  };

  // Handle drag over (allow drop)
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  // Handle drop on calendar (handled by parent)
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const taskId = e.dataTransfer.getData('text/plain');
    // The parent component will handle the actual scheduling
    // This is a placeholder for visual feedback
    setDraggingTask(null);
  };

  return (
    <div className="bg-[#111114] border border-white/5 rounded-[24px] p-5 flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-orange-500/10 border border-orange-500/20">
            <AlertCircle size={16} className="text-orange-500" />
          </div>
          <div>
            <h3 className="text-xs font-black text-white uppercase tracking-widest italic">
              Backlog
            </h3>
            <p className="text-[9px] text-slate-500 uppercase tracking-wider">
              {unscheduledTasks.length} unscheduled
            </p>
          </div>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="p-1.5 rounded-lg hover:bg-white/5 text-slate-500 hover:text-white transition-all"
        >
          {expanded ? (
            <ChevronDown size={14} />
          ) : (
            <ChevronUp size={14} />
          )}
        </button>
      </div>

      {/* Progress indicator */}
      <div className="mb-4">
        <div className="flex justify-between text-[9px] text-slate-500 uppercase tracking-wider mb-2">
          <span>Scheduled</span>
          <span>{scheduledCount} tasks</span>
        </div>
        <div className="h-1 bg-white/5 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-orange-500 to-purple-500 rounded-full transition-all duration-500"
            style={{
              width: `${scheduledCount > 0 ? Math.min((scheduledCount / Math.max(tasks.filter(t => !t.completed).length, 1)) * 100, 100) : 0}%`
            }}
          />
        </div>
      </div>

      {/* Expandable content */}
      {expanded && (
        <div className="flex-1 overflow-y-auto custom-scrollbar">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-8 gap-3">
              <div className="w-6 h-6 border-2 border-orange-500/20 border-t-orange-500 rounded-full animate-spin" />
              <span className="text-[10px] text-slate-500 uppercase tracking-widest">
                Loading backlog...
              </span>
            </div>
          ) : unscheduledTasks.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 gap-3 text-center">
              <div className="p-3 rounded-full bg-green-500/10 border border-green-500/20">
                <Sparkles size={20} className="text-green-500" />
              </div>
              <p className="text-xs text-slate-400 italic">
                All tasks scheduled!
              </p>
              <p className="text-[9px] text-slate-600 uppercase tracking-wider">
                No backlog items
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {unscheduledTasks.map((task, index) => (
                <div
                  key={task.id}
                  draggable
                  onDragStart={(e) => handleDragStart(e, task.id)}
                  onDragEnd={handleDragEnd}
                  onDragOver={handleDragOver}
                  onDrop={handleDrop}
                  className={`
                    group relative p-3 rounded-xl border border-white/5
                    bg-black/20 hover:bg-orange-500/5 hover:border-orange-500/20
                    transition-all cursor-grab active:cursor-grabbing
                    ${draggingTask === task.id ? 'opacity-50 scale-95' : 'opacity-100'}
                  `}
                >
                  {/* Drag handle */}
                  <div className="absolute left-1 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <GripVertical size={12} className="text-slate-500" />
                  </div>

                  {/* Task content */}
                  <div className="pl-4">
                    <h4 className={`
                      text-xs font-bold truncate
                      ${task.completed ? 'text-slate-500 line-through' : 'text-white'}
                    `}>
                      {task.title}
                    </h4>
                    {task.description && (
                      <p className="text-[9px] text-slate-500 truncate mt-0.5">
                        {task.description}
                      </p>
                    )}

                    {/* Quick actions */}
                    <div className="flex items-center gap-2 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => handleQuickSchedule(task.id)}
                        disabled={schedulingTask === task.id}
                        className="flex items-center gap-1 px-2 py-1 rounded-lg bg-orange-500/10 hover:bg-orange-500/20 border border-orange-500/20 text-[9px] font-black uppercase text-orange-400 transition-all"
                      >
                        {schedulingTask === task.id ? (
                          <div className="w-3 h-3 border-1 border-orange-500/50 border-t-orange-500 rounded-full animate-spin" />
                        ) : (
                          <Calendar size={10} />
                        )}
                        Today
                      </button>
                      <button
                        onClick={() => onCreateTask?.()}
                        className="flex items-center gap-1 px-2 py-1 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-[9px] font-black uppercase text-slate-400 transition-all"
                      >
                        <Plus size={10} />
                        Edit
                      </button>
                    </div>
                  </div>

                  {/* Status indicator */}
                  <div className="absolute right-2 top-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse" />
                  </div>
                </div>
              ))}

              {/* Drag instruction */}
              <div className="flex items-center justify-center gap-2 py-3 text-[9px] text-slate-600 uppercase tracking-wider">
                <GripVertical size={12} />
                Drag to calendar to schedule
              </div>
            </div>
          )}
        </div>
      )}

      {/* Footer stats */}
      <div className="mt-4 pt-4 border-t border-white/5">
        <div className="flex items-center justify-between text-[9px]">
          <span className="text-slate-500 uppercase tracking-wider">Efficiency</span>
          <span className="text-orange-500 font-black">
            {tasks.length > 0
              ? `${Math.round((tasks.filter(t => t.completed).length / tasks.length) * 100)}%`
              : '0%'}
          </span>
        </div>
      </div>
    </div>
  );
}

// Chevron icons (inline to avoid additional imports)
// Removed - now using lucide-react imports
