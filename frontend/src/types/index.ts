// ─── Auth ──────────────────────────────────────────
export interface User {
  id: string;
  email: string;
  name: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  user_id: string;
  name: string;
  email: string;
}

// ─── Stats ─────────────────────────────────────────
export interface StatsOverview {
  employees: number;
  projects: number;
  technologies: number;
  departments: number;
  customers: number;
  teams: number;
  documents: number;
}

// ─── Graph ─────────────────────────────────────────
export type NodeType = 'Employee' | 'Team' | 'Project' | 'Technology' | 'Department' | 'Customer' | 'Document' | 'Product';

export interface GraphNode {
  id: string;
  label: string;
  type: NodeType;
  properties: Record<string, unknown>;
  // react-force-graph runtime fields
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number;
  fy?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface NodeDetail {
  id: string;
  type: NodeType;
  properties: Record<string, unknown>;
  relationships: Array<{
    rel_type: string;
    direction: 'in' | 'out';
    neighbor_id: string;
    neighbor_label: NodeType;
    neighbor_name: string;
  }>;
}

// ─── Ask / GraphRAG ────────────────────────────────
export interface AskRequest {
  question: string;
  session_id?: string;
}

export interface Source {
  name: string;
  relevance: string;
}

export interface AskResponse {
  session_id: string;
  message_id: string;
  question: string;
  answer: string;
  findings: string[];
  graph_path_explanation: string;
  sources: Source[];
  follow_up_suggestions: string[];
  subgraph_node_ids: string[];
  subgraph?: GraphData;
}

// ─── Chat ──────────────────────────────────────────
export interface ChatSession {
  session_id: string;
  title: string;
  question: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  structured_answer?: AskResponse;
  created_at: string;
}

export interface ChatThread {
  session_id: string;
  title: string;
  messages: ChatMessage[];
}

// ─── Documents ─────────────────────────────────────
export interface DocumentMeta {
  id: string;
  filename: string;
  file_size: number;
  status: 'pending' | 'processing' | 'done' | 'error';
  created_at: string;
  processed_at?: string;
}

export interface DocumentDetail extends DocumentMeta {
  content: string;
  entities: ExtractedEntity[];
}

export interface ExtractedEntity {
  type: NodeType;
  name: string;
  canonical_name?: string;
  matched?: boolean;
  properties?: Record<string, unknown>;
}

// ─── Insights ──────────────────────────────────────
export interface TechProjectCount {
  technology: string;
  project_count: number;
}

export interface DeptProjectCount {
  department: string;
  project_count: number;
}

export interface RelationshipCount {
  relationship_type: string;
  count: number;
}

export interface ActivityLog {
  id: string;
  event_type: string;
  description: string;
  entity_type?: string;
  entity_name?: string;
  created_at: string;
}

// ─── Entity Detail ─────────────────────────────────
export interface EntityDetail {
  id: string;
  type: NodeType;
  properties: Record<string, unknown>;
  relationships: Array<{
    rel_type: string;
    direction: 'in' | 'out';
    related_id: string;
    related_type: NodeType;
    related_name: string;
  }>;
}

// ─── Data Sources ──────────────────────────────────
export interface DataSource {
  id: string;
  name: string;
  source_type: string;
  status: 'connected' | 'not_connected' | 'error';
  last_sync?: string;
}
