import { useEffect, useMemo, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "../components/Card";
import { api } from "../lib/api";

type AuditRun = {
  id: number;
  status: string;
  summary: AuditSummary;
  findings: unknown[];
};

type AuditTopRule = {
  rule_id: string;
  inconsistency_code: string;
  severity: string;
  message_pt: string;
  count: number;
};

type AuditSummary = {
  processed_invoices: number;
  total_findings: number;
  invoices_with_findings: number;
  severity_breakdown: Record<string, number>;
  top_rules: AuditTopRule[];
  metadata: Record<string, unknown>;
};

type BaselineSummary = AuditSummary & {
  audit_run_id: number;
};

const orgId = 1;

const AuditPage = () => {
  const [audits, setAudits] = useState<AuditRun[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reportLoading, setReportLoading] = useState<string | null>(null);
  const [baselineSummary, setBaselineSummary] = useState<BaselineSummary | null>(null);

  const fetchAudits = async () => {
    const response = await api.get<AuditRun[]>(`/orgs/${orgId}/audits`);
    setAudits(response.data);
  };

  const fetchBaselineSummary = async () => {
    try {
      const response = await api.get<BaselineSummary>(
        `/orgs/${orgId}/audits/baseline/summary`
      );
      setBaselineSummary(response.data);
    } catch (baselineError: unknown) {
      setBaselineSummary(null);
    }
  };

  useEffect(() => {
    fetchAudits()
      .then(fetchBaselineSummary)
      .catch(() => setError("Não foi possível carregar as auditorias."));
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
      await fetchBaselineSummary();
    } catch (auditError) {
      setError("Não foi possível iniciar uma nova auditoria.");
    } finally {
      setLoading(false);
    }
  };

  const severityEntries = useMemo(() => {
    if (!baselineSummary) return [];
    return Object.entries(baselineSummary.severity_breakdown).sort((a, b) =>
      b[1] - a[1]
    );
  }, [baselineSummary]);

  const handleDownload = async (auditId: number, format: "pdf" | "xlsx") => {
    setReportLoading(`${auditId}-${format}`);
    setError(null);
    try {
      const response = await api.get(
        `/orgs/${orgId}/audits/${auditId}/reports/${format}`,
        {
          responseType: "blob",
        }
      );
      const blob = new Blob([response.data], {
        type: response.headers["content-type"] ?? "application/octet-stream",
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `audit-${auditId}.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (downloadError) {
      setError("Não foi possível gerar o relatório solicitado.");
    } finally {
      setReportLoading(null);
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
      {baselineSummary && (
        <Card>
          <CardHeader>
            <CardTitle>Auditoria baseline #{baselineSummary.audit_run_id}</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-6 md:grid-cols-2">
            <div className="space-y-2 text-sm">
              <p>
                <span className="font-semibold">Notas processadas:</span>{" "}
                {baselineSummary.processed_invoices}
              </p>
              <p>
                <span className="font-semibold">Notas com achados:</span>{" "}
                {baselineSummary.invoices_with_findings}
              </p>
              <p>
                <span className="font-semibold">Total de achados:</span>{" "}
                {baselineSummary.total_findings}
              </p>
              <div>
                <p className="font-semibold">Gravidade</p>
                <ul className="mt-1 space-y-1 text-xs text-slate-600">
                  {severityEntries.map(([severity, count]) => (
                    <li key={severity} className="flex justify-between">
                      <span>{severity.toUpperCase()}</span>
                      <span className="font-semibold text-slate-900">{count}</span>
                    </li>
                  ))}
                  {severityEntries.length === 0 && (
                    <li className="text-slate-500">Nenhum achado registrado.</li>
                  )}
                </ul>
              </div>
            </div>
            <div className="text-sm">
              <p className="font-semibold">Principais regras</p>
              <ul className="mt-2 space-y-2">
                {baselineSummary.top_rules.map((rule) => (
                  <li key={rule.rule_id} className="rounded border p-2 text-xs">
                    <p className="font-semibold text-slate-800">
                      {rule.inconsistency_code} · {rule.severity.toUpperCase()}
                    </p>
                    <p className="text-slate-600">{rule.message_pt}</p>
                    <p className="text-[11px] text-slate-500">Ocorrências: {rule.count}</p>
                  </li>
                ))}
                {baselineSummary.top_rules.length === 0 && (
                  <li className="text-xs text-slate-500">Nenhuma recorrência identificada.</li>
                )}
              </ul>
            </div>
          </CardContent>
        </Card>
      )}
      <Card>
        <CardHeader>
          <CardTitle>Execuções recentes</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-4">
            {audits.map((audit) => {
              const summary = audit.summary ?? {};
              const processed = summary.processed_invoices;
              const findings = summary.total_findings;
              return (
                <li key={audit.id} className="flex items-center justify-between rounded border p-3">
                  <div>
                    <p className="font-medium">Execução #{audit.id}</p>
                    <span className="text-xs text-slate-500">
                      {processed ?? 0} notas analisadas · {findings ?? 0} achados
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="rounded-full bg-slate-200 px-3 py-1 text-xs font-semibold uppercase">
                      {audit.status}
                    </span>
                    {audit.status === "done" && (
                      <div className="flex items-center gap-2">
                        <button
                          className="rounded border px-2 py-1 text-xs font-medium"
                          onClick={() => handleDownload(audit.id, "pdf")}
                          disabled={reportLoading === `${audit.id}-pdf`}
                        >
                          {reportLoading === `${audit.id}-pdf` ? "Baixando..." : "PDF"}
                        </button>
                        <button
                          className="rounded border px-2 py-1 text-xs font-medium"
                          onClick={() => handleDownload(audit.id, "xlsx")}
                          disabled={reportLoading === `${audit.id}-xlsx`}
                        >
                          {reportLoading === `${audit.id}-xlsx` ? "Baixando..." : "XLSX"}
                        </button>
                      </div>
                    )}
                  </div>
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
