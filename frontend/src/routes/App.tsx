import { Navigate, Route, Routes } from "react-router-dom";

import DashboardPage from "../pages/DashboardPage";
import InvoicesPage from "../pages/InvoicesPage";
import AuditPage from "../pages/AuditPage";
import BillingPage from "../pages/BillingPage";
import RulesPage from "../pages/RulesPage";
import LoginPage from "../pages/LoginPage";
import Layout from "../layouts/AppLayout";

const App = () => {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/invoices" element={<InvoicesPage />} />
        <Route path="/audits" element={<AuditPage />} />
        <Route path="/billing" element={<BillingPage />} />
        <Route path="/rules" element={<RulesPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

export default App;
