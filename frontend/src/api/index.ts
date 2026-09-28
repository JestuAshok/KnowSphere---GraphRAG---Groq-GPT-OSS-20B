import apiClient from './client';
import type { AuthToken } from '../types';

export const authApi = {
  login: async (email: string, password: string): Promise<AuthToken> => {
    const res = await apiClient.post('/auth/login/json', { email, password });
    return res.data;
  },
  register: async (email: string, name: string, password: string): Promise<AuthToken> => {
    const res = await apiClient.post('/auth/register', { email, name, password });
    return res.data;
  },
  me: async () => {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },
};

export const statsApi = {
  overview: async () => {
    const res = await apiClient.get('/stats/overview');
    return res.data;
  },
};

export const askApi = {
  ask: async (question: string, session_id?: string) => {
    const res = await apiClient.post('/ask', { question, session_id });
    return res.data;
  },
};

export const chatApi = {
  history: async () => {
    const res = await apiClient.get('/chat/history');
    return res.data;
  },
  session: async (id: string) => {
    const res = await apiClient.get(`/chat/${id}`);
    return res.data;
  },
};

export const graphApi = {
  nodes: async (type?: string, limit = 200) => {
    const params: Record<string, string | number> = { limit };
    if (type && type !== 'All') params.type = type;
    const res = await apiClient.get('/graph/nodes', { params });
    return res.data;
  },
  node: async (id: string) => {
    const res = await apiClient.get(`/graph/node/${encodeURIComponent(id)}`);
    return res.data;
  },
  neighbors: async (id: string) => {
    const res = await apiClient.get(`/graph/neighbors/${encodeURIComponent(id)}`);
    return res.data;
  },
  path: async (fromId: string, toId: string) => {
    const res = await apiClient.get('/graph/path', { params: { from: fromId, to: toId } });
    return res.data;
  },
  subgraph: async (entityIds: string[]) => {
    const res = await apiClient.get('/graph/subgraph', { params: { entity_ids: entityIds.join(',') } });
    return res.data;
  },
};

export const documentsApi = {
  list: async () => {
    const res = await apiClient.get('/documents');
    return res.data;
  },
  get: async (id: string) => {
    const res = await apiClient.get(`/documents/${id}`);
    return res.data;
  },
  upload: async (file: File, onProgress?: (pct: number) => void) => {
    const form = new FormData();
    form.append('file', file);
    const res = await apiClient.post('/documents/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (onProgress && e.total) onProgress(Math.round((e.loaded * 100) / e.total));
      },
    });
    return res.data;
  },
};

export const insightsApi = {
  projectsByTechnology: async () => {
    const res = await apiClient.get('/insights/projects-by-technology');
    return res.data;
  },
  departmentProjects: async () => {
    const res = await apiClient.get('/insights/department-projects');
    return res.data;
  },
  topRelationships: async () => {
    const res = await apiClient.get('/insights/top-relationships');
    return res.data;
  },
  recentActivity: async (limit = 20) => {
    const res = await apiClient.get('/activity/recent', { params: { limit } });
    return res.data;
  },
};

export const entitiesApi = {
  get: async (type: string, nameOrId: string) => {
    const res = await apiClient.get(`/entities/${type}/${encodeURIComponent(nameOrId)}`);
    return res.data;
  },
};

export const dataSourcesApi = {
  list: async () => {
    const res = await apiClient.get('/datasources');
    return res.data;
  },
  create: async (name: string, source_type: string, config?: Record<string, unknown>) => {
    const res = await apiClient.post('/datasources', { name, source_type, config });
    return res.data;
  },
  sync: async (id: string) => {
    const res = await apiClient.post(`/datasources/${id}/sync`);
    return res.data;
  },
};
