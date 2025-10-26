import { useEffect, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "../components/Card";
import { api } from "../lib/api";

type AuditRun = {
  id: number;
  status: string;
  summary: Record<string, unknown>;
  findings: unknown[];
};

const orgId = 1;

const AuditPage = () => {
  const [audits, setAudits] = useState<AuditRun[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAudits = async () => {
    const response = await api.get<AuditRun[]>(`/orgs/${orgId}/audits`);
    setAudits(response.data);
  };

  useEffect(() => {
    fetchAudits().catch(() => setError("Não foi possível carregar as auditorias."));
  }, []);

  const handleRunAudit = async () => {
    setLoading(true);
    setError(null);
    try {
      const now = new Date();
      const start = new Date(now.getFullYear(), now.getMonth(), 1);
      await api.post(`/orgs/${orgId}/audits/run`, {
        date_start: start.toISOString(),
        date_end: now.toISOString(),
        ruleset_version: null,
      });
      await fetchAudits();
    } catch (auditError) {
      setError("Não foi possível iniciar uma nova auditoria.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Auditorias</h1>
        <button
          className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-white shadow disabled:opacity-60"
          onClick={handleRunAudit}
          disabled={loading}
        >
          Nova auditoria
        </button>
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <Card>
        <CardHeader>
          <CardTitle>Execuções recentes</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-4">
            {audits.map((audit) => {
              const summary = audit.summary ?? {};
              const processed = summary["processed_invoices"] as number | undefined;
              const findings = summary["total_findings"] as number | undefined;
              return (
                <li key={audit.id} className="flex items-center justify-between rounded border p-3">
                  <div>
                    <p className="font-medium">Execução #{audit.id}</p>
                    <span className="text-xs text-slate-500">
                      {processed ?? 0} notas analisadas · {findings ?? 0} achados
                    </span>
                  </div>
                  <span className="rounded-full bg-slate-200 px-3 py-1 text-xs font-semibold uppercase">
                    {audit.status}
                  </span>
                </li>
              );
            })}
            {audits.length === 0 && (
              <li className="rounded border border-dashed p-4 text-center text-sm text-slate-500">
                Nenhuma auditoria registrada até o momento.
              </li>
            )}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
};

export default AuditPage;
