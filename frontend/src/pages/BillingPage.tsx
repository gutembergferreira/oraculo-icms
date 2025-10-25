import { Card, CardContent, CardHeader, CardTitle } from "../components/Card";

const plans = [
  {
    code: "FREE",
    title: "Free",
    price: "R$ 0",
    features: ["200 XML/mês", "Até 3 usuários"],
    cta: "Selecionar"
  },
  {
    code: "PRO",
    title: "Pro",
    price: "R$ 499/mês",
    features: ["2.000 XML/mês", "Exportações PDF/XLSX", "Regras ZFM"],
    cta: "Assinar"
  }
];

const BillingPage = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Planos e assinatura</h1>
      <div className="grid gap-6 md:grid-cols-2">
        {plans.map((plan) => (
          <Card key={plan.code}>
            <CardHeader>
              <CardTitle>{plan.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{plan.price}</p>
              <ul className="mt-4 space-y-2 text-sm text-slate-600">
                {plan.features.map((feature) => (
                  <li key={feature}>• {feature}</li>
                ))}
              </ul>
              <button className="mt-6 w-full rounded-md bg-primary px-3 py-2 text-sm font-medium text-white">
                {plan.cta}
              </button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default BillingPage;
