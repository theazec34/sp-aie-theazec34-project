"use client";

import { FormEvent, useMemo, useState } from "react";
import { restaurant } from "@/data/site";
import { postJson } from "@/lib/api";
import { INTEGRATIONS } from "@/lib/integrations";
import type { ApplicationFormData, ApplicationFormErrors } from "@/types/site";

const INITIAL: ApplicationFormData = {
  name: "",
  email: "",
  phone: "",
  department: "",
  experience: "",
  message: "",
  privacy: false,
  cvName: "",
};

function validate(form: ApplicationFormData): ApplicationFormErrors {
  const errors: ApplicationFormErrors = {};
  if (!form.name.trim() || form.name.trim().length < 2) {
    errors.name = "El nombre es obligatorio.";
  }
  if (!form.email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    errors.email = "Correo no válido.";
  }
  if (!form.phone.trim() || !/^\+?[0-9\s\-()]{9,18}$/.test(form.phone)) {
    errors.phone = "Teléfono no válido.";
  }
  if (!form.department) errors.department = "Selecciona un puesto.";
  const years = Number(form.experience);
  if (!form.experience.trim() || !Number.isFinite(years) || years < 0 || years > 50) {
    errors.experience = "Indica años de experiencia (0–50).";
  }
  if (!form.message.trim() || form.message.trim().length < 10) {
    errors.message = "Cuéntanos tu experiencia (mín. 10 caracteres).";
  }
  if (!form.privacy) {
    errors.privacy = "Debes aceptar la política de privacidad.";
  }
  return errors;
}

