"use client";

import { FormEvent, useMemo, useState } from "react";
import { ApplicationFormData, ApplicationFormErrors } from "@/types/site";

const INITIAL_FORM: ApplicationFormData = {
  name: "",
  email: "",
  phone: "",
  department: "",
  experience: "",
  message: "",
};

function validate(form: ApplicationFormData): ApplicationFormErrors {
  const errors: ApplicationFormErrors = {};

  if (!form.name.trim()) errors.name = "El nombre es obligatorio.";
  else if (form.name.trim().length < 2) errors.name = "El nombre debe tener al menos 2 caracteres.";

  if (!form.email.trim()) errors.email = "El correo electronico es obligatorio.";
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) errors.email = "Introduce un email valido.";

  if (!form.phone.trim()) errors.phone = "El telefono es obligatorio.";
  else if (!/^\+?[0-9\s\-()]{9,15}$/.test(form.phone)) {
    errors.phone = "Introduce un telefono valido (ej: +34 123 456 789).";
  }

  if (!form.department) errors.department = "Debes seleccionar un departamento.";

  if (!form.experience.trim()) errors.experience = "Los anos de experiencia son obligatorios.";
  else {
    const years = Number(form.experience);
    if (!Number.isFinite(years)) errors.experience = "Debe ser un numero valido.";
    else if (years < 0) errors.experience = "Los anos de experiencia no pueden ser negativos.";
    else if (years > 50) errors.experience = "Los anos de experiencia no pueden exceder 50.";
  }

  if (!form.message.trim()) errors.message = "El mensaje es obligatorio.";
  else if (form.message.trim().length < 10) errors.message = "El mensaje debe tener al menos 10 caracteres.";
  else if (form.message.trim().length > 500) errors.message = "El mensaje no puede exceder 500 caracteres.";

  return errors;
}

const FIELD_LABELS: Record<keyof ApplicationFormData, string> = {
  name: "Nombre completo",
  email: "Correo electronico",
  phone: "Telefono",
  department: "Departamento",
  experience: "Anos de experiencia",
  message: "Motivacion",
};

export function ApplicationForm() {
  const [form, setForm] = useState<ApplicationFormData>(INITIAL_FORM);
  const [errors, setErrors] = useState<ApplicationFormErrors>({});
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const hasErrors = useMemo(() => Object.keys(errors).length > 0, [errors]);

  function updateField<K extends keyof ApplicationFormData>(key: K, value: ApplicationFormData[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setErrors((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    try {
      const validation = validate(form);
      setErrors(validation);
      const valid = Object.keys(validation).length === 0;
      setSubmitted(valid);

      if (!valid) {
        const firstInvalid = Object.keys(validation)[0] as keyof ApplicationFormData;
        const el = document.getElementById(firstInvalid);
        el?.focus();
      }
    } finally {
      setSubmitting(false);
    }
  }

  function onReset() {
    setForm(INITIAL_FORM);
    setErrors({});
    setSubmitted(false);
  }

  return (
    <section id="aplicar" className="section">
      <div className="container">
        <h2 className="section-title">Formulario de aplicacion</h2>
        <p className="section-text">
          Version React + TypeScript del formulario del proyecto, con validacion en cliente.
        </p>

        {hasErrors ? (
          <div className="error-summary" role="alert" aria-live="assertive">
            <h3>Errores en el formulario</h3>
            <ul>
              {Object.entries(errors).map(([field, message]) =>
                message ? (
                  <li key={field}>
                    <button
                      type="button"
                      onClick={() => document.getElementById(field)?.focus()}
                      className="error-link"
                    >
                      {FIELD_LABELS[field as keyof ApplicationFormData]}: {message}
                    </button>
                  </li>
                ) : null,
              )}
            </ul>
          </div>
        ) : null}

        <form className="application-form" onSubmit={onSubmit} noValidate>
          <div className="form-grid">
            <label className="form-field">
              <span>Nombre completo</span>
              <input
                id="name"
                value={form.name}
                onChange={(e) => updateField("name", e.target.value)}
                aria-invalid={Boolean(errors.name)}
              />
              {errors.name ? <small className="form-error">{errors.name}</small> : null}
            </label>

            <label className="form-field">
              <span>Correo electronico</span>
              <input
                id="email"
                type="email"
                value={form.email}
                onChange={(e) => updateField("email", e.target.value)}
                aria-invalid={Boolean(errors.email)}
              />
              {errors.email ? <small className="form-error">{errors.email}</small> : null}
            </label>

            <label className="form-field">
              <span>Telefono</span>
              <input
                id="phone"
                value={form.phone}
                onChange={(e) => updateField("phone", e.target.value)}
                placeholder="+34 123 456 789"
                aria-invalid={Boolean(errors.phone)}
              />
              {errors.phone ? <small className="form-error">{errors.phone}</small> : null}
            </label>

            <label className="form-field">
              <span>Departamento</span>
              <select
                id="department"
                value={form.department}
                onChange={(e) => updateField("department", e.target.value)}
                aria-invalid={Boolean(errors.department)}
              >
                <option value="">Selecciona</option>
                <option value="cocina">Cocina</option>
                <option value="sala">Sala</option>
                <option value="gestion">Gestion</option>
                <option value="compras">Compras</option>
                <option value="eventos">Marketing/Eventos</option>
              </select>
              {errors.department ? <small className="form-error">{errors.department}</small> : null}
            </label>

            <label className="form-field">
              <span>Anos de experiencia</span>
              <input
                id="experience"
                type="number"
                min={0}
                max={50}
                value={form.experience}
                onChange={(e) => updateField("experience", e.target.value)}
                aria-invalid={Boolean(errors.experience)}
              />
              {errors.experience ? <small className="form-error">{errors.experience}</small> : null}
            </label>
          </div>

          <label className="form-field">
            <span>Motivacion</span>
            <textarea
              id="message"
              rows={5}
              maxLength={500}
              value={form.message}
              onChange={(e) => updateField("message", e.target.value)}
              aria-invalid={Boolean(errors.message)}
            />
            {errors.message ? <small className="form-error">{errors.message}</small> : null}
          </label>

          {!submitted ? (
            <div className="form-actions">
              <button type="submit" className="cta" disabled={submitting}>
                {submitting ? "Validando…" : "Enviar aplicacion"}
              </button>
              <button type="button" className="cta cta-secondary" onClick={onReset}>
                Limpiar formulario
              </button>
            </div>
          ) : null}

          {submitted && !hasErrors ? (
            <div className="form-success" role="status" aria-live="polite">
              <p>
                Validación local correcta. Este formulario de demo aún no envía
                datos a un servidor de RRHH.
              </p>
              <p>
                Si quieres postularte de verdad, escribe a{" "}
                <a href="mailto:rrhh@brasaland.example">rrhh@brasaland.example</a>{" "}
                o vuelve al inicio.
              </p>
              <div className="form-actions">
                <button type="button" className="cta cta-secondary" onClick={onReset}>
                  Editar otra vez
                </button>
                <a className="cta" href="/">
                  Ir al inicio
                </a>
              </div>
            </div>
          ) : null}
        </form>
      </div>
    </section>
  );
}
