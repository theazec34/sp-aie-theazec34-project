"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AppNav from "../../../components/AppNav";
import RequireAuth from "../../../components/RequireAuth";
import { apiFetch } from "../../../lib/api";
import { getApiBaseUrl, getToken } from "../../../lib/auth";
import { friendlyCatch, readApiError } from "../../../lib/errors";

type AuthMe = {
  email?: string;
  role?: string;
  profile?: {
    id?: number;
    user_id?: number;
    name?: string | null;
    phone?: string | null;
    address?: string | null;
  } | null;
};

export default function AccountProfilePage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loadFailed, setLoadFailed] = useState(false);

  const load = useCallback(async () => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    setLoading(true);
    setError("");
    setLoadFailed(false);
    try {
      const response = await apiFetch("/auth/me");
      if (!response.ok) {
        const parsed = await readApiError(response);
        throw new Error(parsed.message);
      }
      const data = (await response.json()) as AuthMe;
      setEmail(data.email || "");
      setRole(data.role || "");
      setName(data.profile?.name || "");
      setPhone(data.profile?.phone || "");
      setAddress(data.profile?.address || "");
    } catch (err) {
      setLoadFailed(true);
      setError(friendlyCatch(err, getApiBaseUrl()));
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    void load();
  }, [load]);

  async function onSave(event: FormEvent) {
    event.preventDefault();
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    setSaving(true);
    setError("");
    setMessage("");
    try {
      const response = await apiFetch("/profiles/me", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          phone: phone.trim() || null,
          address: address.trim() || null,
        }),
      });
      if (!response.ok) {
        const parsed = await readApiError(response);
        throw new Error(parsed.message);
      }
      setMessage("Perfil actualizado correctamente.");
    } catch (err) {
      setError(friendlyCatch(err, getApiBaseUrl()));
    } finally {
      setSaving(false);
    }
  }

  return (
    <RequireAuth>
      <main className="bo-shell">
        <AppNav active="profile" />

        <section className="bo-content">
          <header className="bo-topbar">
            <div>
              <p className="bo-kicker">Cuenta</p>
              <h1>Mi perfil</h1>
            </div>
            <span className="bo-status">{role || "…"}</span>
          </header>

          <section className="bo-panel">
            {loading ? <p className="bo-soft">Cargando perfil…</p> : null}
            {error ? (
              <div className="bo-alert bo-alert-error">
                <p>{error}</p>
                {loadFailed ? (
                  <button
                    type="button"
                    className="bo-btn bo-btn-small"
                    onClick={() => void load()}
                  >
                    Reintentar
                  </button>
                ) : null}
              </div>
            ) : null}
            {message ? <p className="bo-alert bo-alert-ok">{message}</p> : null}

            {!loading && !loadFailed ? (
              <form className="auth-form" onSubmit={onSave}>
                <label className="bo-field">
                  <span>Email (solo lectura)</span>
                  <input value={email} readOnly />
                </label>
                <label className="bo-field">
                  <span>Nombre</span>
                  <input value={name} onChange={(e) => setName(e.target.value)} />
                </label>
                <label className="bo-field">
                  <span>Teléfono</span>
                  <input value={phone} onChange={(e) => setPhone(e.target.value)} />
                </label>
                <label className="bo-field">
                  <span>Dirección</span>
                  <input value={address} onChange={(e) => setAddress(e.target.value)} />
                </label>
                <button className="bo-btn bo-btn-primary" type="submit" disabled={saving}>
                  {saving ? "Guardando…" : "Guardar perfil"}
                </button>
              </form>
            ) : null}
          </section>
        </section>
      </main>
    </RequireAuth>
  );
}
