"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import AppNav from "../../../components/AppNav";
import RequireAuth from "../../../components/RequireAuth";
import { apiFetch } from "../../../lib/api";
import { getApiBaseUrl } from "../../../lib/auth";
import { friendlyCatch, readApiError } from "../../../lib/errors";

export default function ChangePasswordPage() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setMessage("");

    if (newPassword !== confirm) {
      setError("La nueva contraseña y la confirmación no coinciden.");
      return;
    }

    setLoading(true);
    try {
      const response = await apiFetch("/auth/change-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });
      if (!response.ok) {
        const parsed = await readApiError(response);
        throw new Error(parsed.message);
      }
      const data = (await response.json()) as { message?: string };
      setMessage(data.message || "Contraseña cambiada correctamente.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirm("");
    } catch (err) {
      setError(friendlyCatch(err, getApiBaseUrl()));
    } finally {
      setLoading(false);
    }
  }

  return (
    <RequireAuth>
      <div className="bo-layout">
        <AppNav active="password" />
        <main className="bo-main">
          <header className="bo-header">
            <div>
              <p className="bo-kicker">Cuenta</p>
              <h1>Cambiar contraseña</h1>
              <p className="bo-soft">
                Introduce tu contraseña actual y la nueva. Deben coincidir la
                nueva y la confirmación antes de llamar a la API.
              </p>
            </div>
            <Link href="/account/profile" className="bo-btn">
              Volver al perfil
            </Link>
          </header>

          <section className="bo-panel" style={{ maxWidth: 480 }}>
            <form className="auth-form" onSubmit={onSubmit}>
              <label className="bo-field">
                <span>Contraseña actual</span>
                <input
                  type="password"
                  required
                  autoComplete="current-password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                />
              </label>
              <label className="bo-field">
                <span>Nueva contraseña (mín. 8)</span>
                <input
                  type="password"
                  required
                  minLength={8}
                  autoComplete="new-password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
              </label>
              <label className="bo-field">
                <span>Confirmar nueva contraseña</span>
                <input
                  type="password"
                  required
                  minLength={8}
                  autoComplete="new-password"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                />
              </label>
              {error ? <p className="bo-alert bo-alert-error">{error}</p> : null}
              {message ? <p className="bo-alert bo-alert-ok">{message}</p> : null}
              <button
                className="bo-btn bo-btn-primary"
                type="submit"
                disabled={loading}
              >
                {loading ? "Guardando…" : "Actualizar contraseña"}
              </button>
            </form>
          </section>
        </main>
      </div>
    </RequireAuth>
  );
}
