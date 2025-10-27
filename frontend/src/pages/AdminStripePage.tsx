import { FormEvent, useEffect, useMemo, useState } from "react";

import { API_BASE_URL } from "../config";
import { useAuth } from "../contexts/AuthContext";

type StripeConfig = {
  public_key: string | null;
  secret_key: string | null;
  webhook_secret: string | null;
};

const AdminStripePage = () => {
  const { accessToken } = useAuth();
  const [config, setConfig] = useState<StripeConfig>({
    public_key: "",
    secret_key: "",
    webhook_secret: "",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const headers = useMemo(() => {
    if (!accessToken) {
      return {};
    }
    return {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    };
  }, [accessToken]);

  useEffect(() => {
    const loadConfig = async () => {
      if (!accessToken) {
        return;
      }
      setLoading(true);
      setMessage(null);
      try {
        const response = await fetch(`${API_BASE_URL}/admin/stripe/config`, {
          headers,
        });
        if (!response.ok) {
          throw new Error("Falha ao carregar credenciais");
        }
        const payload = (await response.json()) as StripeConfig;
        setConfig({
          public_key: payload.public_key ?? "",
          secret_key: payload.secret_key ?? "",
          webhook_secret: payload.webhook_secret ?? "",
        });
      } catch (err) {
        console.error(err);
        setMessage("Não foi possível carregar as credenciais atuais.");
      } finally {
        setLoading(false);
      }
    };

    loadConfig();
  }, [accessToken, headers]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!accessToken) {
      return;
    }
    setSaving(true);
    setMessage(null);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/stripe/config`, {
        method: "PUT",
        headers,
        body: JSON.stringify(config),
      });
      if (!response.ok) {
        throw new Error("Falha ao salvar credenciais");
      }
      const payload = (await response.json()) as StripeConfig;
      setConfig({
        public_key: payload.public_key ?? "",
        secret_key: payload.secret_key ?? "",
        webhook_secret: payload.webhook_secret ?? "",
      });
      setMessage("Credenciais atualizadas com sucesso.");
    } catch (err) {
      console.error(err);
      setMessage("Ocorreu um erro ao salvar as credenciais.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="text-sm text-slate-500">Carregando configurações...</div>;
  }

  return (
    <div className="max-w-3xl space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-slate-900">Credenciais Stripe</h1>
        <p className="mt-1 text-sm text-slate-600">
          Atualize as chaves utilizadas para integrações de billing e webhooks com a Stripe.
        </p>
      </header>

      <form className="space-y-4 rounded-lg bg-white p-6 shadow" onSubmit={handleSubmit}>
        <div>
          <label className="text-sm font-medium text-slate-700" htmlFor="public_key">
            Public Key
          </label>
          <input
            className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
            id="public_key"
            onChange={(event) => setConfig((prev) => ({ ...prev, public_key: event.target.value }))}
            value={config.public_key ?? ""}
          />
        </div>
        <div>
          <label className="text-sm font-medium text-slate-700" htmlFor="secret_key">
            Secret Key
          </label>
          <input
            className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
            id="secret_key"
            onChange={(event) => setConfig((prev) => ({ ...prev, secret_key: event.target.value }))}
            type="password"
            value={config.secret_key ?? ""}
          />
        </div>
        <div>
          <label className="text-sm font-medium text-slate-700" htmlFor="webhook_secret">
            Webhook Secret
          </label>
          <input
            className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
            id="webhook_secret"
            onChange={(event) =>
              setConfig((prev) => ({ ...prev, webhook_secret: event.target.value }))
            }
            type="password"
            value={config.webhook_secret ?? ""}
          />
        </div>
        <p className="text-xs text-slate-500">
          As credenciais são armazenadas de forma segura para todas as organizações vinculadas à plataforma.
        </p>
        <button
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white disabled:opacity-75"
          disabled={saving}
          type="submit"
        >
          {saving ? "Salvando..." : "Salvar alterações"}
        </button>
      </form>

      {message ? (
        <p className="text-sm text-slate-600">{message}</p>
      ) : null}
    </div>
  );
};

export default AdminStripePage;
