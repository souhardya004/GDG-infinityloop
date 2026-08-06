import { Navigate, Route, Routes, useParams } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { HomePage } from "./pages/HomePage";
import { NewProjectPage } from "./pages/NewProjectPage";
import { ProjectDashboardPage } from "./pages/ProjectDashboardPage";
import { ProjectsPage } from "./pages/ProjectsPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<HomePage />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="projects/new" element={<NewProjectPage />} />
        <Route path="projects/:projectId" element={<ProjectDashboardPage />} />
        {/* Legacy nested graph URLs → single full-canvas workspace */}
        <Route path="projects/:projectId/graph/:graphType" element={<GraphRedirect />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

function GraphRedirect() {
  const { projectId = "", graphType = "architecture" } = useParams();
  const view = graphType === "file_dependency" ? "dependency" : graphType;
  return <Navigate to={`/projects/${projectId}?view=${view}`} replace />;
}
