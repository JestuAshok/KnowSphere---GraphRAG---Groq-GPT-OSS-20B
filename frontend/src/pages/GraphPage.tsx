import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import ForceGraph2D from 'react-force-graph-2d';
import { Sidebar } from '../components/Sidebar';
import { MobileTabBar } from '../components/MobileTabBar';
import { graphApi, entitiesApi } from '../api';
import type { GraphNode, GraphEdge, NodeDetail } from '../types';
import { Search, X, ChevronRight, Layers, Table, ExternalLink, ZoomIn, ZoomOut, LocateFixed, RotateCcw } from 'lucide-react';

// Color map matching the reference image legend
const NODE_COLORS: Record<string, string> = {
  Employee: '#3B82F6',
  Team: '#14B8A6',
  Project: '#8B5CF6',
  Technology: '#F97316',
  Department: '#22C55E',
  Customer: '#EC4899',
  Document: '#6366F1',
  Product: '#F59E0B',
};

const NODE_TYPES = ['All', 'Employee', 'Team', 'Project', 'Technology', 'Department', 'Customer', 'Document'];
const TYPE_ORDER = ['Department', 'Team', 'Project', 'Technology', 'Employee', 'Customer', 'Document'];
const TYPE_DESCRIPTIONS: Record<string, string> = {
  Department: 'organizational homes',
  Team: 'working groups',
  Project: 'active initiatives',
  Technology: 'shared capabilities',
  Employee: 'people and owners',
  Customer: 'accounts and partners',
  Document: 'evidence sources',
};
const RELATIONSHIP_LABELS: Record<string, string> = {
  PART_OF: 'belongs to',
  DEPENDS_ON: 'depends on',
  USES: 'uses',
  WORKS_ON: 'works on',
  REPORTS_TO: 'reports to',
  SUPPORTS: 'supports',
  MENTIONED_IN: 'mentioned in',
  RELATED_TO: 'related to',
};

const formatRelationship = (type: string) => RELATIONSHIP_LABELS[type] || type.toLowerCase().replace(/_/g, ' ');

const getNodeSummary = (node: GraphNode): string => {
  const properties = node.properties || {};
  if (node.type === 'Project') {
    const department = typeof properties.department === 'string' ? properties.department : '';
    const technologies = Array.isArray(properties.technologies) ? properties.technologies.join(' · ') : '';
    return [department, technologies].filter(Boolean).join(' · ');
  }
  if (node.type === 'Team' && typeof properties.description === 'string') {
    return properties.description;
  }
  return '';
};

