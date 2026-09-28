import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';
import { MobileTabBar } from '../components/MobileTabBar';
import { documentsApi } from '../api';
import type { DocumentMeta, DocumentDetail, ExtractedEntity } from '../types';
import { Upload, FileText, ArrowLeft, ExternalLink, CheckCircle, Clock, AlertCircle, Share2 } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import toast from 'react-hot-toast';

const NODE_COLORS: Record<string, string> = {
  Employee: '#3B82F6', Team: '#14B8A6', Project: '#8B5CF6',
  Technology: '#F97316', Department: '#22C55E', Customer: '#EC4899', Document: '#6366F1',
};

const StatusIcon: React.FC<{ status: string }> = ({ status }) => {
  if (status === 'done') return <CheckCircle size={14} className="text-green-500" />;
  if (status === 'processing') return <Clock size={14} className="text-amber-500 animate-spin" />;
  return <AlertCircle size={14} className="text-red-500" />;
};

const formatSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
};

// Inline entity highlighter
const HighlightedContent: React.FC<{ text: string; entities: ExtractedEntity[] }> = ({ text, entities }) => {
  if (!entities?.length) return <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans leading-relaxed">{text}</pre>;

  let result = text;
  const highlights: Array<{ start: number; end: number; type: string; name: string }> = [];

  entities.forEach((entity) => {
    const name = entity.canonical_name || entity.name;
    let idx = result.toLowerCase().indexOf(name.toLowerCase());
    while (idx !== -1) {
      highlights.push({ start: idx, end: idx + name.length, type: entity.type, name });
      idx = result.toLowerCase().indexOf(name.toLowerCase(), idx + 1);
    }
  });

  highlights.sort((a, b) => a.start - b.start);

  const parts: JSX.Element[] = [];
  let cursor = 0;
  highlights.forEach((h, i) => {
    if (h.start > cursor) parts.push(<span key={`t${i}`}>{result.slice(cursor, h.start)}</span>);
    const color = NODE_COLORS[h.type] || '#7C3AED';
    parts.push(
      <mark key={`h${i}`} className="rounded px-0.5 font-medium not-italic"
        style={{ background: `${color}25`, color, borderBottom: `1px solid ${color}60` }}>
        {result.slice(h.start, h.end)}
      </mark>
    );
    cursor = h.end;
  });
  if (cursor < result.length) parts.push(<span key="end">{result.slice(cursor)}</span>);

  return <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{parts}</div>;
};