export function JobApplicationForm() {
  const [form, setForm] = useState(INITIAL);
  const [errors, setErrors] = useState<ApplicationFormErrors>({});
  const [sent, setSent] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [serverMessage, setServerMessage] = useState("");
  const [ticketId, setTicketId] = useState<number | null>(null);

  function update<K extends keyof ApplicationFormData>(key: K, value: ApplicationFormData[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setErrors((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
    setSent(false);
  }

  const mailto = useMemo(() => {
    const subject = encodeURIComponent(`Candidatura Brasaland — ${form.department}`);
    const body = encodeURIComponent(
      [
        `Nombre: ${form.name}`,
        `Email: ${form.email}`,
        `Teléfono: ${form.phone}`,
        `Puesto: ${form.department}`,
        `Experiencia (años): ${form.experience}`,
        `CV: ${form.cvName || "no indicado"}`,
        "",
        form.message,
      ].join("\n")
    );
    return `mailto:rrhh@brasaland.com?subject=${subject}&body=${body}`;
  }, [form]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setServerMessage("");
    try {
      const validation = validate(form);
      setErrors(validation);
      if (Object.keys(validation).length) {
        const first = Object.keys(validation)[0];
        document.getElementById(first)?.focus();
        return;
      }

      const result = await postJson<{ id: number; status_message: string }>(
        INTEGRATIONS.careers.path,
        {
          name: form.name.trim(),
          email: form.email.trim(),
          phone: form.phone.trim(),
          department: form.department,
          experience_years: Number(form.experience),
          message: form.message.trim(),
          cv_filename: form.cvName || "",
          privacy_accepted: form.privacy,
        }
      );

      if (!result.ok) {
        setServerMessage(result.detail);
        return;
      }

      setTicketId(result.data.id);
      setServerMessage(result.data.status_message);
      setSent(true);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form id="aplicar" className="site-form" onSubmit={onSubmit} noValidate>
      <div className="form-grid">
        <label className="form-field">
          <span>Nombre completo</span>
          <input
            id="name"
            value={form.name}
            onChange={(e) => update("name", e.target.value)}
            autoComplete="name"
            aria-invalid={Boolean(errors.name)}
          />
          {errors.name ? <span className="field-error" role="alert">{errors.name}</span> : null}
        </label>
        <label className="form-field">
          <span>Correo electrónico</span>
          <input
            id="email"
            type="email"
            value={form.email}
            onChange={(e) => update("email", e.target.value)}
            autoComplete="email"
            aria-invalid={Boolean(errors.email)}
          />
          {errors.email ? <span className="field-error" role="alert">{errors.email}</span> : null}
        </label>
        <label className="form-field">
          <span>Teléfono</span>
          <input
            id="phone"
            type="tel"
            value={form.phone}
            onChange={(e) => update("phone", e.target.value)}
            autoComplete="tel"
            aria-invalid={Boolean(errors.phone)}
          />
          {errors.phone ? <span className="field-error" role="alert">{errors.phone}</span> : null}
        </label>
        <label className="form-field">
          <span>Puesto deseado</span>
          <select
            id="department"
            value={form.department}
            onChange={(e) => update("department", e.target.value)}
            aria-invalid={Boolean(errors.department)}
          >
            <option value="">Selecciona…</option>
            <option value="Sala">Sala y barra</option>
            <option value="Cocina">Cocina / parrilla</option>
            <option value="Operaciones">Operaciones</option>
            <option value="Otro">Otro</option>
          </select>
          {errors.department ? (
            <span className="field-error" role="alert">
              {errors.department}
            </span>
          ) : null}
        </label>
        <label className="form-field">
          <span>Años de experiencia</span>
          <input
            id="experience"
            type="number"
            min={0}
            max={50}
            value={form.experience}
            onChange={(e) => update("experience", e.target.value)}
            aria-invalid={Boolean(errors.experience)}
          />
          {errors.experience ? (
            <span className="field-error" role="alert">
              {errors.experience}
            </span>
          ) : null}
        </label>
        <label className="form-field">
          <span>CV (opcional — solo nombre de fichero)</span>
          <input
            id="cvName"
            type="file"
            accept=".pdf,.doc,.docx"
            onChange={(e) => update("cvName", e.target.files?.[0]?.name ?? "")}
          />
          <span className="field-hint">
            El archivo no se sube al servidor en esta versión; se guarda el nombre.
          </span>
        </label>
      </div>

      <label className="form-field">
        <span>Experiencia y motivación</span>
        <textarea
          id="message"
          rows={5}
          value={form.message}
          onChange={(e) => update("message", e.target.value)}
          maxLength={500}
          aria-invalid={Boolean(errors.message)}
        />
        {errors.message ? (
          <span className="field-error" role="alert">
            {errors.message}
          </span>
        ) : null}
      </label>

      <label className="form-check">
        <input
          id="privacy"
          type="checkbox"
          checked={form.privacy}
          onChange={(e) => update("privacy", e.target.checked)}
          aria-invalid={Boolean(errors.privacy)}
        />
        <span>
          He leído la <a href="/privacidad">política de privacidad</a> y consiento el
          tratamiento de mis datos para gestionar esta candidatura.
        </span>
      </label>
      {errors.privacy ? (
        <span className="field-error" role="alert">
          {errors.privacy}
        </span>
      ) : null}

      <p className="form-disclaimer">
        La candidatura se registra en el sistema de Brasaland. No implica contratación. Contacto
        de respaldo: {restaurant.email}.
      </p>

      <div className="form-actions">
        <button className="cta" type="submit" disabled={submitting}>
          {submitting ? "Enviando…" : "Enviar candidatura"}
        </button>
        {INTEGRATIONS.careers.mailtoFallback ? (
          <a className="cta cta-ghost" href={mailto}>
            Respaldo por correo
          </a>
        ) : null}
      </div>

      {sent ? (
        <p className="form-status form-status-ok" role="status">
          {serverMessage}
          {ticketId != null ? ` (ref. #${ticketId})` : ""}
        </p>
      ) : null}
      {!sent && serverMessage ? (
        <p className="form-status form-status-error" role="alert">
          {serverMessage}
        </p>
      ) : null}
    </form>
  );
}
