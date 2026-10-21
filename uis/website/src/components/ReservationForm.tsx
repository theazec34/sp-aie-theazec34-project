"use client";

import { FormEvent, useMemo, useState } from "react";
import { restaurant } from "@/data/site";
import { postJson } from "@/lib/api";
import { INTEGRATIONS } from "@/lib/integrations";
import type { ReservationFormData, ReservationFormErrors } from "@/types/site";

const INITIAL: ReservationFormData = {
  fullName: "",
  phone: "",
  email: "",
  date: "",
  time: "",
  guests: "2",
  notes: "",
};

function validate(form: ReservationFormData): ReservationFormErrors {
  const errors: ReservationFormErrors = {};
  if (!form.fullName.trim() || form.fullName.trim().length < 2) {
    errors.fullName = "Indica nombre y apellidos.";
  }
  if (!form.phone.trim() || !/^\+?[0-9\s\-()]{9,18}$/.test(form.phone)) {
    errors.phone = "Teléfono no válido.";
  }
  if (!form.email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    errors.email = "Correo no válido.";
  }
  if (!form.date) errors.date = "Elige una fecha.";
  if (!form.time) errors.time = "Elige una hora.";
  const guests = Number(form.guests);
  if (!Number.isFinite(guests) || guests < 1 || guests > 20) {
    errors.guests = "Comensales entre 1 y 20.";
  }
  return errors;
}

type Status = "idle" | "sent" | "error";

export function ReservationForm() {
  const [form, setForm] = useState(INITIAL);
  const [errors, setErrors] = useState<ReservationFormErrors>({});
  const [status, setStatus] = useState<Status>("idle");
  const [submitting, setSubmitting] = useState(false);
  const [serverMessage, setServerMessage] = useState("");
  const [ticketId, setTicketId] = useState<number | null>(null);

  const hasErrors = useMemo(() => Object.keys(errors).length > 0, [errors]);

  function update<K extends keyof ReservationFormData>(key: K, value: ReservationFormData[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setErrors((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
    setStatus("idle");
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setServerMessage("");
    try {
      const validation = validate(form);
      setErrors(validation);
      if (Object.keys(validation).length) {
        setStatus("error");
        const first = Object.keys(validation)[0];
        document.getElementById(`res-${first}`)?.focus();
        return;
      }

      const result = await postJson<{ id: number; message: string }>(
        INTEGRATIONS.reservations.path,
        {
          full_name: form.fullName.trim(),
          phone: form.phone.trim(),
          email: form.email.trim(),
          date: form.date,
          time: form.time.length === 5 ? `${form.time}:00` : form.time,
          guests: Number(form.guests),
          notes: form.notes.trim(),
        }
      );

      if (!result.ok) {
        setStatus("error");
        setServerMessage(result.detail);
        return;
      }

      setTicketId(result.data.id);
      setServerMessage(result.data.message);
      setStatus("sent");
    } finally {
      setSubmitting(false);
    }
  }

  const mailto = useMemo(() => {
    const subject = encodeURIComponent(`Reserva Brasaland — ${form.date} ${form.time}`);
    const body = encodeURIComponent(
      [
        `Nombre: ${form.fullName}`,
        `Teléfono: ${form.phone}`,
        `Email: ${form.email}`,
        `Fecha: ${form.date}`,
        `Hora: ${form.time}`,
        `Comensales: ${form.guests}`,
        `Notas: ${form.notes || "—"}`,
      ].join("\n")
    );
    return `mailto:${restaurant.email}?subject=${subject}&body=${body}`;
  }, [form]);

  return (
    <form className="site-form" onSubmit={onSubmit} noValidate>
      <div className="form-grid">
        <label className="form-field">
          <span>Nombre y apellidos</span>
          <input
            id="res-fullName"
            value={form.fullName}
            onChange={(e) => update("fullName", e.target.value)}
            autoComplete="name"
            aria-invalid={Boolean(errors.fullName)}
          />
          {errors.fullName ? (
            <span className="field-error" role="alert">
              {errors.fullName}
            </span>
          ) : null}
        </label>

        <label className="form-field">
          <span>Teléfono</span>
          <input
            id="res-phone"
            type="tel"
            value={form.phone}
            onChange={(e) => update("phone", e.target.value)}
            autoComplete="tel"
            aria-invalid={Boolean(errors.phone)}
          />
          {errors.phone ? (
            <span className="field-error" role="alert">
              {errors.phone}
            </span>
          ) : null}
        </label>

        <label className="form-field">
          <span>Correo electrónico</span>
          <input
            id="res-email"
            type="email"
            value={form.email}
            onChange={(e) => update("email", e.target.value)}
            autoComplete="email"
            aria-invalid={Boolean(errors.email)}
          />
          {errors.email ? (
            <span className="field-error" role="alert">
              {errors.email}
            </span>
          ) : null}
        </label>

        <label className="form-field">
          <span>Fecha</span>
          <input
            id="res-date"
            type="date"
            value={form.date}
            onChange={(e) => update("date", e.target.value)}
            aria-invalid={Boolean(errors.date)}
          />
          {errors.date ? (
            <span className="field-error" role="alert">
              {errors.date}
            </span>
          ) : null}
        </label>

        <label className="form-field">
          <span>Hora</span>
          <input
            id="res-time"
            type="time"
            value={form.time}
            onChange={(e) => update("time", e.target.value)}
            aria-invalid={Boolean(errors.time)}
          />
          {errors.time ? (
            <span className="field-error" role="alert">
              {errors.time}
            </span>
          ) : null}
        </label>

        <label className="form-field">
          <span>Comensales</span>
          <input
            id="res-guests"
            type="number"
            min={1}
            max={20}
            value={form.guests}
            onChange={(e) => update("guests", e.target.value)}
            aria-invalid={Boolean(errors.guests)}
          />
          {errors.guests ? (
            <span className="field-error" role="alert">
              {errors.guests}
            </span>
          ) : null}
        </label>
      </div>

      <label className="form-field">
        <span>Comentarios o necesidades especiales (opcional)</span>
        <textarea
          id="res-notes"
          rows={4}
          value={form.notes}
          onChange={(e) => update("notes", e.target.value)}
          maxLength={500}
        />
      </label>

      <p className="form-disclaimer">
        La solicitud se guarda en el sistema Brasaland con estado «recibida».{" "}
        <strong>No confirma mesa automáticamente</strong>: el restaurante debe
        validarla. Si la API no responde, puedes usar el correo de respaldo.
      </p>

      <div className="form-actions">
        <button className="cta" type="submit" disabled={submitting}>
          {submitting ? "Enviando…" : "Enviar solicitud"}
        </button>
        {INTEGRATIONS.reservations.mailtoFallback ? (
          <a className="cta cta-ghost" href={mailto}>
            Respaldo por correo
          </a>
        ) : null}
      </div>

      {status === "sent" ? (
        <p className="form-status form-status-ok" role="status">
          {serverMessage}
          {ticketId != null ? ` (ref. #${ticketId})` : ""}
        </p>
      ) : null}
      {status === "error" || hasErrors ? (
        <p className="form-status form-status-error" role="alert">
          {serverMessage || "Revisa los campos marcados."}
        </p>
      ) : null}
    </form>
  );
}