export const DocumentsPage: React.FC = () => {
  const navigate = useNavigate();
  const [docs, setDocs] = useState<DocumentMeta[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<DocumentDetail | null>(null);
  const [activeTab, setActiveTab] = useState<'content' | 'entities' | 'metadata'>('content');
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  const loadDocs = () => {
    documentsApi.list().then(setDocs).finally(() => setLoading(false));
  };

  useEffect(() => { loadDocs(); }, []);

  const loadDoc = async (id: string) => {
    try {
      const d = await documentsApi.get(id);
      setSelectedDoc(d);
      setActiveTab('content');
    } catch { toast.error('Failed to load document'); }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    multiple: false,
    accept: { 'text/*': ['.txt', '.md'], 'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'] },
    onDrop: async (files) => {
      if (!files[0]) return;
      setUploading(true);
      try {
        await documentsApi.upload(files[0]);
        toast.success('Document uploaded! Processing in background...');
        setTimeout(loadDocs, 2000);
      } catch (err: any) {
        toast.error(err?.response?.data?.detail || 'Upload failed');
      } finally {
        setUploading(false);
      }
    },
  });

  const groupedEntities = selectedDoc?.entities?.reduce((acc, e) => {
    const type = e.type || 'Unknown';
    if (!acc[type]) acc[type] = [];
    acc[type].push(e);
    return acc;
  }, {} as Record<string, ExtractedEntity[]>) ?? {};

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="page-with-sidebar flex-1 flex">
        {/* Document list panel */}
        <div className={`${selectedDoc ? 'hidden md:flex' : 'flex'} flex-col w-full md:w-72 border-r border-gray-200 bg-white`}>
          <div className="p-4 border-b border-gray-100">
            <h1 className="text-lg font-bold text-gray-900">Documents</h1>
            <p className="text-xs text-gray-400 mt-0.5">{docs.length} files indexed</p>
          </div>

          {/* Upload drop zone */}
          <div {...getRootProps()} className={`mx-3 my-3 border-2 border-dashed rounded-xl p-3 text-center cursor-pointer transition-colors
            ${isDragActive ? 'border-brand-600 bg-brand-50' : 'border-gray-200 hover:border-brand-400 hover:bg-gray-50'}`}>
            <input {...getInputProps()} id="doc-upload-input" />
            <Upload size={18} className={`mx-auto mb-1 ${isDragActive ? 'text-brand-600' : 'text-gray-400'}`} />
            <p className="text-xs text-gray-500">
              {uploading ? 'Uploading...' : isDragActive ? 'Drop file here' : 'Drop file or click to upload'}
            </p>
          </div>

          {/* List */}
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className="flex justify-center py-8"><div className="spinner" /></div>
            ) : (
              docs.map((doc) => (
                <button key={doc.id} id={`doc-${doc.id}`}
                  onClick={() => loadDoc(doc.id)}
                  className={`w-full flex items-start gap-3 px-4 py-3 hover:bg-gray-50 text-left border-b border-gray-100 transition-colors
                    ${selectedDoc?.id === doc.id ? 'bg-brand-50 border-l-2 border-l-brand-600' : ''}`}>
                  <FileText size={18} className="text-brand-600 flex-shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-gray-800 text-sm truncate">{doc.filename}</div>
                    <div className="flex items-center gap-2 mt-0.5">
                      <StatusIcon status={doc.status} />
                      <span className="text-xs text-gray-400">{formatSize(doc.file_size)}</span>
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Document detail */}
        {selectedDoc ? (
          <div className="flex-1 flex flex-col min-w-0">
            {/* Header */}
            <div className="bg-white border-b border-gray-100 px-5 py-3 flex items-center gap-3">
              <button onClick={() => setSelectedDoc(null)} className="md:hidden p-1 rounded-lg hover:bg-gray-100">
                <ArrowLeft size={18} className="text-gray-500" />
              </button>
              <div className="flex-1 min-w-0">
                <div className="font-bold text-gray-900 truncate">{selectedDoc.filename}</div>
                <div className="text-xs text-gray-400 flex items-center gap-3 mt-0.5">
                  <span>Uploaded {new Date(selectedDoc.created_at).toLocaleDateString()}</span>
                  <span>{formatSize(selectedDoc.file_size)}</span>
                </div>
              </div>
              <a href={`#`} id="open-in-tab-btn"
                className="flex items-center gap-1.5 text-xs font-semibold text-brand-600 border border-brand-200 px-3 py-1.5 rounded-full hover:bg-brand-50">
                <ExternalLink size={12} /> Open in New Tab
              </a>
            </div>

            {/* Tabs */}
            <div className="bg-white border-b border-gray-100 flex px-5 gap-1">
              {(['content', 'entities', 'metadata'] as const).map((tab) => (
                <button key={tab} id={`doc-tab-${tab}`}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors capitalize
                    ${activeTab === tab ? 'border-brand-600 text-brand-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
                  {tab}
                </button>
              ))}
            </div>

            {/* Tab content */}
            <div className="flex-1 overflow-y-auto p-5">
              {activeTab === 'content' && (
                <HighlightedContent text={selectedDoc.content || 'No content extracted.'} entities={selectedDoc.entities || []} />
              )}

              {activeTab === 'entities' && (
                <div className="space-y-4">
                  {Object.entries(groupedEntities).map(([type, ents]) => (
                    <div key={type}>
                      <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2 flex items-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full" style={{ background: NODE_COLORS[type] || '#7C3AED' }} />
                        {type} ({ents.length})
                      </h3>
                      <div className="space-y-1.5">
                        {ents.map((e, i) => (
                          <button key={i}
                            onClick={() => navigate(`/entities/${type.toLowerCase()}/${encodeURIComponent(e.canonical_name || e.name)}`)}
                            className="w-full flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg hover:bg-brand-50 text-left text-sm text-gray-700 transition-colors group">
                            <Share2 size={12} className="text-gray-400 group-hover:text-brand-600" />
                            {e.canonical_name || e.name}
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                  {Object.keys(groupedEntities).length === 0 && (
                    <p className="text-gray-400 text-sm">No entities extracted yet.</p>
                  )}
                </div>
              )}

              {activeTab === 'metadata' && (
                <div className="space-y-2">
                  {[
                    ['ID', selectedDoc.id],
                    ['Filename', selectedDoc.filename],
                    ['Size', formatSize(selectedDoc.file_size)],
                    ['Status', selectedDoc.status],
                    ['Uploaded', new Date(selectedDoc.created_at).toLocaleString()],
                    ['Processed', selectedDoc.processed_at ? new Date(selectedDoc.processed_at).toLocaleString() : 'Pending'],
                  ].map(([k, v]) => (
                    <div key={k} className="flex gap-4 py-2 border-b border-gray-100 text-sm">
                      <span className="text-gray-400 font-medium w-28 flex-shrink-0">{k}</span>
                      <span className="text-gray-700 break-all">{v}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="hidden md:flex flex-1 items-center justify-center text-center text-gray-400">
            <div>
              <FileText size={40} className="mx-auto mb-3 opacity-30" />
              <p className="font-medium">Select a document to view</p>
              <p className="text-sm mt-1">Upload files on the left to start exploring</p>
            </div>
          </div>
        )}
      </main>
      <MobileTabBar />
    </div>
  );
};
