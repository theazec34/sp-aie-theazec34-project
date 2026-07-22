"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AppNav from "../../../components/AppNav";
import RequireAuth from "../../../components/RequireAuth";
import { apiFetch } from "../../../lib/api";
import { getToken } from "../../../lib/auth";

type AuthMe = {
  email: string;
  role: string;
  profile: {
    id: number;
    user_id: number;
    name: string;
    phone: string | null;
    address: string | null;
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

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }

    async function load() {
      setLoading(true);
      setError("");
      try {
        const response = await apiFetch("/auth/me");
        if (!response.ok) {
          throw new Error(`Error HTTP ${response.status}`);
        }
        const data = (await response.json()) as AuthMe;
        setEmail(data.email);
        setRole(data.role);
        setName(data.profile?.name || "");
        setPhone(data.profile?.phone || "");
        setAddress(data.profile?.address || "");
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [router]);

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
        const detail = await response.json().catch(() => ({}));
        throw new Error(
          typeof detail.detail === "string"
            ? detail.detail
            : `Error HTTP ${response.status}`
        );
      }
      setMessage("Perfil actualizado correctamente.");
    } catch (err) {
      setError((err as Error).message);
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
            {error ? <p className="bo-alert bo-alert-error">{error}</p> : null}
            {message ? <p className="bo-alert bo-alert-ok">{message}</p> : null}

            {!loading ? (
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
