
'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { LogOut, TrendingUp, Activity, PieChart as PieIcon, Zap, Terminal, Shield, Sparkles } from 'lucide-react';

// Get API base URL from environment
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export default function DashboardPage() {
  const { user, isLoading, signOut } = useAuth();
  const [profile, setProfile] = useState({ name: 'System Operator' });
  const [stats, setStats] = useState({
    totalTasks: 0,
    completed: 0,
    pending: 0,
    efficiency: "0%",
    weeklyStats: []
  });
  const [fetchError, setFetchError] = useState<string | null>(null);

  // Fetch stats and profile cache
  useEffect(() => {
    const saved = localStorage.getItem('operatorProfile');
    if (saved) {
      try {
        setProfile(JSON.parse(saved));
      } catch (e) {
        console.error("Profile parse error", e);
      }
    }

    const fetchStats = async () => {
      if (!user?.id) {
        console.log('[Dashboard] No user ID available');
        return;
      }

      try {
        console.log('[Dashboard] Fetching stats from:', `${API_BASE_URL}/api/tasks/stats?user_id=${user.id}`);
        const res = await fetch(`${API_BASE_URL}/api/tasks/stats?user_id=${user.id}`, {
          credentials: 'include'
        });

        console.log('[Dashboard] Response status:', res.status);

        if (res.ok) {
          const data = await res.json();
          console.log('[Dashboard] Stats received:', data);
          setStats(data);
          setFetchError(null);
        } else {
          const errorText = await res.text();
          console.error('[Dashboard] API Error:', res.status, errorText);
          setFetchError(`API Error: ${res.status}`);
        }
      } catch (error) {
        console.error('[Dashboard] Fetch error:', error);
        setFetchError('Connection failed - check if backend is running');
      }
    };

    if (!isLoading && user) {
      console.log('[Dashboard] User loaded, fetching stats...');
      fetchStats();
    }
  }, [user, isLoading]);

  const pieData = [
    { name: 'Completed', value: stats.completed || 1 },
    { name: 'Pending', value: stats.pending || 1 },
  ];

  const COLORS = ['#9333ea', 'rgba(147, 51, 234, 0.1)'];

  if (isLoading) return (
    <div className="h-screen bg-[#09090b] flex flex-col items-center justify-center gap-4">
      <div className="w-12 h-12 border-4 border-purple-500/20 border-t-purple-500 rounded-full animate-spin"></div>
      <div className="text-purple-500 font-black tracking-[0.5em] animate-pulse">BOOTING MISSION CONTROL...</div>
    </div>
  );

  return (
    <div className="p-6 lg:p-12 bg-[#09090b] min-h-screen text-white relative overflow-hidden">
      {/* Error Banner */}
      {fetchError && (
        <div className="fixed top-4 right-4 z-50 bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-2 rounded-lg text-xs font-black uppercase tracking-wider">
          {fetchError}
        </div>
      )}

      {/* Background Decor */}
      <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-purple-600/5 blur-[120px] rounded-full pointer-events-none"></div>

      {/* HEADER SECTION */}
      <header className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-center mb-16 gap-8">
        <div className="space-y-4">
          <div className="flex items-center gap-3">
             <div className="p-2 bg-purple-600/10 rounded-lg border border-purple-500/20">
               <Terminal size={16} className="text-purple-500" />
             </div>
             <p className="text-[10px] text-purple-500 font-black tracking-[0.4em] uppercase italic">Neural Link: Online</p>
          </div>
          <div>
            <h1 className="text-6xl font-black italic uppercase tracking-tighter leading-none bg-gradient-to-r from-white to-white/40 bg-clip-text text-transparent">
              Welcome, <span className="text-white">{profile.name.split(' ')[0]}</span>
            </h1>
            <p className="text-slate-500 mt-2 font-medium tracking-wide">Your operational efficiency is at <span className="text-purple-400 font-bold">{stats.efficiency}</span> this cycle.</p>
          </div>
        </div>

        <button
          onClick={signOut}
          className="group flex items-center gap-4 bg-[#111114] hover:bg-red-500 border border-white/5 hover:border-red-500 px-8 py-4 rounded-[2rem] transition-all duration-500 shadow-2xl"
        >
          <div className="flex flex-col items-end">
            <span className="text-[8px] font-black uppercase tracking-widest text-slate-500 group-hover:text-white/70">Secure Exit</span>
            <span className="text-[10px] font-black uppercase tracking-widest text-red-500 group-hover:text-white transition-colors">Abort Session</span>
          </div>
          <LogOut size={20} className="text-red-500 group-hover:text-white group-hover:translate-x-1 transition-all" />
        </button>
      </header>

      {/* STATS CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-16 relative z-10">
        {[
          { label: 'Total Missions', value: stats.totalTasks, icon: <Activity size={20}/>, color: 'text-blue-400', glow: 'shadow-blue-900/10' },
          { label: 'Successful', value: stats.completed, icon: <Zap size={20}/>, color: 'text-purple-500', glow: 'shadow-purple-900/20' },
          { label: 'Performance', value: stats.efficiency, icon: <TrendingUp size={20}/>, color: 'text-emerald-400', glow: 'shadow-emerald-900/10' },
          { label: 'Active Tasks', value: stats.pending, icon: <Sparkles size={20}/>, color: 'text-amber-400', glow: 'shadow-amber-900/10' },
        ].map((item, i) => (
          <div key={i} className={`bg-[#111114]/50 backdrop-blur-xl p-8 rounded-[3rem] border border-white/5 shadow-2xl relative overflow-hidden group hover:border-white/10 transition-all duration-500 ${item.glow}`}>
            <div className="relative z-10">
              <div className={`${item.color} mb-6 p-3 bg-white/5 w-fit rounded-2xl transition-transform group-hover:scale-110 duration-500`}>{item.icon}</div>
              <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] mb-2">{item.label}</p>
              <p className={`text-4xl font-black tracking-tighter italic ${item.color}`}>{item.value}</p>
            </div>
            {/* Holographic background icon */}
            <div className={`absolute -right-6 -bottom-6 opacity-[0.03] transition-all duration-700 group-hover:scale-125 ${item.color}`}>
               {React.cloneElement(item.icon as React.ReactElement, { size: 140 })}
            </div>
          </div>
        ))}
      </div>

      {/* GRAPHS SECTION */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 relative z-10 mb-20">

        {/* WEEKLY ACTIVITY */}
        <div className="lg:col-span-8 bg-[#111114]/50 backdrop-blur-xl p-10 rounded-[4rem] border border-white/5 shadow-2xl group">
          <div className="flex justify-between items-center mb-12">
            <div>
              <h2 className="text-sm font-black uppercase tracking-[0.3em] text-white italic">Operational Flow</h2>
              <p className="text-[10px] text-slate-600 font-bold uppercase mt-1">Activity per deployment cycle</p>
            </div>
            <div className="flex gap-2">
              <div className="h-1.5 w-1.5 rounded-full bg-purple-500"></div>
              <div className="h-1.5 w-1.5 rounded-full bg-purple-500/30"></div>
              <div className="h-1.5 w-1.5 rounded-full bg-purple-500/10"></div>
            </div>
          </div>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.weeklyStats.length > 0 ? stats.weeklyStats : [{name: 'Cycle 1', tasks: stats.totalTasks}]}>
                <defs>
                  <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#9333ea" stopOpacity={1} />
                    <stop offset="100%" stopColor="#9333ea" stopOpacity={0.4} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff" vertical={false} opacity={0.02} />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#4b5563', fontSize: 10, fontWeight: 'bold'}} />
                <YAxis hide />
                <Tooltip
                  cursor={{fill: 'rgba(255,255,255,0.02)'}}
                  contentStyle={{backgroundColor: '#0c0c0e', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '20px', fontSize: '10px', boxShadow: '0 20px 50px rgba(0,0,0,0.5)'}}
                />
                <Bar dataKey="tasks" fill="url(#barGradient)" radius={[12, 12, 4, 4]} barSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* DISTRIBUTION MAP */}
        <div className="lg:col-span-4 bg-[#111114]/50 backdrop-blur-xl p-10 rounded-[4rem] border border-white/5 shadow-2xl flex flex-col items-center">
          <div className="w-full mb-10">
            <h2 className="text-sm font-black uppercase tracking-[0.3em] text-white italic">Task Distribution</h2>
            <p className="text-[10px] text-slate-600 font-bold uppercase mt-1">Success vs Active Ratio</p>
          </div>

          <div className="h-64 w-full relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} innerRadius={80} outerRadius={110} paddingAngle={10} dataKey="value" strokeWidth={0}>
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>

            {/* Center HUD */}
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <Shield className="text-purple-500/20 absolute" size={140} />
              <div className="relative text-center">
                <span className="text-3xl font-black italic block bg-gradient-to-b from-white to-white/50 bg-clip-text text-transparent">
                  {stats.efficiency}
                </span>
                <span className="text-[9px] font-black text-purple-500 uppercase tracking-widest mt-1 block">Rating</span>
              </div>
            </div>
          </div>

          <div className="flex gap-8 w-full mt-12 justify-center">
            <div className="flex items-center gap-3">
              <div className="w-2.5 h-2.5 rounded-full bg-purple-600 shadow-[0_0_12px_rgba(147,51,234,0.6)]"></div>
              <span className="text-[10px] font-black uppercase text-slate-400 tracking-wider">Complete</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-2.5 h-2.5 rounded-full bg-white/10"></div>
              <span className="text-[10px] font-black uppercase text-slate-400 tracking-wider">Active</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

