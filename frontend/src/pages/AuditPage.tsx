import { Card, CardContent, CardHeader, CardTitle } from "../components/Card";

const mockAudits = [
  {
    id: 1,
    periodo: "01/03/2024 - 31/03/2024",
    status: "Concluída",
    findings: 12
  },
  {
    id: 2,
    periodo: "01/04/2024 - 15/04/2024",
    status: "Em processamento",
    findings: 0
  }
];

const AuditPage = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Auditorias</h1>
        <button className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-white shadow">
          Nova auditoria
        </button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Execuções recentes</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-4">
            {mockAudits.map((audit) => (
              <li key={audit.id} className="flex items-center justify-between">
                <div>
                  <p className="font-medium">{audit.periodo}</p>
                  <span className="text-xs text-slate-500">
                    {audit.findings} achados
                  </span>
                </div>
                <span className="rounded-full bg-slate-200 px-3 py-1 text-xs font-semibold">
                  {audit.status}
                </span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
};

export default AuditPage;
