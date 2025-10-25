import { useState } from "react";
import { Link } from "react-router-dom";

const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    // Integração real chamará API /auth/login
    alert(`Login enviado para ${email}`);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100">
      <div className="w-full max-w-md rounded-lg border bg-white p-8 shadow">
        <h1 className="text-2xl font-semibold">Bem-vindo ao Oráculo ICMS</h1>
        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <label className="text-sm font-medium" htmlFor="email">
              E-mail
            </label>
            <input
              id="email"
              className="w-full rounded-md border px-3 py-2 text-sm"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              type="email"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium" htmlFor="password">
              Senha
            </label>
            <input
              id="password"
              className="w-full rounded-md border px-3 py-2 text-sm"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type="password"
            />
          </div>
          <button className="w-full rounded-md bg-primary px-3 py-2 text-sm font-medium text-white">
            Entrar
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-slate-600">
          Não tem uma conta? <Link className="text-primary" to="/signup">Criar agora</Link>
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
