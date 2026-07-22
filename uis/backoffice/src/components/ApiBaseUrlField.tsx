"use client";

import { useState } from "react";
import {
  detectApiBaseUrl,
  getApiBaseUrl,
  setStoredApiBaseUrl,
} from "../lib/auth";

type Props = {
  onChange?: (url: string) => void;
};

/** Editable API base URL for Codespaces / local debugging. */
export default function ApiBaseUrlField({ onChange }: Props) {
  const [value, setValue] = useState(() =>
    typeof window === "undefined" ? "" : getApiBaseUrl()
  );

  function commit(next: string) {
    setStoredApiBaseUrl(next);
    const resolved = getApiBaseUrl();
    setValue(resolved);
    onChange?.(resolved);
  }

  return (
    <label className="bo-field api-base-field">
      <span>URL de la API</span>
      <input
        type="url"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onBlur={() => commit(value)}
        placeholder={typeof window === "undefined" ? "" : detectApiBaseUrl()}
        autoComplete="off"
      />
      <span className="api-base-hint">
        En Codespaces debe apuntar al puerto 8000 (Public). Borra el valor y pulsa
        «Usar auto-detectada» si hace falta.
      </span>
      <button
        type="button"
        className="api-base-reset"
        onClick={() => {
          setStoredApiBaseUrl("");
          const detected = detectApiBaseUrl();
          setValue(detected);
          onChange?.(detected);
        }}
      >
        Usar auto-detectada
      </button>
    </label>
  );
}
