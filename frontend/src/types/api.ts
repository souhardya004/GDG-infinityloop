export type ProjectStatus =
  | "draft"
  | "ingesting"
  | "analyzing"
  | "ready"
  | "failed"
  | "archived";

export type ProjectSummary = {
  id: string;
  name: string;
  slug: string;
  status: ProjectStatus;
  visibility: string;
  file_count: number;
  loc_total: number;
  created_at: string;
  analyzed_at: string | null;
};

export type Project = {
  id: string;
  name: string;
  slug: string;
  description: string;
  status: ProjectStatus;
  visibility: string;
  stats: {
    loc_total: number;
    file_count: number;
    function_count: number;
    class_count: number;
    api_count: number;
    table_count: number;
    technical_debt_score: string | null;
    architecture_pattern: string | null;
  };
  languages: { language: string; file_count: number; loc: number }[];
  analyzed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type AnalysisJob = {
  id: string;
  project_id: string;
  job_type: string;
  status: string;
  stage: string;
  progress_pct: string | number;
  error_message: string;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
};

export type GraphNode = {
  uid: string;
  label: string;
  kind: string;
  properties: Record<string, unknown>;
};

export type GraphEdge = {
  id: string;
  source: string;
  target: string;
  type: string;
  properties: Record<string, unknown>;
};

export type GraphResponse = {
  project_id: string;
  graph_type: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  meta: {
    truncated: boolean;
    total_nodes: number;
    returned_nodes: number;
    total_edges: number;
    returned_edges: number;
  };
};

export type FileTreeNode = {
  name: string;
  path: string;
  type: "folder" | "file";
  language?: string;
  size_bytes?: number;
  line_count?: number;
  file_count?: number;
  children?: FileTreeNode[];
};