const NodeDetailPanel: React.FC<{
  node: GraphNode;
  detail: NodeDetail | null;
  onClose: () => void;
  onExpand: (nodeId: string) => void;
  onNavigate: (type: string, name: string) => void;
}> = ({ node, detail, onClose, onExpand, onNavigate }) => {
  const color = NODE_COLORS[node.type] || '#7C3AED';

  return (
    <div className="absolute top-0 right-0 w-72 h-full bg-white shadow-xl border-l border-gray-100 overflow-y-auto z-20 animate-slide-in-right">
      <div className="p-4 border-b border-gray-100 flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: `${color}20` }}>
            <div className="w-3 h-3 rounded-full" style={{ background: color }} />
          </div>
          <div>
            <div className="font-bold text-gray-900 text-sm">{node.label}</div>
            <div className="text-xs font-medium" style={{ color }}>{node.type}</div>
          </div>
        </div>
        <button onClick={onClose} className="p-1 rounded-lg hover:bg-gray-100 text-gray-400">
          <X size={16} />
        </button>
      </div>

      <div className="p-4 space-y-4">
        {/* Properties */}
        {node.properties && Object.keys(node.properties).length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Properties</h4>
            <div className="space-y-1.5">
              {Object.entries(node.properties).map(([k, v]) => (
                <div key={k} className="flex gap-2 text-xs">
                  <span className="text-gray-400 font-medium capitalize min-w-0 truncate">{k}:</span>
                  <span className="text-gray-700 min-w-0 truncate">{String(v)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Relationships */}
        {detail?.relationships && detail.relationships.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
              Relationships ({detail.relationships.length})
            </h4>
            <div className="space-y-1.5">
              {detail.relationships.slice(0, 10).map((rel, i) => (
                <div key={i} className="flex items-center gap-2 text-xs p-2 bg-gray-50 rounded-lg">
                  <span className="text-gray-400">{rel.direction === 'out' ? '→' : '←'}</span>
                  <span className="font-medium text-brand-600 uppercase text-[10px]">{rel.rel_type}</span>
                  <span className="text-gray-700 truncate flex-1">{rel.neighbor_name}</span>
                  <span className="text-gray-400 text-[10px]">{rel.neighbor_label}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="space-y-2 pt-2 border-t border-gray-100">
          <button
            onClick={() => onExpand(node.id)}
            className="w-full btn-ghost flex items-center justify-between text-sm border border-gray-200 rounded-xl px-3 py-2"
          >
            <span>Expand Neighbors</span> <ChevronRight size={14} />
          </button>
          <button
            onClick={() => onNavigate(node.type.toLowerCase(), node.label)}
            className="w-full btn-ghost flex items-center justify-between text-sm border border-gray-200 rounded-xl px-3 py-2"
          >
            <span>View Details</span> <ExternalLink size={14} />
          </button>
        </div>
      </div>
    </div>
  );
};

export const GraphPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const highlightIds = (searchParams.get('highlight') || '').split(',').filter(Boolean);

  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [nodeDetail, setNodeDetail] = useState<NodeDetail | null>(null);
  const [filterType, setFilterType] = useState('All');
  const [viewMode, setViewMode] = useState<'graph' | 'table'>('graph');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const fgRef = useRef<any>(null);

  const loadGraph = useCallback(async (type?: string) => {
    setLoading(true);
    setLoadError(false);
    try {
      const data = await graphApi.nodes(type === 'All' ? undefined : type);
      setNodes(data.nodes);
      setEdges(data.edges);
    } catch {
      setLoadError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadGraph(filterType); }, [filterType]);

  // If highlight IDs provided (from Ask page), load subgraph
  useEffect(() => {
    if (highlightIds.length > 0) {
      // highlight handled via filter
    }
  }, []);

  const handleNodeClick = useCallback(async (node: any) => {
    setSelectedNode(node);
    try {
      const detail = await graphApi.node(node.id);
      setNodeDetail(detail);
    } catch { setNodeDetail(null); }
  }, []);

  const handleExpand = async (nodeId: string) => {
    try {
      const data = await graphApi.neighbors(nodeId);
      setNodes((prev) => {
        const existing = new Set(prev.map((n) => n.id));
        const newNodes = data.nodes.filter((n: GraphNode) => !existing.has(n.id));
        return [...prev, ...newNodes];
      });
      setEdges((prev) => [...prev, ...data.edges]);
    } catch { }
  };

  const filteredNodes = nodes.filter((n) =>
    !search || n.label.toLowerCase().includes(search.toLowerCase())
  );

  const typeCounts = nodes.reduce<Record<string, number>>((counts, node) => {
    counts[node.type] = (counts[node.type] || 0) + 1;
    return counts;
  }, {});

  const resetGraph = () => {
    setSearch('');
    setFilterType('All');
    setSelectedNode(null);
    setNodeDetail(null);
    fgRef.current?.zoomToFit(500, 48);
  };

  const graphData = {
    nodes: filteredNodes.map((n) => ({
      ...n,
      color: NODE_COLORS[n.type] || '#7C3AED',
      highlighted: highlightIds.includes(n.id),
    })),
    links: edges.map((e) => ({ source: e.source, target: e.target, label: formatRelationship(e.type) })),
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="page-with-sidebar flex-1 flex flex-col" style={{ minHeight: '100vh' }}>
        {/* Top bar */}
        <div className="bg-white border-b border-gray-100 px-4 py-3 flex flex-wrap items-center gap-3">
          {/* View toggle */}
          <div className="flex bg-slate-100 rounded-xl p-1 gap-1">
            <button id="graph-view-btn" onClick={() => setViewMode('graph')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors
                ${viewMode === 'graph' ? 'bg-white shadow-sm text-brand-600' : 'text-gray-500'}`}>
              <Layers size={15} /> Graph View
            </button>
            <button id="table-view-btn" onClick={() => setViewMode('table')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors
                ${viewMode === 'table' ? 'bg-white shadow-sm text-brand-600' : 'text-gray-500'}`}>
              <Table size={15} /> Table View
            </button>
          </div>

          <div className="flex-1 min-w-0 relative max-w-xs">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input className="input-field pl-8 py-1.5 text-sm" placeholder="Search nodes..."
              value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>

          <select
            id="node-type-filter"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="input-field w-auto text-sm py-1.5"
          >
            {NODE_TYPES.map((t) => <option key={t}>{t}</option>)}
          </select>

          <div className="hidden md:flex items-center gap-1 border-l border-gray-200 pl-3">
            <button title="Zoom in" aria-label="Zoom in" onClick={() => fgRef.current?.zoom(1.35, 350)} className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 hover:text-brand-600">
              <ZoomIn size={16} />
            </button>
            <button title="Zoom out" aria-label="Zoom out" onClick={() => fgRef.current?.zoom(0.75, 350)} className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 hover:text-brand-600">
              <ZoomOut size={16} />
            </button>
            <button title="Center graph" aria-label="Center graph" onClick={() => fgRef.current?.zoomToFit(500, 48)} className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 hover:text-brand-600">
              <LocateFixed size={16} />
            </button>
            <button title="Reset filters" aria-label="Reset filters" onClick={resetGraph} className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 hover:text-brand-600">
              <RotateCcw size={16} />
            </button>
          </div>

          {/* Legend */}
          <div className="hidden lg:flex items-center gap-3 ml-auto">
            {Object.entries(NODE_COLORS).map(([type, color]) => (
              <div key={type} className="flex items-center gap-1.5 text-xs text-gray-500">
                <div className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
                {type}
              </div>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 relative overflow-hidden bg-slate-50" style={{ height: 'calc(100vh - 112px)' }}>
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="spinner" style={{ width: 32, height: 32 }} />
            </div>
          ) : loadError ? (
            <div className="flex items-center justify-center h-full bg-slate-50">
              <div className="text-center">
                <p className="font-semibold text-gray-800">The knowledge map is unavailable.</p>
                <p className="text-sm text-gray-500 mt-1">Check the backend and refresh this view.</p>
              </div>
            </div>
          ) : viewMode === 'graph' ? (
            <>
              <div className="absolute left-5 top-5 z-10 w-60 rounded-xl border border-slate-200 bg-white/95 p-4 text-slate-900 shadow-lg backdrop-blur">
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-brand-600">Knowledge graph</p>
                <p className="mt-1 text-sm text-slate-500">See how your organization is connected.</p>
                <div className="mt-4 grid grid-cols-2 gap-2 border-t border-slate-100 pt-3">
                  <div><p className="text-2xl font-semibold">{filteredNodes.length}</p><p className="text-[10px] uppercase tracking-wide text-slate-400">visible nodes</p></div>
                  <div><p className="text-2xl font-semibold">{edges.length}</p><p className="text-[10px] uppercase tracking-wide text-slate-400">connections</p></div>
                </div>
                <div className="mt-3 border-t border-slate-100 pt-3 text-[11px] leading-relaxed text-slate-500">
                  <span className="font-semibold text-slate-700">Read the flow:</span> departments → teams → projects → technologies
                </div>
              </div>
              <div className="absolute right-5 top-5 z-10 hidden w-48 rounded-xl border border-slate-200 bg-white/95 p-3 text-slate-700 shadow-lg backdrop-blur lg:block">
                <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">Layers</p>
                {TYPE_ORDER.filter((type) => typeCounts[type]).map((type) => (
                  <button key={type} onClick={() => setFilterType(type)} className="flex w-full items-center gap-2 rounded-lg px-1.5 py-1.5 text-left text-xs text-slate-600 hover:bg-slate-50">
                    <span className="h-2.5 w-2.5 rounded-full" style={{ background: NODE_COLORS[type] }} />
                    <span className="flex-1"><span className="block">{type}</span><span className="block text-[10px] text-slate-400">{TYPE_DESCRIPTIONS[type]}</span></span><span className="text-slate-400">{typeCounts[type]}</span>
                  </button>
                ))}
              </div>
              <ForceGraph2D
                ref={fgRef}
                graphData={graphData}
                d3AlphaDecay={0.03}
                d3VelocityDecay={0.45}
                cooldownTicks={120}
                onEngineStop={() => fgRef.current?.zoomToFit(600, 64)}
                nodeLabel={(n: any) => {
                  const summary = getNodeSummary(n);
                  return summary ? `${n.label} (${n.type}) - ${summary}` : `${n.label} (${n.type})`;
                }}
                nodeColor={(n: any) => n.highlighted ? '#FBBF24' : (NODE_COLORS[n.type] || '#7C3AED')}
                linkLabel={(l: any) => l.label}
                linkColor={(link: any) => link.source?.id === selectedNode?.id || link.target?.id === selectedNode?.id ? '#64748B' : '#CBD5E1'}
                linkWidth={(link: any) => link.source?.id === selectedNode?.id || link.target?.id === selectedNode?.id ? 2 : 1}
                linkDirectionalArrowLength={3}
                linkDirectionalArrowRelPos={1}
                linkCanvasObjectMode={() => 'after'}
                linkCanvasObject={(link: any, ctx, globalScale) => {
                  if (globalScale < 2 || !link.source?.x || !link.target?.x) return;
                  const text = link.label;
                  const x = link.source.x + (link.target.x - link.source.x) / 2;
                  const y = link.source.y + (link.target.y - link.source.y) / 2;
                  ctx.font = `${8 / globalScale}px Inter, sans-serif`;
                  ctx.fillStyle = '#64748B';
                  ctx.textAlign = 'center';
                  ctx.fillText(text, x, y);
                }}
                backgroundColor="#F8FAFC"
                onNodeClick={handleNodeClick}
                nodeCanvasObject={(node: any, ctx, globalScale) => {
                  const color = node.highlighted ? '#FBBF24' : (NODE_COLORS[node.type] || '#7C3AED');
                  const isPrimary = node.type === 'Department' || node.type === 'Team' || node.type === 'Project';
                  const isSelected = node.id === selectedNode?.id;
                  const r = node.type === 'Department' ? 10 : node.type === 'Team' ? 8 : node.type === 'Project' ? 7 : 5;

                  if (isSelected || node.highlighted) {
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, r + 5, 0, 2 * Math.PI);
                    ctx.fillStyle = `${color}25`;
                    ctx.fill();
                  }

                  ctx.beginPath();
                  ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
                  ctx.fillStyle = color;
                  ctx.fill();
                  ctx.strokeStyle = '#FFFFFF';
                  ctx.lineWidth = isSelected ? 2.5 : 1.5;
                  ctx.stroke();

                  if (globalScale > (isPrimary || isSelected ? 1.1 : 1.8)) {
                    const label = node.label.length > 24 ? `${node.label.slice(0, 23)}...` : node.label;
                    ctx.font = `${(isPrimary ? 11 : 10) / globalScale}px Inter, sans-serif`;
                    ctx.fillStyle = isSelected ? '#0F172A' : '#334155';
                    ctx.textAlign = 'center';
                    ctx.fillText(label, node.x, node.y + r + 10 / globalScale);

                    if (node.type === 'Project' && globalScale > 1.35) {
                      const summary = getNodeSummary(node);
                      if (summary) {
                        const shortSummary = summary.length > 32 ? `${summary.slice(0, 31)}...` : summary;
                        ctx.font = `${8 / globalScale}px Inter, sans-serif`;
                        ctx.fillStyle = '#64748B';
                        ctx.fillText(shortSummary, node.x, node.y + r + 20 / globalScale);
                      }
                    }
                  }
                }}
                width={selectedNode ? window.innerWidth - 224 - 288 : window.innerWidth - 224}
                height={window.innerHeight - 112}
              />
              {selectedNode && (
                <NodeDetailPanel
                  node={selectedNode}
                  detail={nodeDetail}
                  onClose={() => { setSelectedNode(null); setNodeDetail(null); }}
                  onExpand={handleExpand}
                  onNavigate={(type, name) => navigate(`/entities/${type}/${encodeURIComponent(name)}`)}
                />
              )}
            </>
          ) : (
            /* Table view */
            <div className="overflow-auto h-full p-4">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 px-3 text-gray-500 font-semibold">Name</th>
                    <th className="text-left py-2 px-3 text-gray-500 font-semibold">Type</th>
                    <th className="text-left py-2 px-3 text-gray-500 font-semibold">Properties</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredNodes.map((n) => (
                    <tr key={n.id} className="border-b border-gray-100 hover:bg-brand-50 cursor-pointer"
                      onClick={() => { setSelectedNode(n); graphApi.node(n.id).then(setNodeDetail).catch(() => {}); }}>
                      <td className="py-2 px-3 font-medium text-gray-900">{n.label}</td>
                      <td className="py-2 px-3">
                        <span className="badge" style={{ background: `${NODE_COLORS[n.type]}15`, color: NODE_COLORS[n.type] }}>
                          {n.type}
                        </span>
                      </td>
                      <td className="py-2 px-3 text-gray-500 text-xs truncate max-w-xs">
                        {Object.entries(n.properties || {}).slice(0, 2).map(([k, v]) => `${k}: ${v}`).join(', ')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
      <MobileTabBar />
    </div>
  );
};
