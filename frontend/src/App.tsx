import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  Outlet,
} from "react-router-dom";
import { LoginView, CallbackView, DashboardView } from "./views";
import { AuthProvider, useAuth } from "./context/AuthContext";

const ProtectedRoute = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <p>Cargando sesión...</p>;
  }

  return isAuthenticated ? <Outlet /> : <Navigate to="/" replace />;
};

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LoginView />} />
      <Route path="/callback" element={<CallbackView />} />

      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<DashboardView />} />
      </Route>
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <AppRoutes />
      </Router>
    </AuthProvider>
  );
}

export default App;
