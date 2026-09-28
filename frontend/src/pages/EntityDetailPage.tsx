import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';
import { MobileTabBar } from '../components/MobileTabBar';
import { entitiesApi } from '../api';
import type { EntityDetail } from '../types';
import { Share2, ChevronRight, ArrowLeft, User, Briefcase, Cpu, Building2, Users, FileText } from 'lucide-react';

const NODE_COLORS: Record<string, string> = {
  employee: '#3B82F6', team: '#14B8A6', project: '#8B5CF6',
  technology: '#F97316', department: '#22C55E', customer: '#EC4899', document: '#6366F1',
};

const ENTITY_ICONS: Record<string, React.ReactNode> = {
  employee: <User size={20} />, team: <Users size={20} />, project: <Briefcase size={20} />,
  technology: <Cpu size={20} />, department: <Building2 size={20} />, document: <FileText size={20} />,
};

const TABS = ['Overview', 'Projects', 'Technologies', 'Documents', 'Relationships'] as const;

export const EntityDetailPage: React.FC = () => {
  const { type = '', id = '' } = useParams<{ type: string; id: string }>();
  const navigate = useNavigate();
  const [entity, setEntity] = useState<EntityDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<typeof TABS[number]>('Overview');

  useEffect(() => {
    setLoading(true);
    entitiesApi.get(type, id)
      .then(setEntity)
      .catch(() => setEntity(null))
      .finally(() => setLoading(false));
  }, [type, id]);

  const color = NODE_COLORS[type.toLowerCase()] || '#7C3AED';
  const name = entity?.properties?.name as string || id;
  const role = entity?.properties?.role as string;
  const description = entity?.properties?.description as string;
  const department = entity?.relationships?.find(r => r.rel_type === 'BELONGS_TO' || r.rel_type === 'PART_OF')?.related_name;
  const team = entity?.relationships?.find(r => r.rel_type === 'MEMBER_OF')?.related_name;

  // Related by category
  const relatedProjects = entity?.relationships?.filter(r => r.related_type === 'Project') ?? [];
  const relatedTechs = entity?.relationships?.filter(r => r.related_type === 'Technology') ?? [];
  const relatedDocs = entity?.relationships?.filter(r => r.related_type === 'Document') ?? [];

  // Group related entities
  const relatedByType = entity?.relationships?.reduce((acc, r) => {
    const t = r.related_type || 'Unknown';
    if (!acc[t]) acc[t] = [];
    acc[t].push(r);
    return acc;
  }, {} as Record<string, typeof entity.relationships>) ?? {};

  if (loading) {
    return (
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="page-with-sidebar flex-1 flex items-center justify-center">
          <div className="spinner" style={{ width: 36, height: 36 }} />
        </main>
      </div>
    );
  }

  if (!entity) {
    return (
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="page-with-sidebar flex-1 flex items-center justify-center">
          <div className="text-center text-gray-400">
            <p className="font-medium">Entity not found</p>
            <button onClick={() => navigate(-1)} className="btn-ghost mt-3 flex items-center gap-1 mx-auto">
              <ArrowLeft size={14} /> Go back
            </button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="page-with-sidebar flex-1">
        <div className="page-content p-6">
          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-sm text-gray-400 mb-4">
            <button onClick={() => navigate(-1)} className="hover:text-gray-600 capitalize">{type}</button>
            <ChevronRight size={14} />
            <span className="text-gray-700 font-medium">{name}</span>
          </div>

          <div className="flex flex-col lg:flex-row gap-6">
            {/* Main panel */}
            <div className="flex-1">
              {/* Entity header */}
              <div className="card mb-4">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 rounded-2xl flex items-center justify-center"
                      style={{ background: `${color}20` }}>
                      <span style={{ color }}>{ENTITY_ICONS[type.toLowerCase()] || <User size={20} />}</span>
                    </div>
                    <div>
                      <h1 className="text-2xl font-bold text-gray-900">{name}</h1>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="badge" style={{ background: `${color}15`, color }}>{entity.type}</span>
                        {role && <span className="badge badge-purple">{role}</span>}
                      </div>
                    </div>
                  </div>
                  <button
                    id="view-in-graph-btn"
                    onClick={() => navigate(`/graph?highlight=${entity.id}`)}
                    className="btn-secondary flex items-center gap-2 text-sm"
                  >
                    <Share2 size={14} /> View in Graph
                  </button>
                </div>

                {/* Tabs */}
                <div className="flex gap-1 border-t border-gray-100 pt-3 -mx-2">
                  {TABS.map((tab) => (
                    <button key={tab} id={`entity-tab-${tab.toLowerCase()}`}
                      onClick={() => setActiveTab(tab)}
                      className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors
                        ${activeTab === tab ? 'bg-brand-600 text-white' : 'text-gray-500 hover:bg-gray-100'}`}>
                      {tab}
                    </button>
                  ))}
                </div>
              </div>

              {/* Tab content */}
              {activeTab === 'Overview' && (
                <div className="card">
                  <h3 className="section-title text-base mb-4">About</h3>
                  <div className="space-y-3">
                    {description && (
                      <p className="text-sm text-gray-600 leading-relaxed">{description}</p>
                    )}
                    {department && (
                      <div className="flex gap-3 text-sm">
                        <span className="text-gray-400 font-medium w-28">Department</span>
                        <button onClick={() => navigate(`/entities/department/${encodeURIComponent(department)}`)}
                          className="text-brand-600 hover:underline">{department}</button>
                      </div>
                    )}
                    {team && (
                      <div className="flex gap-3 text-sm">
                        <span className="text-gray-400 font-medium w-28">Team</span>
                        <button onClick={() => navigate(`/entities/team/${encodeURIComponent(team)}`)}
                          className="text-brand-600 hover:underline">{team}</button>
                      </div>
                    )}
                    {Object.entries(entity.properties || {}).filter(([k]) => !['name', 'description'].includes(k)).map(([k, v]) => (
                      <div key={k} className="flex gap-3 text-sm">
                        <span className="text-gray-400 font-medium w-28 capitalize">{k}</span>
                        <span className="text-gray-700">{String(v)}</span>
                      </div>
                    ))}
                  </div>

                  {relatedProjects.length > 0 && (
                    <div className="mt-5">
                      <h4 className="text-sm font-semibold text-gray-700 mb-2">Key Projects</h4>
                      <div className="space-y-1.5">
                        {relatedProjects.map((r, i) => (
                          <button key={i} onClick={() => navigate(`/entities/project/${encodeURIComponent(r.related_name)}`)}
                            className="flex items-center gap-2 text-sm text-brand-600 hover:underline">
                            <Briefcase size={13} /> {r.related_name}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {relatedTechs.length > 0 && (
                    <div className="mt-4">
                      <h4 className="text-sm font-semibold text-gray-700 mb-2">Technologies</h4>
                      <div className="flex flex-wrap gap-2">
                        {relatedTechs.map((r, i) => (
                          <button key={i} onClick={() => navigate(`/entities/technology/${encodeURIComponent(r.related_name)}`)}
                            className="badge badge-purple hover:bg-brand-200">{r.related_name}</button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'Relationships' && (
                <div className="card">
                  <h3 className="section-title text-base mb-4">All Relationships</h3>
                  <div className="space-y-2">
                    {entity.relationships?.map((r, i) => (
                      <button key={i}
                        onClick={() => navigate(`/entities/${r.related_type.toLowerCase()}/${encodeURIComponent(r.related_name)}`)}
                        className="w-full flex items-center gap-3 p-2.5 bg-gray-50 rounded-xl hover:bg-brand-50 text-left transition-colors group">
                        <span className="text-gray-400 text-xs">{r.direction === 'out' ? '→' : '←'}</span>
                        <span className="badge-purple text-[10px] px-2 py-0.5 rounded-full font-mono">{r.rel_type}</span>
                        <span className="flex-1 text-sm text-gray-700">{r.related_name}</span>
                        <span className="text-xs text-gray-400">{r.related_type}</span>
                        <ChevronRight size={14} className="text-gray-300 group-hover:text-brand-600" />
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {activeTab !== 'Overview' && activeTab !== 'Relationships' && (
                <div className="card">
                  <h3 className="section-title text-base mb-4">{activeTab}</h3>
                  {(activeTab === 'Projects' ? relatedProjects
                    : activeTab === 'Technologies' ? relatedTechs
                    : relatedDocs).length === 0 ? (
                    <p className="text-gray-400 text-sm">No {activeTab.toLowerCase()} found.</p>
                  ) : (
                    <div className="space-y-2">
                      {(activeTab === 'Projects' ? relatedProjects : activeTab === 'Technologies' ? relatedTechs : relatedDocs)
                        .map((r, i) => (
                          <button key={i}
                            onClick={() => navigate(`/entities/${r.related_type.toLowerCase()}/${encodeURIComponent(r.related_name)}`)}
                            className="w-full flex items-center gap-2 p-2.5 bg-gray-50 rounded-xl hover:bg-brand-50 text-left text-sm text-gray-700 transition-colors">
                            {r.related_name}
                          </button>
                        ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Right panel — related entities */}
            <div className="w-full lg:w-64 space-y-4">
              {Object.entries(relatedByType).map(([type, rels]) => (
                <div key={type} className="card">
                  <h3 className="text-sm font-semibold text-gray-500 mb-3 flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full" style={{ background: NODE_COLORS[type.toLowerCase()] || '#7C3AED' }} />
                    {type}
                  </h3>
                  <div className="space-y-1.5">
                    {(rels ?? []).slice(0, 5).map((r, i) => (
                      <button key={i}
                        onClick={() => navigate(`/entities/${r.related_type.toLowerCase()}/${encodeURIComponent(r.related_name)}`)}
                        className="w-full text-left text-sm text-brand-600 hover:text-brand-800 flex items-center gap-1.5 py-0.5">
                        <span className="truncate">{r.related_name}</span>
                        <ChevronRight size={12} className="flex-shrink-0" />
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
      <MobileTabBar />
    </div>
  );
};
