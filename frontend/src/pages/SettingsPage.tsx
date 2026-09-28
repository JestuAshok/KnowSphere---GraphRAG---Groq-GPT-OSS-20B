import React, { useEffect, useState } from 'react';
import { Sidebar } from '../components/Sidebar';
import { MobileTabBar } from '../components/MobileTabBar';
import { dataSourcesApi, documentsApi } from '../api';
import type { DataSource } from '../types';
import { CheckCircle, XCircle, RefreshCw, Plus, Clock, Upload } from 'lucide-react';
import toast from 'react-hot-toast';
import { useDropzone } from 'react-dropzone';

const DS_ICONS: Record<string, string> = {
  sharepoint: '🔷', confluence: '🔵', google_drive: '🟢',
  postgres: '🐘', neo4j: '🔮', custom_api: '⚙️', file_upload: '📁',
};

const DS_DESCRIPTIONS: Record<string, string> = {
  sharepoint: 'Microsoft SharePoint integration for document ingestion',
  confluence: 'Atlassian Confluence pages and spaces',
  google_drive: 'Google Drive documents and folders',
  postgres: 'PostgreSQL database connector',
  neo4j: 'Neo4j knowledge graph (primary store)',
  custom_api: 'Custom REST API connector',
};

const DataSourceCard: React.FC<{
  source: DataSource;
  onSync: (id: string) => void;
}> = ({ source, onSync }) => {
  const isConnected = source.status === 'connected';
  const [syncing, setSyncing] = useState(false);

  const handleSync = async () => {
    setSyncing(true);
    await onSync(source.id);
    setSyncing(false);
  };

  return (
    <div className="card card-hover flex items-start gap-4" id={`ds-card-${source.source_type}`}>
      <div className="w-12 h-12 rounded-xl bg-gray-50 flex items-center justify-center text-2xl flex-shrink-0">
        {DS_ICONS[source.source_type] || '🔌'}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-semibold text-gray-900">{source.name}</span>
          <div className={`flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full
            ${isConnected ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
            {isConnected ? <CheckCircle size={11} /> : <XCircle size={11} />}
            {isConnected ? 'Connected' : 'Not Connected'}
          </div>
        </div>
        <p className="text-xs text-gray-400">{DS_DESCRIPTIONS[source.source_type] || 'Data connector'}</p>
        {source.last_sync && (
          <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
            <Clock size={10} /> Last sync: {new Date(source.last_sync).toLocaleDateString()}
          </p>
        )}
      </div>
      <button
        id={`ds-sync-${source.source_type}`}
        onClick={handleSync}
        disabled={syncing}
        className={`flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-full border transition-colors flex-shrink-0
          ${isConnected
            ? 'border-brand-200 text-brand-600 hover:bg-brand-50'
            : 'border-gray-200 text-gray-500 hover:bg-gray-50'}`}
      >
        {syncing ? <RefreshCw size={12} className="animate-spin" /> : isConnected ? <RefreshCw size={12} /> : <Plus size={12} />}
        {isConnected ? 'Sync' : 'Connect'}
      </button>
    </div>
  );
};

export const SettingsPage: React.FC = () => {
  const [sources, setSources] = useState<DataSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  const loadSources = () => {
    dataSourcesApi.list().then(setSources).finally(() => setLoading(false));
  };

  useEffect(() => { loadSources(); }, []);

  const handleSync = async (id: string) => {
    try {
      await dataSourcesApi.sync(id);
      toast.success('Sync triggered!');
      loadSources();
    } catch { toast.error('Sync failed'); }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    multiple: false,
    onDrop: async (files) => {
      if (!files[0]) return;
      setUploading(true);
      try {
        await documentsApi.upload(files[0]);
        toast.success('Document uploaded and queued for ingestion!');
      } catch (err: any) {
        toast.error(err?.response?.data?.detail || 'Upload failed');
      } finally {
        setUploading(false);
      }
    },
  });

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="page-with-sidebar flex-1">
        <div className="page-content p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="section-title text-2xl">Data Sources</h1>
              <p className="section-subtitle">Manage your data sources and integrations.</p>
            </div>
            <button id="add-datasource-btn" className="btn-primary flex items-center gap-2">
              <Plus size={16} /> Add Data Source
            </button>
          </div>

          {/* File Upload Section */}
          <div className="card mb-6">
            <h2 className="section-title text-base mb-3">Quick Document Upload</h2>
            <p className="text-sm text-gray-500 mb-3">
              Upload a file to trigger the full ingestion pipeline: extract → embed → graph.
            </p>
            <div {...getRootProps()} className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors
              ${isDragActive ? 'border-brand-600 bg-brand-50' : 'border-gray-200 hover:border-brand-400 hover:bg-gray-50'}`}>
              <input {...getInputProps()} id="settings-upload-input" />
              <Upload size={28} className={`mx-auto mb-2 ${isDragActive ? 'text-brand-600' : 'text-gray-300'}`} />
              <p className="text-sm font-medium text-gray-600">
                {uploading ? 'Uploading...' : isDragActive ? 'Drop file here' : 'Drag & drop a file or click to browse'}
              </p>
              <p className="text-xs text-gray-400 mt-1">Supports: .txt, .md, .pdf, .docx, .xlsx</p>
            </div>
          </div>

          {/* Data Source Cards */}
          <h2 className="section-title text-base mb-3">Connectors</h2>
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[...Array(6)].map((_, i) => <div key={i} className="card h-24 animate-pulse bg-gray-100" />)}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {sources.map((s) => (
                <DataSourceCard key={s.id} source={s} onSync={handleSync} />
              ))}
            </div>
          )}
        </div>
      </main>
      <MobileTabBar />
    </div>
  );
};
