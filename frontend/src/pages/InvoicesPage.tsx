import { useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "../components/Card";

const mockInvoices = [
  {
    id: 1,
    fornecedor: "Fornecedor A",
    accessKey: "35180400000000000123550010000001231000001230",
    total: "R$ 12.500,00",
    status: "Sem inconsistências"
  },
  {
    id: 2,
    fornecedor: "Fornecedor B",
    accessKey: "35180400000000000123550010000009871000005432",
    total: "R$ 8.320,50",
    status: "2 apontamentos"
  }
];

const InvoicesPage = () => {
  const [filter, setFilter] = useState("");
  const invoices = mockInvoices.filter((invoice) =>
    invoice.fornecedor.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Notas Fiscais</h1>
        <button className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-white shadow">
          Upload XML
        </button>
      </div>
      <input
        className="w-full rounded-md border px-3 py-2 text-sm"
        placeholder="Filtrar por fornecedor"
        value={filter}
        onChange={(event) => setFilter(event.target.value)}
      />
      <Card>
        <CardHeader>
          <CardTitle>Últimas notas importadas</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="text-xs uppercase tracking-wide text-slate-500">
                <th className="py-2">Fornecedor</th>
                <th>Chave de acesso</th>
                <th>Total</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((invoice) => (
                <tr key={invoice.id} className="border-t text-sm">
                  <td className="py-2 font-medium">{invoice.fornecedor}</td>
                  <td className="font-mono text-xs">{invoice.accessKey}</td>
                  <td>{invoice.total}</td>
                  <td>{invoice.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
};

export default InvoicesPage;
