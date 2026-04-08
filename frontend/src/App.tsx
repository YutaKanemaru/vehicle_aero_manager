import { useEffect } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { LoadingOverlay } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import { LoginPage } from "./components/auth/LoginPage";
import { AppLayout } from "./components/layout/AppShell";
import { TemplateList } from "./components/templates/TemplateList";
import { GeometryList } from "./components/geometries/GeometryList";
import { AssemblyList } from "./components/assemblies/AssemblyList";
import { useAuthStore } from "./stores/auth";
import { authApi } from "./api/auth";

function ConfigurationsPlaceholder() {
  return <div>Configurations - Coming in Step 5</div>;
}

function AuthenticatedApp() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Navigate to="/templates" replace />} />
        <Route path="/templates" element={<TemplateList />} />
        <Route path="/geometries" element={<GeometryList />} />
        <Route path="/assemblies" element={<AssemblyList />} />
        <Route path="/configurations" element={<ConfigurationsPlaceholder />} />
      </Route>
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
}

export default function App() {
  const { token, user, setAuth, logout } = useAuthStore();

  const { isLoading, isError } = useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const u = await authApi.me();
      setAuth(token!, u);
      return u;
    },
    enabled: !!token && !user,
    retry: false,
  });

  useEffect(() => {
    if (isError) logout();
  }, [isError, logout]);

  if (isLoading) {
    return <LoadingOverlay visible />;
  }

  if (!token || !user) {
    return (
      <Routes>
        <Route path="*" element={<LoginPage />} />
      </Routes>
    );
  }

  return <AuthenticatedApp />;
}
