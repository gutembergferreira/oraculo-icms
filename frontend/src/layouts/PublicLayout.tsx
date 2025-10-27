import { Link, Outlet } from "react-router-dom";

const PublicLayout = () => {
  return (
    <div className="min-h-screen bg-white">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <span className="text-xl font-semibold text-primary">Oráculo ICMS</span>
          <Link className="rounded-md border px-4 py-2 text-sm" to="/login">
            Entrar
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-4xl px-4 py-10">
        <Outlet />
      </main>
    </div>
  );
};

export default PublicLayout;
