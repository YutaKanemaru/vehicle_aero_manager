import { useEffect } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { LoadingOverlay } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import { LoginPage } from "./components/auth/LoginPage";
import { AppLayout } from "./components/layout/AppShell";
import { useAuthStore } from "./stores/auth";
import { authApi } from "./api/auth";

function DashboardPlaceholder() {
  return <div>Dashboard - Coming soon</div>;
}

function TemplatesPlaceholder() {
  return <div>Templates - Coming in Step 3</div>;
}

function ConfigurationsPlaceholder() {
  return <div>Configurations - Coming in Step 5</div>;
}

function AuthenticatedApp() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<DashboardPlaceholder />} />
        <Route path="/templates" element={<TemplatesPlaceholder />} />
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
