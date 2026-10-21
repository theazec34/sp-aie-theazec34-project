"use client";

import { FormEvent, useMemo, useState } from "react";
import { restaurant } from "@/data/site";
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

type Status = "idle" | "ready" | "error";

export function ReservationForm() {
  const [form, setForm] = useState(INITIAL);
  const [errors, setErrors] = useState<ReservationFormErrors>({});
  const [status, setStatus] = useState<Status>("idle");
  const [submitting, setSubmitting] = useState(false);

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

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    try {
      const validation = validate(form);
      setErrors(validation);
      if (Object.keys(validation).length) {
        setStatus("error");
        const first = Object.keys(validation)[0];
        document.getElementById(`res-${first}`)?.focus();
        return;
      }
      // Sin endpoint de reservas: preparamos mailto / estado listo (no fingimos confirmación).
      setStatus("ready");
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
            aria-describedby={errors.fullName ? "err-fullName" : undefined}
          />
          {errors.fullName ? (
            <span id="err-fullName" className="field-error" role="alert">
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
            aria-describedby={errors.phone ? "err-phone" : undefined}
          />
          {errors.phone ? (
            <span id="err-phone" className="field-error" role="alert">
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
            aria-describedby={errors.email ? "err-email" : undefined}
          />
          {errors.email ? (
            <span id="err-email" className="field-error" role="alert">
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
        Esta solicitud no confirma mesa automáticamente
        {INTEGRATIONS.reservations.ready
          ? "."
          : `: aún no hay motor de reservas (${INTEGRATIONS.reservations.suggestedPath}).`}{" "}
        Al validar el formulario podrás enviarla por correo a{" "}
        <strong>{restaurant.email}</strong> o llamarnos.
      </p>

      <div className="form-actions">
        <button className="cta" type="submit" disabled={submitting}>
          {submitting ? "Validando…" : "Preparar solicitud"}
        </button>
        {status === "ready" ? (
          <a className="cta cta-ghost" href={mailto}>
            Enviar por correo
          </a>
        ) : null}
      </div>

      {status === "ready" ? (
        <p className="form-status form-status-ok" role="status">
          Datos válidos. La reserva no está confirmada hasta que el restaurante responda.
          Usa «Enviar por correo» o llama al {restaurant.phone}
          {restaurant.phoneIsPlaceholder ? " [teléfono provisional]" : ""}.
        </p>
      ) : null}
      {status === "error" || hasErrors ? (
        <p className="form-status form-status-error" role="alert">
          Revisa los campos marcados.
        </p>
      ) : null}
    </form>
  );
}
