import { FormEvent, useEffect, useState } from "react";

import { API_BASE_URL } from "../config";
import { useAuth } from "../contexts/AuthContext";

type NavigationLink = {
  label: string;
  path: string;
};

type PageContent = {
  title: string;
  content: string;
};

const AdminPage = () => {
  const { accessToken } = useAuth();
  const [links, setLinks] = useState<NavigationLink[]>([]);
  const [page, setPage] = useState<PageContent>({ title: "", content: "" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    setLoading(true);
    const fetchJson = async (endpoint: string) => {
      const response = await fetch(endpoint, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!response.ok) {
        throw new Error("Falha ao carregar dados");
      }
      return response.json();
    };

    Promise.all([
      fetchJson(`${API_BASE_URL}/admin/navigation`),
      fetchJson(`${API_BASE_URL}/admin/pages/home`),
    ])
      .then(([navigation, page]) => {
        setLinks(navigation);
        setPage({ title: page.title, content: page.content });
      })
      .catch((error) => {
        console.error("Falha ao carregar dados administrativos", error);
        setMessage("Não foi possível carregar os dados administrativos.");
      })
      .finally(() => setLoading(false));
  }, [accessToken]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!accessToken) {
      return;
    }
    setSaving(true);
    setMessage(null);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/pages/home`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(page),
      });
      if (!response.ok) {
        throw new Error("Erro ao salvar");
      }
      const updated = await response.json();
      setPage({ title: updated.title, content: updated.content });
      setMessage("Página atualizada com sucesso!");
    } catch (error) {
      console.error(error);
      setMessage("Ocorreu um erro ao salvar as alterações.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="text-center text-slate-500">Carregando dados...</div>;
  }

  return (
    <div className="space-y-8">
      <section className="rounded-lg bg-white p-6 shadow">
        <h1 className="text-2xl font-semibold text-slate-900">Administração</h1>
        <p className="mt-2 text-sm text-slate-600">
          Acesse rapidamente todas as áreas da plataforma.
        </p>
        <ul className="mt-4 grid gap-2 sm:grid-cols-2">
          {links.map((link) => (
            <li key={link.path} className="rounded border px-4 py-2 text-sm">
              <span className="font-medium">{link.label}</span>
              <span className="block text-xs text-slate-500">{link.path}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="rounded-lg bg-white p-6 shadow">
        <h2 className="text-xl font-semibold text-slate-900">Editar página inicial</h2>
        <p className="mt-1 text-sm text-slate-600">
          Atualize o título e a mensagem exibidos para visitantes na landing page.
        </p>
        <form className="mt-4 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="text-sm font-medium" htmlFor="title">
              Título
            </label>
            <input
              className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
              id="title"
              value={page.title}
              onChange={(event) => setPage((prev) => ({ ...prev, title: event.target.value }))}
            />
          </div>
          <div>
            <label className="text-sm font-medium" htmlFor="content">
              Conteúdo
            </label>
            <textarea
              className="mt-1 h-40 w-full rounded-md border px-3 py-2 text-sm"
              id="content"
              value={page.content}
              onChange={(event) => setPage((prev) => ({ ...prev, content: event.target.value }))}
            />
          </div>
          <button
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white disabled:opacity-75"
            disabled={saving}
            type="submit"
          >
            {saving ? "Salvando..." : "Salvar alterações"}
          </button>
        </form>
        {message ? <p className="mt-3 text-sm text-slate-600">{message}</p> : null}
      </section>
    </div>
  );
};

export default AdminPage;
