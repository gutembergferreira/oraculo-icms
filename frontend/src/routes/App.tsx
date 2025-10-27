import { Navigate, Route, Routes } from "react-router-dom";

import { RequireAdmin, RequireAuth } from "../components/RouteGuards";
import Layout from "../layouts/AppLayout";
import PublicLayout from "../layouts/PublicLayout";
import AdminBillingPage from "../pages/AdminBillingPage";
import AdminPage from "../pages/AdminPage";
import AdminPlansPage from "../pages/AdminPlansPage";
import AdminStripePage from "../pages/AdminStripePage";
import AdminUsersPage from "../pages/AdminUsersPage";
import AuditPage from "../pages/AuditPage";
import BillingPage from "../pages/BillingPage";
import DashboardPage from "../pages/DashboardPage";
import HomePage from "../pages/HomePage";
import InvoicesPage from "../pages/InvoicesPage";
import LoginPage from "../pages/LoginPage";
import RulesPage from "../pages/RulesPage";

const App = () => {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route index element={<HomePage />} />
      </Route>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<RequireAuth />}>
        <Route element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/invoices" element={<InvoicesPage />} />
          <Route path="/audits" element={<AuditPage />} />
          <Route path="/billing" element={<BillingPage />} />
          <Route path="/rules" element={<RulesPage />} />
          <Route element={<RequireAdmin />}>
            <Route path="/admin" element={<AdminPage />} />
            <Route path="/admin/users" element={<AdminUsersPage />} />
            <Route path="/admin/plans" element={<AdminPlansPage />} />
            <Route path="/admin/stripe" element={<AdminStripePage />} />
            <Route path="/admin/billing" element={<AdminBillingPage />} />
          </Route>
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;
