import { useCallback, useEffect, useMemo, useState } from "react";

import { API_BASE_URL } from "../config";
import { useAuth } from "../contexts/AuthContext";

type Plan = {
  id: number;
  code: string;
  name: string;
  monthly_price_cents: number;
  features: Record<string, unknown>;
  limits: Record<string, unknown>;
  stripe_product_id: string | null;
  stripe_price_id: string | null;
};

const AdminPlansPage = () => {
  const { accessToken } = useAuth();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);

  const headers = useMemo(() => {
    if (!accessToken) {
      return {};
    }
    return {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    };
  }, [accessToken]);

  const fetchPlans = useCallback(async () => {
    if (!accessToken) {
      return;
    }
    setLoading(true);
    setMessage(null);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/plans`, { headers });
      if (!response.ok) {
        throw new Error("Falha ao carregar planos");
      }
      const payload = (await response.json()) as Plan[];
      setPlans(payload);
    } catch (err) {
      console.error(err);
      setMessage("Não foi possível carregar os planos disponíveis.");
    } finally {
      setLoading(false);
    }
  }, [accessToken, headers]);

  useEffect(() => {
    fetchPlans();
  }, [fetchPlans]);

  const syncPlans = useCallback(async () => {
    if (!accessToken) {
      return;
    }
    setSyncing(true);
    setMessage(null);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/plans/sync`, {
        method: "POST",
        headers,
      });
      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        const error = detail?.detail ?? "Falha ao sincronizar";
        throw new Error(typeof error === "string" ? error : "Erro inesperado");
      }
      await fetchPlans();
      setMessage("Catálogo sincronizado com sucesso.");
    } catch (err) {
      console.error(err);
      setMessage(
        err instanceof Error ? err.message : "Não foi possível sincronizar o catálogo."
      );
    } finally {
      setSyncing(false);
    }
  }, [accessToken, fetchPlans, headers]);

  if (loading) {
    return <div className="text-sm text-slate-500">Carregando planos...</div>;
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Administração de Planos</h1>
          <p className="mt-1 text-sm text-slate-600">
            Visualize os planos cadastrados e garanta que estejam sincronizados com o Stripe.
          </p>
        </div>
        <button
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white disabled:opacity-75"
          disabled={syncing}
          onClick={syncPlans}
          type="button"
        >
          {syncing ? "Sincronizando..." : "Sincronizar com Stripe"}
        </button>
      </header>

      {message ? (
        <p className="rounded border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700">
          {message}
        </p>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2">
        {plans.map((plan) => (
          <article key={plan.id} className="rounded-lg border bg-white p-5 shadow-sm">
            <header className="mb-3 flex items-baseline justify-between gap-2">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">{plan.name}</h2>
                <p className="text-xs uppercase tracking-wide text-slate-500">{plan.code}</p>
              </div>
              <span className="text-sm font-medium text-primary">
                R$ {(plan.monthly_price_cents / 100).toFixed(2)} / mês
              </span>
            </header>
            <section className="text-sm text-slate-600">
              <h3 className="font-semibold text-slate-800">Recursos</h3>
              <ul className="mt-2 space-y-1 text-xs">
                {Object.entries(plan.features ?? {}).map(([feature, value]) => (
                  <li key={feature}>
                    <span className="font-medium text-slate-700">{feature}</span>: {String(value)}
                  </li>
                ))}
                {Object.keys(plan.features ?? {}).length === 0 ? <li>Nenhum recurso configurado.</li> : null}
              </ul>
            </section>
            <section className="mt-4 text-sm text-slate-600">
              <h3 className="font-semibold text-slate-800">Limites</h3>
              <ul className="mt-2 space-y-1 text-xs">
                {Object.entries(plan.limits ?? {}).map(([limit, value]) => (
                  <li key={limit}>
                    <span className="font-medium text-slate-700">{limit}</span>: {String(value)}
                  </li>
                ))}
                {Object.keys(plan.limits ?? {}).length === 0 ? <li>Nenhum limite configurado.</li> : null}
              </ul>
            </section>
            <section className="mt-4 text-xs text-slate-500">
              <p>Stripe Product ID: {plan.stripe_product_id ?? "—"}</p>
              <p>Stripe Price ID: {plan.stripe_price_id ?? "—"}</p>
            </section>
          </article>
        ))}
      </div>
    </div>
  );
};

export default AdminPlansPage;
