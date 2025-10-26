import { useEffect, useState } from "react";

import { API_BASE_URL } from "../config";

type HomeContent = {
  title: string;
  content: string;
};

const HomePage = () => {
  const [data, setData] = useState<HomeContent | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_BASE_URL}/public-api/content/home`, {
      method: "GET",
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error("Não foi possível carregar a página");
        }
        const payload = await response.json();
        setData({ title: payload.title, content: payload.content });
      })
      .catch((error) => {
        console.error(error);
        setData({
          title: "Oráculo ICMS",
          content:
            "Centralize a gestão tributária da sua empresa com análises inteligentes e integrações prontas.",
        });
      })
      .finally(() => setLoading(false));

    return () => controller.abort();
  }, []);

  if (loading) {
    return <div className="text-center text-slate-500">Carregando...</div>;
  }

  if (!data) {
    return <div className="text-center text-slate-500">Conteúdo não disponível.</div>;
  }

  return (
    <section className="space-y-6">
      <h1 className="text-4xl font-bold text-slate-900">{data.title}</h1>
      <div className="space-y-4 text-lg text-slate-600">
        {data.content.split("\n").map((paragraph, index) => (
          <p key={index}>{paragraph}</p>
        ))}
      </div>
      <div className="rounded-lg bg-slate-100 p-6 text-slate-700">
        <h2 className="text-2xl font-semibold">Integração simples com seu ERP</h2>
        <p className="mt-2">
          Utilize nossa API pública para conectar o Oráculo ICMS aos sistemas da sua empresa e
          acompanhar auditorias em tempo real.
        </p>
      </div>
    </section>
  );
};

export default HomePage;
