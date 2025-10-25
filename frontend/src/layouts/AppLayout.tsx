import { Link, Outlet } from "react-router-dom";

const navItems = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/invoices", label: "Notas" },
  { to: "/audits", label: "Auditorias" },
  { to: "/billing", label: "Planos" }
];

const AppLayout = () => {
  return (
    <div className="min-h-screen bg-slate-100">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <span className="text-xl font-semibold text-primary">Oráculo ICMS</span>
          <nav className="flex gap-4 text-sm font-medium">
            {navItems.map((item) => (
              <Link key={item.to} className="hover:text-primary" to={item.to}>
                {item.label}
              </Link>
            ))}
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
