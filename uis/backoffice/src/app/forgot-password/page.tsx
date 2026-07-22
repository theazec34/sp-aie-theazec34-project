"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import ApiBaseUrlField from "../../components/ApiBaseUrlField";
import { getApiBaseUrl, networkErrorMessage } from "../../lib/auth";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    const apiBase = getApiBaseUrl().replace(/\/$/, "");
    try {
      const response = await fetch(`${apiBase}/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim() }),
      });
      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        throw new Error(
          typeof detail.detail === "string"
            ? detail.detail
            : "No se pudo enviar la solicitud."
        );
      }
      setDone(true);
    } catch (err) {
      setError(networkErrorMessage(err, apiBase));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <p className="bo-kicker">Brasaland OPS</p>
        <h1>Recuperar contraseña</h1>
        <p className="bo-soft">
          Introduce tu email. Si está registrado, te enviaremos un enlace para
          elegir una nueva contraseña.
        </p>

        {done ? (
          <p className="bo-alert bo-alert-ok" role="status">
            Si esa dirección está en nuestro sistema, recibirás un enlace de
            restablecimiento. Revisa tu bandeja de entrada (y la consola de la
            API si estás en modo demo sin Resend).
          </p>
        ) : (
          <form className="auth-form" onSubmit={onSubmit}>
            <ApiBaseUrlField />
            <label className="bo-field">
              <span>Email</span>
              <input
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
              />
            </label>
            {error ? <p className="bo-alert bo-alert-error">{error}</p> : null}
            <button className="bo-btn bo-btn-primary" type="submit" disabled={loading}>
              {loading ? "Enviando…" : "Enviar enlace"}
            </button>
          </form>
        )}

        <p className="auth-footer">
          <Link href="/login">Volver a iniciar sesión</Link>
        </p>
      </section>
    </main>
  );
}
