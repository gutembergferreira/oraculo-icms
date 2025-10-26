import { useEffect, useMemo, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "../components/Card";
import { api } from "../lib/api";

type Plan = {
  code: string;
  name: string;
  monthly_price_cents: number;
  features: Record<string, boolean>;
  limits: Record<string, number>;
};

const FEATURE_LABELS: Record<string, string> = {
  exports_pdf: "Exportação de relatórios em PDF",
  exports_xlsx: "Exportação de relatórios em XLSX",
  rules_dsl_custom: "Editor de regras personalizadas (DSL)",
  priority_support: "Suporte prioritário",
  dedicated_success: "Customer success dedicado",
};

const LIMIT_LABELS: Record<string, string> = {
  max_xml_uploads_month: "XML por mês",
  max_storage_mb: "Armazenamento (MB)",
  max_users: "Usuários inclusos",
};

const orgId = 1;

const centsToCurrency = (value: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(
    value / 100
  );

const BillingPage = () => {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loadingPlan, setLoadingPlan] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [portalLoading, setPortalLoading] = useState(false);

  useEffect(() => {
    api
      .get<Plan[]>("/public/plans")
      .then((response) => setPlans(response.data))
      .catch(() => setError("Não foi possível carregar os planos disponíveis."));
  }, []);

  const handleSubscribe = async (planCode: string) => {
    setError(null);
    setLoadingPlan(planCode);
    try {
      const { data } = await api.post<CheckoutSessionResponse>(
        "/billing/create-checkout-session",
        {
          org_id: orgId,
          plan_code: planCode,
        }
      );
      window.location.href = data.checkout_url;
    } catch (subscriptionError) {
      setError(
        "Não foi possível iniciar o checkout. Verifique se as credenciais Stripe estão configuradas."
      );
    } finally {
      setLoadingPlan(null);
    }
  };

  const handlePortal = async () => {
    setError(null);
    setPortalLoading(true);
    try {
      const { data } = await api.post<PortalSessionResponse>("/billing/portal", {
        org_id: orgId,
      });
      window.location.href = data.portal_url;
    } catch (portalError) {
      setError("Não foi possível abrir o portal de cobrança.");
    } finally {
      setPortalLoading(false);
    }
  };

  const formattedPlans = useMemo(() => plans, [plans]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold">Planos e assinatura</h1>
        <button
          onClick={handlePortal}
          disabled={portalLoading}
          className="rounded-md border border-primary px-3 py-2 text-sm font-medium text-primary disabled:opacity-50"
        >
          {portalLoading ? "Abrindo portal..." : "Gerenciar assinatura"}
        </button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {formattedPlans.map((plan) => {
          const isFree = plan.monthly_price_cents === 0;
          const priceLabel = isFree
            ? "Gratuito"
            : centsToCurrency(plan.monthly_price_cents);
          const featureEntries = Object.entries(plan.features ?? {});
          const limitEntries = Object.entries(plan.limits ?? {});

          return (
            <Card key={plan.code}>
              <CardHeader>
                <CardTitle className="flex items-baseline justify-between">
                  <span>{plan.name}</span>
                  <span className="text-sm font-normal uppercase text-slate-500">
                    {plan.code}
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-3xl font-bold">{priceLabel}</p>
                <div className="space-y-3 text-sm text-slate-600">
                  <div>
                    <p className="font-medium text-slate-700">Recursos</p>
                    <ul className="mt-1 space-y-1">
                      {featureEntries.length === 0 && <li>Sem recursos extras</li>}
                      {featureEntries.map(([key, value]) => (
                        <li key={key} className="flex items-center gap-2">
                          <span>{value ? "✅" : "⚪"}</span>
                          <span>{FEATURE_LABELS[key] ?? key}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <p className="font-medium text-slate-700">Limites</p>
                    <ul className="mt-1 space-y-1">
                      {limitEntries.map(([key, value]) => (
                        <li key={key}>
                          {LIMIT_LABELS[key] ?? key}: <strong>{value}</strong>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
                {!isFree && (
                  <button
                    className="w-full rounded-md bg-primary px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
                    onClick={() => handleSubscribe(plan.code)}
                    disabled={loadingPlan === plan.code}
                  >
                    {loadingPlan === plan.code ? "Redirecionando..." : "Assinar"}
                  </button>
                )}
                {isFree && (
                  <div className="rounded-md border border-slate-200 px-3 py-2 text-center text-xs text-slate-500">
                    Plano aplicado automaticamente para novas organizações.
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
};

type CheckoutSessionResponse = {
  checkout_url: string;
};

type PortalSessionResponse = {
  portal_url: string;
};

export default BillingPage;
