import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  Outlet,
} from "react-router-dom";

import {
  LoginView,
  CallbackView,
  DashboardView,
  RecommendationsView,
} from "./views";

import { AuthProvider, useAuth } from "./context/AuthContext";
import { UserProvider } from "./context/UserContext";
import { MusicProvider } from "./context/MusicContext";

const ProtectedRoute = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="h-screen w-full bg-zinc-950 flex items-center justify-center text-white">
        <p className="animate-pulse">Cargando sesión...</p>
      </div>
    );
  }

  return isAuthenticated ? <Outlet /> : <Navigate to="/" replace />;
};

function AppRoutes() {
  return (
    <Routes>
      {/* Rutas Públicas */}
      <Route path="/" element={<LoginView />} />
      <Route path="/callback" element={<CallbackView />} />

      {/* Rutas Protegidas */}
      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<DashboardView />} />
        <Route path="/recommendations" element={<RecommendationsView />} />
      </Route>

      {/* Fallback por si escriben cualquier cosa */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <UserProvider>
        <MusicProvider>
          <Router>
            <AppRoutes />
          </Router>
        </MusicProvider>
      </UserProvider>
    </AuthProvider>
  );
}

export default App;
