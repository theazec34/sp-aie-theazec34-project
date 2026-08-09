"use client";

import Link from "next/link";
import { FormEvent, Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import ApiBaseUrlField from "../../components/ApiBaseUrlField";
import {
  getApiBaseUrl,
  loginRequest,
  networkErrorMessage,
  setToken,
} from "../../lib/auth";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const resetOk = searchParams.get("reset") === "ok";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    const apiBase = getApiBaseUrl().replace(/\/$/, "");
    try {
      const token = await loginRequest(apiBase, email.trim(), password);
      setToken(token);
      router.replace("/proveedores");
    } catch (err) {
      setError(networkErrorMessage(err, apiBase));
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      {resetOk ? (
        <p className="bo-alert bo-alert-ok" role="status">
          Contraseña actualizada. Ya puedes iniciar sesión con la nueva.
        </p>
      ) : null}
      <form className="auth-form" onSubmit={onSubmit}>
        <ApiBaseUrlField />
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
    </>
  );
}

export default function LoginPage() {
  return (
    <main className="auth-shell">
      <section className="auth-card">
        <p className="bo-kicker">Brasaland OPS</p>
        <h1>Iniciar sesión</h1>
        <p className="bo-soft">Accede con tu email y contraseña de la API.</p>

        <Suspense
          fallback={
            <div className="auth-form" aria-busy="true" aria-label="Cargando formulario">
              <div className="bo-field"><span>Email</span><input disabled /></div>
              <div className="bo-field"><span>Contraseña</span><input disabled type="password" /></div>
              <button className="bo-btn bo-btn-primary" type="button" disabled>
                Entrando…
              </button>
            </div>
          }
        >
          <LoginForm />
        </Suspense>

        <p className="auth-footer">
          <Link href="/forgot-password">¿Olvidaste tu contraseña?</Link>
        </p>
        <p className="auth-footer">
          ¿No tienes cuenta? <Link href="/register">Regístrate</Link>
        </p>
      </section>
    </main>
  );
}
