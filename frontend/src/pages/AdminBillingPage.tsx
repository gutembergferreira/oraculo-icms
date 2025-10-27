import { FormEvent, useEffect, useMemo, useState } from "react";

import { API_BASE_URL } from "../config";
import { useAuth } from "../contexts/AuthContext";

type Organization = {
  id: number;
  name: string;
  slug: string;
};

type PortalResponse = {
  portal_url: string;
};

const AdminBillingPage = () => {
  const { accessToken } = useAuth();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrg, setSelectedOrg] = useState<number | "">("");
  const [portalLink, setPortalLink] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
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
    const fetchOrganizations = async () => {
      if (!accessToken) {
        return;
      }
      setLoading(true);
      setMessage(null);
      try {
        const response = await fetch(`${API_BASE_URL}/admin/organizations`, {
          headers,
        });
        if (!response.ok) {
          throw new Error("Falha ao carregar organizações");
        }
        const payload = (await response.json()) as Organization[];
        setOrganizations(payload);
      } catch (err) {
        console.error(err);
        setMessage("Não foi possível carregar as organizações disponíveis.");
      } finally {
        setLoading(false);
      }
    };

    fetchOrganizations();
  }, [accessToken, headers]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!accessToken || selectedOrg === "") {
      setMessage("Selecione uma organização para gerar o portal.");
      return;
    }
    setSubmitting(true);
    setMessage(null);
    setPortalLink(null);
    try {
      const response = await fetch(`${API_BASE_URL}/billing/portal`, {
        method: "POST",
        headers,
        body: JSON.stringify({ org_id: Number(selectedOrg) }),
      });
      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        const error = detail?.detail ?? "Falha ao gerar portal";
        throw new Error(typeof error === "string" ? error : "Erro inesperado");
      }
      const payload = (await response.json()) as PortalResponse;
      setPortalLink(payload.portal_url);
      setMessage("Portal de cobranças gerado com sucesso.");
    } catch (err) {
      console.error(err);
      setMessage(err instanceof Error ? err.message : "Não foi possível gerar o portal.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-slate-900">Portal de Cobranças</h1>
        <p className="mt-1 text-sm text-slate-600">
          Gere um link de acesso ao portal de faturamento da Stripe para qualquer organização ativa.
        </p>
      </header>

      {loading ? (
        <p className="text-sm text-slate-500">Carregando organizações...</p>
      ) : (
        <form className="space-y-4 rounded-lg bg-white p-6 shadow" onSubmit={handleSubmit}>
          <div>
            <label className="text-sm font-medium text-slate-700" htmlFor="organization">
              Organização
            </label>
            <select
              className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
              id="organization"
              onChange={(event) => setSelectedOrg(event.target.value ? Number(event.target.value) : "")}
              value={selectedOrg}
            >
              <option value="">Selecione...</option>
              {organizations.map((org) => (
                <option key={org.id} value={org.id}>
                  {org.name} ({org.slug})
                </option>
              ))}
            </select>
          </div>
          <button
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white disabled:opacity-75"
            disabled={submitting || selectedOrg === ""}
            type="submit"
          >
            {submitting ? "Gerando portal..." : "Gerar link do portal"}
          </button>
        </form>
      )}

      {message ? (
        <p className="text-sm text-slate-600">{message}</p>
      ) : null}

      {portalLink ? (
        <div className="rounded border border-primary bg-primary/5 p-4 text-sm text-primary">
          <p>Link gerado:</p>
          <a className="break-all underline" href={portalLink} rel="noreferrer" target="_blank">
            {portalLink}
          </a>
        </div>
      ) : null}
    </div>
  );
};

export default AdminBillingPage;
