import { ChangeEvent, useEffect, useMemo, useRef, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "../components/Card";
import { api } from "../lib/api";

type InvoiceSummary = {
  id: number;
  access_key: string;
  emitente_cnpj: string;
  destinatario_cnpj: string;
  uf: string;
  issue_date: string;
  total_value: number;
  freight_value: number | null;
  has_st: boolean;
  findings_count: number;
};

type InvoiceItem = {
  id: number;
  seq: number;
  product_code: string;
  description: string;
  ncm: string | null;
  cfop: string | null;
  cst: string | null;
  total_value: number;
  quantity: number;
};

type AuditFinding = {
  id: number;
  rule_id: string;
  inconsistency_code: string;
  severity: string;
  message_pt: string;
  suggestion_code: string | null;
};

type InvoiceDetail = InvoiceSummary & {
  items: InvoiceItem[];
  findings: AuditFinding[];
};

const orgId = 1;

const formatCurrency = (value: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(
    value
  );

const InvoicesPage = () => {
  const [filter, setFilter] = useState("");
  const [invoices, setInvoices] = useState<InvoiceSummary[]>([]);
  const [selectedInvoice, setSelectedInvoice] = useState<InvoiceDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const xmlInputRef = useRef<HTMLInputElement | null>(null);
  const zipInputRef = useRef<HTMLInputElement | null>(null);

  const fetchInvoices = async () => {
    const response = await api.get<InvoiceSummary[]>(`/orgs/${orgId}/invoices`);
    setInvoices(response.data);
    if (response.data.length > 0) {
      await loadInvoiceDetail(response.data[0].id);
    } else {
      setSelectedInvoice(null);
    }
  };

  const loadInvoiceDetail = async (invoiceId: number) => {
    const response = await api.get<InvoiceDetail>(
      `/orgs/${orgId}/invoices/${invoiceId}`
    );
    setSelectedInvoice(response.data);
  };

  useEffect(() => {
    fetchInvoices().catch(() => setError("Não foi possível carregar as notas."));
  }, []);

  const filteredInvoices = useMemo(() => {
    if (!filter) return invoices;
    const term = filter.toLowerCase();
    return invoices.filter((invoice) =>
      invoice.emitente_cnpj.toLowerCase().includes(term) ||
      invoice.destinatario_cnpj.toLowerCase().includes(term) ||
      invoice.access_key.includes(filter)
    );
  }, [filter, invoices]);

  const handleUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      await api.post(`/orgs/${orgId}/uploads/xml`, formData);
      await fetchInvoices();
    } catch (uploadError) {
      setError("Falha ao enviar XML. Verifique o arquivo e tente novamente.");
    } finally {
      setLoading(false);
      if (xmlInputRef.current) {
        xmlInputRef.current.value = "";
      }
    }
  };

  const handleZipUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      await api.post(`/orgs/${orgId}/uploads/zip`, formData);
      await fetchInvoices();
    } catch (uploadError) {
      setError("Falha ao processar ZIP. Confirme o conteúdo antes de reenviar.");
    } finally {
      setLoading(false);
      if (zipInputRef.current) {
        zipInputRef.current.value = "";
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold">Notas Fiscais</h1>
        <div className="flex items-center gap-2">
          <button
            className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-white shadow"
            onClick={() => xmlInputRef.current?.click()}
            disabled={loading}
          >
            Upload XML
          </button>
          <button
            className="rounded-md border border-primary px-3 py-2 text-sm font-medium text-primary"
            onClick={() => zipInputRef.current?.click()}
            disabled={loading}
          >
            Importar ZIP
          </button>
          <input
            ref={xmlInputRef}
            type="file"
            accept=".xml"
            className="hidden"
            onChange={handleUpload}
          />
          <input
            ref={zipInputRef}
            type="file"
            accept=".zip"
            className="hidden"
            onChange={handleZipUpload}
          />
        </div>
      </div>

      <input
        className="w-full rounded-md border px-3 py-2 text-sm"
        placeholder="Filtrar por CNPJ ou chave de acesso"
        value={filter}
        onChange={(event) => setFilter(event.target.value)}
      />

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="grid gap-6 lg:grid-cols-[2fr,1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Notas importadas</CardTitle>
          </CardHeader>
          <CardContent>
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-xs uppercase tracking-wide text-slate-500">
                  <th className="py-2">Emitente</th>
                  <th>Destinatário</th>
                  <th>Chave de acesso</th>
                  <th className="text-right">Total</th>
                  <th className="text-center">Achados</th>
                </tr>
              </thead>
              <tbody>
                {filteredInvoices.map((invoice) => (
                  <tr
                    key={invoice.id}
                    className={`cursor-pointer border-t text-sm hover:bg-slate-50 ${
                      selectedInvoice?.id === invoice.id ? "bg-slate-100" : ""
                    }`}
                    onClick={() => loadInvoiceDetail(invoice.id)}
                  >
                    <td className="py-2 font-medium">{invoice.emitente_cnpj}</td>
                    <td>{invoice.destinatario_cnpj}</td>
                    <td className="font-mono text-xs">{invoice.access_key}</td>
                    <td className="text-right">
                      {formatCurrency(invoice.total_value)}
                    </td>
                    <td className="text-center font-semibold text-primary">
                      {invoice.findings_count}
                    </td>
                  </tr>
                ))}
                {filteredInvoices.length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-4 text-center text-sm text-slate-500">
                      Nenhuma nota encontrada.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Detalhes da nota</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            {selectedInvoice ? (
              <>
                <div>
                  <p className="font-semibold">Chave</p>
                  <p className="font-mono text-xs">{selectedInvoice.access_key}</p>
                </div>
                <div className="grid grid-cols-2 gap-4 text-xs text-slate-600">
                  <div>
                    <p className="font-semibold text-slate-900">Emitente</p>
                    <p>{selectedInvoice.emitente_cnpj}</p>
                  </div>
                  <div>
                    <p className="font-semibold text-slate-900">Destinatário</p>
                    <p>{selectedInvoice.destinatario_cnpj}</p>
                  </div>
                  <div>
                    <p className="font-semibold text-slate-900">Emissão</p>
                    <p>
                      {new Date(selectedInvoice.issue_date).toLocaleDateString("pt-BR")}
                    </p>
                  </div>
                  <div>
                    <p className="font-semibold text-slate-900">Total</p>
                    <p>{formatCurrency(selectedInvoice.total_value)}</p>
                  </div>
                </div>

                <div>
                  <p className="mb-2 font-semibold">Itens ({selectedInvoice.items.length})</p>
                  <ul className="space-y-2">
                    {selectedInvoice.items.map((item) => (
                      <li key={item.id} className="rounded border p-2">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-semibold">{item.description}</span>
                          <span className="font-mono">{formatCurrency(item.total_value)}</span>
                        </div>
                        <div className="mt-1 grid grid-cols-2 text-[11px] text-slate-500">
                          <span>CFOP: {item.cfop ?? "-"}</span>
                          <span>NCM: {item.ncm ?? "-"}</span>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <p className="mb-2 font-semibold">Achados ({selectedInvoice.findings.length})</p>
                  <ul className="space-y-2">
                    {selectedInvoice.findings.map((finding) => (
                      <li key={finding.id} className="rounded border border-orange-200 bg-orange-50 p-2">
                        <p className="text-xs font-semibold text-orange-800">
                          {finding.inconsistency_code} · {finding.severity.toUpperCase()}
                        </p>
                        <p className="text-xs text-slate-700">{finding.message_pt}</p>
                        {finding.suggestion_code && (
                          <p className="text-[11px] text-slate-500">
                            Sugestão: {finding.suggestion_code}
                          </p>
                        )}
                      </li>
                    ))}
                    {selectedInvoice.findings.length === 0 && (
                      <li className="rounded border border-emerald-200 bg-emerald-50 p-2 text-xs text-emerald-700">
                        Nenhuma inconsistência identificada para esta execução.
                      </li>
                    )}
                  </ul>
                </div>
              </>
            ) : (
              <p className="text-sm text-slate-500">
                Importe uma nota para visualizar os detalhes.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default InvoicesPage;
