import { useCallback, useEffect, useMemo, useState } from "react";

import { API_BASE_URL } from "../config";
import { useAuth } from "../contexts/AuthContext";

type AdminUser = {
  id: number;
  email: string;
  first_name: string | null;
  last_name: string | null;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  organizations: string[];
};

const AdminUsersPage = () => {
  const { accessToken } = useAuth();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const headers = useMemo(() => {
    if (!accessToken) {
      return {};
    }
    return {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    };
  }, [accessToken]);

  const fetchUsers = useCallback(async () => {
    if (!accessToken) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users`, {
        headers,
      });
      if (!response.ok) {
        throw new Error("Falha ao carregar usuários");
      }
      const payload = (await response.json()) as AdminUser[];
      setUsers(payload);
    } catch (err) {
      console.error(err);
      setError("Não foi possível carregar a lista de usuários.");
    } finally {
      setLoading(false);
    }
  }, [accessToken, headers]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const updateUser = useCallback(
    async (userId: number, updates: Partial<Pick<AdminUser, "is_active" | "is_superuser">>) => {
      if (!accessToken) {
        return;
      }
      setUpdatingId(userId);
      setError(null);
      try {
        const response = await fetch(`${API_BASE_URL}/admin/users/${userId}`, {
          method: "PUT",
          headers,
          body: JSON.stringify(updates),
        });
        if (!response.ok) {
          throw new Error("Falha ao atualizar usuário");
        }
        const updated = (await response.json()) as AdminUser;
        setUsers((prev) => prev.map((user) => (user.id === updated.id ? updated : user)));
      } catch (err) {
        console.error(err);
        setError("Não foi possível atualizar o usuário selecionado.");
      } finally {
        setUpdatingId(null);
      }
    },
    [accessToken, headers]
  );

  if (loading) {
    return <div className="text-sm text-slate-500">Carregando usuários...</div>;
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-slate-900">Administração de Usuários</h1>
        <p className="mt-1 text-sm text-slate-600">
          Gerencie contas, permissões e status de acesso para toda a plataforma.
        </p>
      </header>

      {error ? <p className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 bg-white shadow">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Usuário</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Organizações</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Admin</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 text-sm">
            {users.map((user) => (
              <tr key={user.id}>
                <td className="px-4 py-3">
                  <div className="font-medium text-slate-900">{user.full_name}</div>
                  <div className="text-xs text-slate-500">{user.email}</div>
                </td>
                <td className="px-4 py-3 text-xs text-slate-600">
                  {user.organizations.length > 0 ? user.organizations.join(", ") : "—"}
                </td>
                <td className="px-4 py-3">
                  <label className="inline-flex cursor-pointer items-center gap-2 text-xs font-medium text-slate-600">
                    <input
                      checked={user.is_active}
                      className="h-4 w-4"
                      disabled={updatingId === user.id}
                      onChange={() => updateUser(user.id, { is_active: !user.is_active, is_superuser: user.is_superuser })}
                      type="checkbox"
                    />
                    Ativo
                  </label>
                </td>
                <td className="px-4 py-3">
                  <label className="inline-flex cursor-pointer items-center gap-2 text-xs font-medium text-slate-600">
                    <input
                      checked={user.is_superuser}
                      className="h-4 w-4"
                      disabled={updatingId === user.id}
                      onChange={() => updateUser(user.id, { is_superuser: !user.is_superuser, is_active: user.is_active })}
                      type="checkbox"
                    />
                    Superusuário
                  </label>
                </td>
                <td className="px-4 py-3 text-right text-xs text-slate-500">
                  Criado em {new Date(user.created_at).toLocaleDateString("pt-BR")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AdminUsersPage;
