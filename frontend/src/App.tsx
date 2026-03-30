import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { useAuth } from "@/hooks/useAuth";
import { Layout } from "@/components/Layout";
import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { NewOutreachPage } from "@/pages/NewOutreachPage";
import { TrackerPage } from "@/pages/TrackerPage";
import { ApplicationDetailPage } from "@/pages/ApplicationDetailPage";
import { TemplatesPage } from "@/pages/TemplatesPage";
import { ProfilePage } from "@/pages/ProfilePage";
import { FitAnalyzerPage } from "@/pages/FitAnalyzerPage";

export default function App() {
  const { user, loading, login, register, logout } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (!user) {
    return (
      <>
        <LoginPage onLogin={login} onRegister={register} />
        <Toaster />
      </>
    );
  }

  return (
    <BrowserRouter>
      <Layout onLogout={logout} username={user.username}>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/outreach/new" element={<NewOutreachPage />} />
          <Route path="/tracker" element={<TrackerPage />} />
          <Route path="/applications/:id" element={<ApplicationDetailPage />} />
          <Route path="/templates" element={<TemplatesPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/fit" element={<FitAnalyzerPage />} />
          <Route path="/login" element={<Navigate to="/" />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Layout>
      <Toaster />
    </BrowserRouter>
  );
}
