import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";

export const RequireAuth: React.FC = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="py-12 text-center text-slate-500">Carregando...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
};

export const RequireAdmin: React.FC = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="py-12 text-center text-slate-500">Carregando...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!user.is_superuser) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
};
