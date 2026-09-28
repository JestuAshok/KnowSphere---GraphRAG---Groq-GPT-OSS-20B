import React, { useEffect, useState } from 'react';
import { Sidebar } from '../components/Sidebar';
import { MobileTabBar } from '../components/MobileTabBar';
import { insightsApi } from '../api';
import type { TechProjectCount, DeptProjectCount, RelationshipCount, ActivityLog } from '../types';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';
import { Activity, FileInput, GitBranch, Cpu, Clock } from 'lucide-react';

const DONUT_COLORS = ['#7C3AED', '#4F46E5', '#3B82F6', '#14B8A6', '#22C55E', '#F97316'];

const formatRelative = (isoDate: string) => {
  const diff = Date.now() - new Date(isoDate).getTime();
  const mins = Math.floor(diff / 60000);
  const hrs = Math.floor(mins / 60);
  if (mins < 2) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
};

const ActivityIcon: React.FC<{ type: string }> = ({ type }) => {
  if (type === 'document_ingested') return <FileInput size={14} className="text-blue-500" />;
  if (type === 'entity_detected') return <Cpu size={14} className="text-orange-500" />;
  if (type === 'relationship_updated') return <GitBranch size={14} className="text-green-500" />;
  return <Activity size={14} className="text-gray-400" />;
};

export const InsightsPage: React.FC = () => {
  const [techData, setTechData] = useState<TechProjectCount[]>([]);
  const [deptData, setDeptData] = useState<DeptProjectCount[]>([]);
  const [relData, setRelData] = useState<RelationshipCount[]>([]);
  const [activity, setActivity] = useState<ActivityLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [timeRange, setTimeRange] = useState('Last 6 Months');

  useEffect(() => {
    setLoading(true);
    Promise.all([
      insightsApi.projectsByTechnology(),
      insightsApi.departmentProjects(),
      insightsApi.topRelationships(),
      insightsApi.recentActivity(),
    ]).then(([tech, dept, rel, act]) => {
      setTechData(tech);
      setDeptData(dept);
      setRelData(rel);
      setActivity(act);
    }).catch(() => {
      setError(true);
    }).finally(() => setLoading(false));
  }, [timeRange]);

  const totalProjects = deptData.reduce((s, d) => s + d.project_count, 0) || 1;

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="page-with-sidebar flex-1">
        <div className="page-content p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="section-title text-2xl">Insights & Analytics</h1>
              <p className="section-subtitle">Discover trends and key insights from your organizational knowledge.</p>
            </div>
            <select
              id="time-range-selector"
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="input-field w-auto text-sm"
            >
              {['Last 6 Months', 'Last 3 Months', 'Last 30 Days', 'All Time'].map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </div>

          {loading ? (
            <div className="flex justify-center py-20"><div className="spinner" style={{ width: 36, height: 36 }} /></div>
          ) : error ? (
            <div className="card text-center py-12">
              <p className="font-semibold text-gray-700">Insights could not be loaded.</p>
              <p className="text-sm text-gray-500 mt-1">Start Neo4j on localhost:7687 and try again.</p>
            </div>
          ) : (
            <>
              {/* Charts row */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                {/* Bar chart */}
                <div className="card">
                  <h2 className="section-title text-base mb-4">Projects by Technology</h2>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={techData} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
                      <XAxis dataKey="technology" tick={{ fontSize: 11, fill: '#6B7280' }}
                        tickFormatter={(v) => v.replace('Technology ', 'Tech ').replace('Tech W', 'W').replace('Tech V', 'V')} />
                      <YAxis tick={{ fontSize: 11, fill: '#6B7280' }} />
                      <Tooltip
                        contentStyle={{ borderRadius: 12, border: 'none', boxShadow: '0 4px 24px rgba(0,0,0,0.12)', fontSize: 12 }}
                        formatter={(v: number) => [v, 'Projects']}
                      />
                      <Bar dataKey="project_count" fill="#7C3AED" radius={[6, 6, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Donut chart */}
                <div className="card flex flex-col">
                  <h2 className="section-title text-base mb-4">Department-wise Projects</h2>
                  <div className="flex-1 flex items-center gap-4">
                    <ResponsiveContainer width="60%" height={180}>
                      <PieChart>
                        <Pie data={deptData} dataKey="project_count" nameKey="department"
                          cx="50%" cy="50%" innerRadius={50} outerRadius={75}
                          paddingAngle={3}>
                          {deptData.map((_, i) => (
                            <Cell key={i} fill={DONUT_COLORS[i % DONUT_COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(v: number) => [v, 'Projects']}
                          contentStyle={{ borderRadius: 12, border: 'none', boxShadow: '0 4px 24px rgba(0,0,0,0.12)', fontSize: 12 }} />
                      </PieChart>
                    </ResponsiveContainer>
                    {/* Legend */}
                    <div className="flex-1 space-y-2">
                      {deptData.map((d, i) => (
                        <div key={d.department} className="flex items-center justify-between text-xs">
                          <div className="flex items-center gap-2">
                            <div className="w-2.5 h-2.5 rounded-full" style={{ background: DONUT_COLORS[i % DONUT_COLORS.length] }} />
                            <span className="text-gray-600">{d.department}</span>
                          </div>
                          <span className="font-semibold text-gray-800">
                            {Math.round((d.project_count / totalProjects) * 100)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Bottom row */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Top relationships */}
                <div className="card">
                  <h2 className="section-title text-base mb-4">Top Relationships</h2>
                  <div className="space-y-3">
                    {relData.map((rel, i) => (
                      <div key={i} className="flex items-center gap-3">
                        <GitBranch size={14} className="text-brand-600 flex-shrink-0" />
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium text-gray-700">{rel.relationship_type}</span>
                            <span className="text-sm font-bold text-gray-900">{rel.count}</span>
                          </div>
                          <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                            <div className="h-full rounded-full bg-brand-600 transition-all duration-500"
                              style={{ width: `${Math.min((rel.count / (relData[0]?.count || 1)) * 100, 100)}%` }} />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recent Activity */}
                <div className="card">
                  <h2 className="section-title text-base mb-4">Recent Activity</h2>
                  <div className="space-y-3">
                    {activity.slice(0, 8).map((a) => (
                      <div key={a.id} className="flex items-start gap-3">
                        <div className="w-7 h-7 rounded-lg bg-gray-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <ActivityIcon type={a.event_type} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-gray-700 leading-snug">{a.description}</p>
                          <p className="text-xs text-gray-400 mt-0.5 flex items-center gap-1">
                            <Clock size={10} /> {formatRelative(a.created_at)}
                          </p>
                        </div>
                      </div>
                    ))}
                    {activity.length === 0 && (
                      <p className="text-gray-400 text-sm text-center py-4">No activity yet</p>
                    )}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </main>
      <MobileTabBar />
    </div>
  );
};
