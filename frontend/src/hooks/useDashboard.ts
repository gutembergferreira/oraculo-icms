export const useDashboardMetrics = () => {
  const data = {
    cards: [
      { title: "Notas auditadas", value: "128", description: "Últimos 30 dias" },
      { title: "Inconsistências", value: "32", description: "Classificadas por severidade" },
      { title: "Valor potencial", value: "R$ 145k", description: "Recuperável" }
    ]
  };

  return { data };
};
