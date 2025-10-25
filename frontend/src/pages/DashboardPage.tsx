import { Card, CardContent, CardHeader, CardTitle } from "../components/Card";
import { useDashboardMetrics } from "../hooks/useDashboard";

const DashboardPage = () => {
  const { data } = useDashboardMetrics();

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Visão Geral</h1>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {data.cards.map((card) => (
          <Card key={card.title}>
            <CardHeader>
              <CardTitle>{card.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{card.value}</p>
              <span className="text-xs text-slate-500">{card.description}</span>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default DashboardPage;
