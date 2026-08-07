const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown) {
    super(typeof body === "object" && body && "detail" in body ? String((body as { detail: unknown }).detail) : `HTTP ${status}`);
    this.status = status;
    this.body = body;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: {
        ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...init?.headers,
      },
    });
  } catch {
    throw new ApiError(0, {
      detail: "Cannot reach the API. Check that the backend is running and VITE_API_BASE_URL is set correctly.",
    });
  }

  const text = await response.text();
  let data: unknown = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { detail: text.slice(0, 200) };
    }
  }
  if (!response.ok) {
    throw new ApiError(response.status, data);
  }
  return data as T;
}

export const api = {
  listProjects: () =>
    request<{ results?: import("../types/api").ProjectSummary[] } | import("../types/api").ProjectSummary[]>(
      "/projects/",
    ).then((data) => (Array.isArray(data) ? data : data.results ?? [])),

  createProject: (payload: { name: string; description?: string }) =>
    request<import("../types/api").Project>("/projects/", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getProject: (id: string) => request<import("../types/api").Project>(`/projects/${id}/`),

  ingestZip: async (projectId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<{ job: import("../types/api").AnalysisJob }>(
      `/projects/${projectId}/ingest/zip/`,
      { method: "POST", body: form, headers: {} },
    );
  },

  ingestGitHub: (projectId: string, payload: { url: string; branch?: string }) =>
    request<{ job: import("../types/api").AnalysisJob }>(
      `/projects/${projectId}/ingest/github/`,
      { method: "POST", body: JSON.stringify(payload) },
    ),

  getJob: (projectId: string, jobId: string) =>
    request<import("../types/api").AnalysisJob>(`/projects/${projectId}/jobs/${jobId}/`),

  getFileTree: (projectId: string) =>
    request<{ tree: import("../types/api").FileTreeNode[] }>(`/projects/${projectId}/files/tree/`),

  getGraph: (projectId: string, graphType: string) =>
    request<import("../types/api").GraphResponse>(
      `/projects/${projectId}/graphs/${graphType}/?limit=800`,
    ),

  rebuildGraphs: (projectId: string) =>
    request<{
      project_id: string;
      node_total: number;
      edge_total: number;
      graphs: Record<string, number>;
    }>(`/projects/${projectId}/graphs/rebuild/`, { method: "POST", body: "{}" }),

  reanalyze: (projectId: string) =>
    request<import("../types/api").AnalysisJob>(`/projects/${projectId}/reanalyze/`, {
      method: "POST",
      body: "{}",
    }),

  health: () => request<{ status: string }>("/health/"),
};
