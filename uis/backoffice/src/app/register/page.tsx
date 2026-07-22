"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { getApiBaseUrl, loginRequest, setToken } from "../../lib/auth";

type FieldErrors = Record<string, string>;

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setFieldErrors({});
    setLoading(true);

    const apiBase = getApiBaseUrl().replace(/\/$/, "");
    try {
      const response = await fetch(`${apiBase}/users`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.trim(),
          password,
          name: name.trim() || null,
          phone: phone.trim() || null,
          address: address.trim() || null,
        }),
      });

      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        if (Array.isArray(detail.detail)) {
          const next: FieldErrors = {};
          for (const item of detail.detail) {
            const field = Array.isArray(item.loc) ? String(item.loc.at(-1)) : "form";
            next[field] = item.msg || "Valor inválido";
          }
          setFieldErrors(next);
          throw new Error("Revisa los campos marcados.");
        }
        throw new Error(
          typeof detail.detail === "string"
            ? detail.detail
            : "No se pudo completar el registro."
        );
      }

      const token = await loginRequest(apiBase, email.trim(), password);
      setToken(token);
      router.replace("/account/profile");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-card auth-card-wide">
        <p className="bo-kicker">Brasaland OPS</p>
        <h1>Crear cuenta</h1>
        <p className="bo-soft">
          Registra credenciales y, si quieres, datos de perfil (nombre y contacto).
        </p>

        <form className="auth-form" onSubmit={onSubmit}>
          <label className="bo-field">
            <span>Email</span>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            {fieldErrors.email ? (
              <span className="field-error">{fieldErrors.email}</span>
            ) : null}
          </label>
          <label className="bo-field">
            <span>Contraseña (mín. 8)</span>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            {fieldErrors.password ? (
              <span className="field-error">{fieldErrors.password}</span>
            ) : null}
          </label>
          <label className="bo-field">
            <span>Nombre (opcional)</span>
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </label>
          <label className="bo-field">
            <span>Teléfono (opcional)</span>
            <input value={phone} onChange={(e) => setPhone(e.target.value)} />
          </label>
          <label className="bo-field">
            <span>Dirección (opcional)</span>
            <input value={address} onChange={(e) => setAddress(e.target.value)} />
          </label>

          {error ? <p className="bo-alert bo-alert-error">{error}</p> : null}
          <button className="bo-btn bo-btn-primary" type="submit" disabled={loading}>
            {loading ? "Creando…" : "Registrarme"}
          </button>
        </form>

        <p className="auth-footer">
          ¿Ya tienes cuenta? <Link href="/login">Inicia sesión</Link>
        </p>
      </section>
    </main>
  );
}
