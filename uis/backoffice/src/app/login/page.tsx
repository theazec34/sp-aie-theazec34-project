"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { getApiBaseUrl, loginRequest, setToken } from "../../lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const token = await loginRequest(getApiBaseUrl(), email.trim(), password);
      setToken(token);
      router.replace("/proveedores");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <p className="bo-kicker">Brasaland OPS</p>
        <h1>Iniciar sesión</h1>
        <p className="bo-soft">Accede con tu email y contraseña de la API.</p>

        <form className="auth-form" onSubmit={onSubmit}>
          <label className="bo-field">
            <span>Email</span>
            <input
              type="email"
              required
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>
          <label className="bo-field">
            <span>Contraseña</span>
            <input
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          {error ? <p className="bo-alert bo-alert-error">{error}</p> : null}
          <button className="bo-btn bo-btn-primary" type="submit" disabled={loading}>
            {loading ? "Entrando…" : "Entrar"}
          </button>
        </form>

        <p className="auth-footer">
          ¿No tienes cuenta? <Link href="/register">Regístrate</Link>
        </p>
      </section>
    </main>
  );
}
