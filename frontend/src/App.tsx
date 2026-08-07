import { Navigate, Route, Routes, useParams } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AuthProvider } from "./context/AuthContext";
import { HomePage } from "./pages/HomePage";
import { LoginPage } from "./pages/LoginPage";
import { NewProjectPage } from "./pages/NewProjectPage";
import { OAuthCallbackPage } from "./pages/OAuthCallbackPage";
import { ProjectDashboardPage } from "./pages/ProjectDashboardPage";
import { ProjectsPage } from "./pages/ProjectsPage";

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route element={<AppShell />}>
          {/* Public Routes */}
          <Route index element={<HomePage />} />
          <Route path="login" element={<LoginPage />} />
          <Route path="auth/callback/:provider" element={<OAuthCallbackPage />} />

          {/* Protected Routes — Exclusive to authenticated user */}
          <Route element={<ProtectedRoute />}>
            <Route path="projects" element={<ProjectsPage />} />
            <Route path="projects/new" element={<NewProjectPage />} />
            <Route path="projects/:projectId" element={<ProjectDashboardPage />} />
            {/* Legacy nested graph URLs → single full-canvas workspace */}
            <Route path="projects/:projectId/graph/:graphType" element={<GraphRedirect />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </AuthProvider>
  );
}

function GraphRedirect() {
  const { projectId = "", graphType = "architecture" } = useParams();
  const view = graphType === "file_dependency" ? "dependency" : graphType;
  return <Navigate to={`/projects/${projectId}?view=${view}`} replace />;
}

