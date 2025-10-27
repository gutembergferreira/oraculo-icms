import { Link, Outlet } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";

const AppLayout = () => {
  const { user, logout } = useAuth();
  const links = [
    { to: "/dashboard", label: "Dashboard" },
    { to: "/invoices", label: "Notas" },
    { to: "/audits", label: "Auditorias" },
    { to: "/billing", label: "Planos" },
    { to: "/rules", label: "Regras" }
  ];

  if (user?.is_superuser) {
    links.push({ to: "/admin", label: "Administração" });
  }

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <span className="text-xl font-semibold text-primary">Oráculo ICMS</span>
          <nav className="flex items-center gap-4 text-sm font-medium">
            {links.map((item) => (
              <Link key={item.to} className="hover:text-primary" to={item.to}>
                {item.label}
              </Link>
            ))}
            <button
              className="rounded-md border px-3 py-1 text-xs"
              onClick={logout}
              type="button"
            >
              Sair
            </button>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
};

export default AppLayout;
