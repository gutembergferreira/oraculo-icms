import { useEffect, useMemo, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "../components/Card";
import { api } from "../lib/api";

type RuleDefinition = {
  id: string;
  name: string;
  scope: string;
  then: { inconsistency_code: string; severity: string; message_pt: string };
};

type RuleSetContent = {
  yaml: string;
  metadata: Record<string, unknown>;
};

type RuleSetRead = {
  id: number;
  name: string;
  version: string;
  content: RuleSetContent & { rules: RuleDefinition[] };
};

type RuleEditorPayload = {
  baseline: RuleSetRead;
  override: RuleSetRead | null;
  effective_yaml: string;
  effective_rules: RuleDefinition[];
  metadata: Record<string, unknown>;
};

type RulePack = {
  slug: string;
  name: string;
  description?: string;
  version?: string;
  yaml: string;
};

const orgId = 1;

const RulesPage = () => {
  const [payload, setPayload] = useState<RuleEditorPayload | null>(null);
  const [overrideYaml, setOverrideYaml] = useState("");
  const [catalog, setCatalog] = useState<RulePack[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [rulesResp, catalogResp] = await Promise.all([
          api.get<RuleEditorPayload>(`/rules/orgs/${orgId}`),
          api.get<RulePack[]>(`/rules/catalog`),
        ]);
        setPayload(rulesResp.data);
        setOverrideYaml(rulesResp.data.override?.content.yaml ?? "");
        setCatalog(catalogResp.data);
      } catch (requestError) {
        setError("Não foi possível carregar o editor de regras.");
      } finally {
        setLoading(false);
      }
    };

    loadData().catch(() => setError("Erro inesperado ao buscar dados."));
  }, []);

  const handleSave = async () => {
    if (saving) return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await api.put(`/rules/orgs/${orgId}`, {
        yaml: overrideYaml,
        name: payload?.override?.name ?? "Override",
      });
      const refreshed = await api.get<RuleEditorPayload>(`/rules/orgs/${orgId}`);
      setPayload(refreshed.data);
      setOverrideYaml(refreshed.data.override?.content.yaml ?? overrideYaml);
      setSuccess("Regras salvas com sucesso.");
    } catch (saveError) {
      setError("Falha ao salvar o YAML. Verifique a sintaxe e tente novamente.");
    } finally {
      setSaving(false);
    }
  };

  const handleLoadPack = (pack: RulePack) => {
    setOverrideYaml(pack.yaml);
    setSuccess(`Pacote ${pack.name} carregado no editor.`);
  };

  const handleClearOverride = () => {
    setOverrideYaml("rules: []\n");
    setSuccess("Override substituído por um conjunto vazio.");
  };

  const effectiveRules = useMemo(
    () => payload?.effective_rules ?? [],
    [payload?.effective_rules]
  );

  if (loading) {
    return <p className="text-sm text-slate-600">Carregando regras...</p>;
  }

  if (!payload) {
    return (
      <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        {error ?? "Não foi possível carregar as regras desta organização."}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Editor de Regras</h1>
          <p className="text-sm text-slate-600">
            Gerencie a composição do baseline global com overrides específicos da organização.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
            onClick={handleClearOverride}
          >
            Usar apenas baseline
          </button>
          {catalog.map((pack) => (
            <button
              key={pack.slug}
              className="rounded-md border border-primary px-3 py-2 text-sm font-medium text-primary hover:bg-primary/10"
              onClick={() => handleLoadPack(pack)}
            >
              Carregar {pack.name}
            </button>
          ))}
          <button
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white shadow"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? "Salvando..." : "Salvar override"}
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}
      {success && (
        <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
          {success}
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>
              Baseline global <span className="text-xs text-slate-500">v{payload.baseline.version}</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <textarea
              className="h-72 w-full rounded-md border border-slate-200 bg-slate-50 p-3 font-mono text-xs text-slate-700"
              value={payload.baseline.content.yaml}
              readOnly
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Override da organização</CardTitle>
          </CardHeader>
          <CardContent>
            <textarea
              className="h-72 w-full rounded-md border border-slate-200 bg-white p-3 font-mono text-xs"
              value={overrideYaml}
              onChange={(event) => setOverrideYaml(event.target.value)}
              placeholder="rules: []"
            />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Regras efetivas</CardTitle>
          <p className="text-sm text-slate-600">
            Resultado da composição entre baseline e override para novos cálculos.
          </p>
        </CardHeader>
        <CardContent>
          <textarea
            className="mb-4 h-56 w-full rounded-md border border-slate-200 bg-slate-50 p-3 font-mono text-xs text-slate-700"
            value={payload.effective_yaml}
            readOnly
          />
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-3 py-2">ID</th>
                  <th className="px-3 py-2">Nome</th>
                  <th className="px-3 py-2">Escopo</th>
                  <th className="px-3 py-2">Código</th>
                  <th className="px-3 py-2">Severidade</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {effectiveRules.map((rule) => (
                  <tr key={rule.id}>
                    <td className="px-3 py-2 font-mono text-xs text-slate-600">{rule.id}</td>
                    <td className="px-3 py-2 text-slate-700">{rule.name}</td>
                    <td className="px-3 py-2 text-slate-500">{rule.scope}</td>
                    <td className="px-3 py-2 text-slate-600">{rule.then.inconsistency_code}</td>
                    <td className="px-3 py-2">
                      <span className="rounded bg-slate-100 px-2 py-1 text-xs uppercase text-slate-700">
                        {rule.then.severity}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default RulesPage;
