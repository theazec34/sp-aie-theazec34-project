"use client";

import Link from "next/link";
import { FormEvent, Suspense, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import ApiBaseUrlField from "../../components/ApiBaseUrlField";
import { getApiBaseUrl, networkErrorMessage } from "../../lib/auth";

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = useMemo(() => searchParams.get("token")?.trim() || "", [searchParams]);

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");

    if (!token) {
      setError("Falta el token de restablecimiento en la URL.");
      return;
    }
    if (password !== confirm) {
      setError("La nueva contraseña y la confirmación no coinciden.");
      return;
    }

    setLoading(true);
    const apiBase = getApiBaseUrl().replace(/\/$/, "");
    try {
      const response = await fetch(`${apiBase}/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: password }),
      });
      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        throw new Error(
          typeof detail.detail === "string"
            ? detail.detail
            : "No se pudo restablecer la contraseña."
        );
      }
      router.replace("/login?reset=ok");
    } catch (err) {
      setError(networkErrorMessage(err, apiBase));
    } finally {
      setLoading(false);
    }
  }

  if (!token) {
    return (
      <>
        <p className="bo-alert bo-alert-error">
          Enlace inválido o incompleto: no hay token en la URL.
        </p>
        <p className="auth-footer">
          <Link href="/forgot-password">Solicitar un nuevo enlace</Link>
        </p>
      </>
    );
  }

  return (
    <form className="auth-form" onSubmit={onSubmit}>
      <ApiBaseUrlField />
      <label className="bo-field">
        <span>Nueva contraseña (mín. 8)</span>
        <input
          type="password"
          required
          minLength={8}
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </label>
      <label className="bo-field">
        <span>Confirmar contraseña</span>
        <input
          type="password"
          required
          minLength={8}
          autoComplete="new-password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
        />
      </label>
      {error ? (
        <div>
          <p className="bo-alert bo-alert-error">{error}</p>
          <p className="auth-footer" style={{ marginTop: 8 }}>
            <Link href="/forgot-password">Solicitar un nuevo enlace</Link>
          </p>
        </div>
      ) : null}
      <button className="bo-btn bo-btn-primary" type="submit" disabled={loading}>
        {loading ? "Guardando…" : "Guardar contraseña"}
      </button>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <main className="auth-shell">
      <section className="auth-card">
        <p className="bo-kicker">Brasaland OPS</p>
        <h1>Nueva contraseña</h1>
        <p className="bo-soft">
          Elige una contraseña nueva. El enlace del email solo es válido una vez
          y durante un tiempo limitado.
        </p>
        <Suspense fallback={<p className="bo-soft">Cargando…</p>}>
          <ResetPasswordForm />
        </Suspense>
        <p className="auth-footer">
          <Link href="/login">Volver a iniciar sesión</Link>
        </p>
      </section>
    </main>
  );
}
