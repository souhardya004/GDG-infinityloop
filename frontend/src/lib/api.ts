function resolveApiBase(): string {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (!envUrl || typeof envUrl !== "string") {
    return "/api/v1";
  }
  const trimmed = envUrl.trim().replace(/\/+$/, "");
  if (!trimmed) {
    return "/api/v1";
  }
  if (trimmed.endsWith("/api/v1")) {
    return trimmed;
  }
  if (trimmed.endsWith("/api")) {
    return `${trimmed}/v1`;
  }
  return `${trimmed}/api/v1`;
}

const API_BASE = resolveApiBase();

const TOKEN_STORAGE_KEY = "codescope_token";

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setStoredToken(token: string | null) {
  if (token) {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  }
}

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
  const token = getStoredToken();
  const authHeaders: Record<string, string> = {};
  if (token) {
    authHeaders["Authorization"] = `Token ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: {
        ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...authHeaders,
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
      if (text.trim().startsWith("<")) {
        data = {
          detail: `API endpoint returned HTTP ${response.status} (${response.statusText || "Not Found"}). Check that VITE_API_BASE_URL is configured correctly.`,
        };
      } else {
        data = { detail: text.slice(0, 200) };
      }
    }
  }
  if (!response.ok) {
    throw new ApiError(response.status, data);
  }
  return data as T;
}

export const api = {
  // Auth endpoints
  auth: {
    me: () => request<{ user: import("../types/api").User }>("/auth/me/"),
    login: (payload: { username_or_email: string; password: string }) =>
      request<import("../types/api").AuthResponse>("/auth/login/", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    signup: (payload: { email: string; password: string; username?: string; full_name?: string }) =>
      request<import("../types/api").AuthResponse>("/auth/signup/", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    github: (payload: { code: string; redirect_uri?: string }) =>
      request<import("../types/api").AuthResponse>("/auth/github/", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    google: (payload: { code?: string; id_token?: string; redirect_uri?: string }) =>
      request<import("../types/api").AuthResponse>("/auth/google/", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    demo: () =>
      request<import("../types/api").AuthResponse>("/auth/demo/", {
        method: "POST",
        body: "{}",
      }),
    logout: () =>
      request<{ detail: string }>("/auth/logout/", {
        method: "POST",
        body: "{}",
      }),
    providers: () =>
      request<import("../types/api").ProvidersConfig>("/auth/providers/"),
  },

  // Project endpoints
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

