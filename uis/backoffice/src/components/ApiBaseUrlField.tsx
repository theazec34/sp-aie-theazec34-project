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

/** Editable API base URL (defaults to same-origin proxy). */
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
        type="text"
        inputMode="url"
        spellCheck={false}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onBlur={() => commit(value)}
        placeholder={typeof window === "undefined" ? "" : detectApiBaseUrl()}
        autoComplete="off"
        aria-describedby="api-base-hint"
      />
      <span id="api-base-hint" className="api-base-hint">
        Recomendado: dejar la URL auto-detectada (proxy del panel) y pulsar
        «Usar auto-detectada» si cambias de entorno.
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
