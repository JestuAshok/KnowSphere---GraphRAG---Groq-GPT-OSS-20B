import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';
import { TopBar } from '../components/TopBar';
import { StatCard } from '../components/StatCard';
import { MobileTabBar } from '../components/MobileTabBar';
import { statsApi, chatApi } from '../api';
import type { StatsOverview, ChatSession } from '../types';
import {
  Users, Briefcase, Cpu, Building2, UserCheck, FileText,
  MessageSquare, Share2, Upload, BarChart2, ChevronRight, Clock
} from 'lucide-react';

const getGreeting = () => {
  const h = new Date().getHours();
  if (h < 12) return 'Good Morning';
  if (h < 17) return 'Good Afternoon';
  return 'Good Evening';
};

const formatRelative = (isoDate: string) => {
  const diff = Date.now() - new Date(isoDate).getTime();
  const mins = Math.floor(diff / 60000);
  const hrs = Math.floor(mins / 60);
  const days = Math.floor(hrs / 24);
  if (mins < 2) return 'just now';
  if (mins < 60) return `${mins} minutes ago`;
  if (hrs < 24) return `${hrs} hour${hrs > 1 ? 's' : ''} ago`;
  return `${days} day${days > 1 ? 's' : ''} ago`;
};

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem('ks_user') || '{"name":"User"}');
  const [stats, setStats] = useState<StatsOverview | null>(null);
  const [recentQs, setRecentQs] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      statsApi.overview().catch(() => null),
      chatApi.history().catch(() => []),
    ]).then(([s, q]) => {
      if (s) setStats(s);
      setRecentQs(q ?? []);
    }).finally(() => setLoading(false));
  }, []);

  const quickActions = [
    { label: 'Ask a Question', sub: 'Get instant answers', icon: <MessageSquare size={22} />, color: '#7C3AED', to: '/ask' },
    { label: 'Explore Graph', sub: 'Visualize relationships', icon: <Share2 size={22} />, color: '#4F46E5', to: '/graph' },
    { label: 'Upload Documents', sub: 'Inject new data', icon: <Upload size={22} />, color: '#0EA5E9', to: '/documents' },
    { label: 'View Insights', sub: 'See trends & analytics', icon: <BarChart2 size={22} />, color: '#22C55E', to: '/insights' },
  ];

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="page-with-sidebar flex-1">
        <TopBar />
        <div className="page-content p-6">
          {/* Greeting */}
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-gray-900">
              {getGreeting()}, {user.name}! 👋
            </h1>
            <p className="text-gray-500 text-sm mt-1">Explore your organization's knowledge graph.</p>
          </div>

          {/* Stat cards — row 1 */}
          {loading ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="card h-28 animate-pulse bg-gray-100" />
              ))}
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <StatCard title="Employees" value={stats?.employees ?? 0} change={12} icon={<Users size={20} />} color="#3B82F6" />
                <StatCard title="Projects" value={stats?.projects ?? 0} change={6} icon={<Briefcase size={20} />} color="#8B5CF6" />
                <StatCard title="Technologies" value={stats?.technologies ?? 0} change={9} icon={<Cpu size={20} />} color="#F97316" />
                <StatCard title="Departments" value={stats?.departments ?? 0} change={0} icon={<Building2 size={20} />} color="#22C55E" />
              </div>

              {/* Stat cards — row 2 */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
                <StatCard title="Customers" value={stats?.customers ?? 0} change={16} icon={<UserCheck size={20} />} color="#EC4899" />
                <StatCard title="Documents" value={stats?.documents ?? 0} change={18} icon={<FileText size={20} />} color="#6366F1" />
                {/* Quote card */}
                <div className="card bg-gradient-to-br from-brand-600 to-brand-800 col-span-2 md:col-span-1">
                  <p className="text-white/80 text-sm leading-relaxed">
                    "Connections <span className="text-white font-semibold">create opportunities.</span>"
                  </p>
                  <p className="text-white/50 text-xs mt-3">— KnowSphere Insight</p>
                </div>
              </div>
            </>
          )}

          {/* Quick Actions */}
          <div className="mb-6">
            <h2 className="section-title mb-3">Quick Actions</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {quickActions.map((a) => (
                <button
                  key={a.to}
                  id={`quick-action-${a.label.replace(/\s+/g, '-').toLowerCase()}`}
                  onClick={() => navigate(a.to)}
                  className="card card-hover flex flex-col items-start gap-3 text-left p-4 group"
                >
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center transition-transform group-hover:scale-110"
                    style={{ background: `${a.color}15` }}>
                    <span style={{ color: a.color }}>{a.icon}</span>
                  </div>
                  <div>
                    <div className="font-semibold text-gray-900 text-sm">{a.label}</div>
                    <div className="text-gray-400 text-xs mt-0.5">{a.sub}</div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Recent Questions */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="section-title">Recent Questions</h2>
              <button onClick={() => navigate('/ask')} className="text-brand-600 text-sm font-medium hover:underline flex items-center gap-1">
                See all <ChevronRight size={14} />
              </button>
            </div>
            {recentQs.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <MessageSquare size={32} className="mx-auto mb-2 opacity-40" />
                <p className="text-sm">No questions yet. <button onClick={() => navigate('/ask')} className="text-brand-600 font-medium hover:underline">Ask your first question →</button></p>
              </div>
            ) : (
              <div className="space-y-2">
                {recentQs.slice(0, 5).map((q) => (
                  <button
                    key={q.session_id}
                    id={`recent-q-${q.session_id}`}
                    onClick={() => navigate(`/ask?session=${q.session_id}`)}
                    className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-brand-50 text-left transition-colors group"
                  >
                    <div className="w-2 h-2 rounded-full bg-brand-600 flex-shrink-0" />
                    <span className="flex-1 text-sm text-gray-700 truncate">{q.question}</span>
                    <span className="text-xs text-gray-400 flex-shrink-0 flex items-center gap-1">
                      <Clock size={11} /> {formatRelative(q.updated_at)}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
      <MobileTabBar />
    </div>
  );
};
