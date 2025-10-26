import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { API_BASE_URL } from "../config";
import { useAuth } from "../contexts/AuthContext";

type Provider = {
  type: string;
  name: string;
};

const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [searchParams, setSearchParams] = useSearchParams();
  const [processingSSO, setProcessingSSO] = useState(false);
  const { login, authenticate } = useAuth();
  const navigate = useNavigate();

  const loginWithTokens = useCallback(
    async (accessToken: string, refreshToken: string) => {
      await authenticate(accessToken, refreshToken);
      navigate("/dashboard", { replace: true });
    },
    [authenticate, navigate]
  );

  useEffect(() => {
    fetch(`${API_BASE_URL}/auth/providers`)
      .then((response) => response.json())
      .then((data) => setProviders(data.providers ?? []))
      .catch(() => setProviders([{ type: "password", name: "E-mail e senha" }]));
  }, []);

  useEffect(() => {
    const code = searchParams.get("code");
    if (!code || processingSSO) {
      return;
    }
    setProcessingSSO(true);
    fetch(`${API_BASE_URL}/auth/sso/callback`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ code, state: searchParams.get("state") }),
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error("Falha na autenticação SSO");
        }
        const tokens = await response.json();
        // reaproveita fluxo de login padrão
        await loginWithTokens(tokens.access_token, tokens.refresh_token);
        setSearchParams({}, { replace: true });
      })
      .catch(() => {
        setError("Não foi possível concluir o login via SSO.");
      })
      .finally(() => setProcessingSSO(false));
  }, [processingSSO, searchParams, setSearchParams, loginWithTokens]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    try {
      await login(email, password);
      navigate("/dashboard", { replace: true });
    } catch (authError) {
      setError((authError as Error).message ?? "Falha no login");
    }
  };

  const handleSSO = async () => {
    setError(null);
    try {
      const state =
        typeof window !== "undefined" && window.crypto?.randomUUID
          ? window.crypto.randomUUID()
          : Math.random().toString(36).slice(2);
      const response = await fetch(
        `${API_BASE_URL}/auth/sso/authorize?state=${encodeURIComponent(state)}`
      );
      if (!response.ok) {
        throw new Error("SSO indisponível");
      }
      const payload = await response.json();
      window.location.href = payload.url;
    } catch (error) {
      setError((error as Error).message ?? "Não foi possível iniciar o SSO");
    }
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
        {providers.some((provider) => provider.type === "sso") ? (
          <button
            className="mt-4 w-full rounded-md border px-3 py-2 text-sm font-medium"
            onClick={handleSSO}
            type="button"
            disabled={processingSSO}
          >
            Entrar com {providers.find((provider) => provider.type === "sso")?.name ?? "SSO"}
          </button>
        ) : null}
        {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
        <p className="mt-4 text-center text-sm text-slate-600">
          Não tem uma conta? <Link className="text-primary" to="/signup">Criar agora</Link>
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
