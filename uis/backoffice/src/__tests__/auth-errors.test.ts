/**
 * @jest-environment jsdom
 */
import {
  clearToken,
  detectApiBaseUrl,
  getApiBaseUrl,
  getToken,
  networkErrorMessage,
  setStoredApiBaseUrl,
  setToken,
} from "../lib/auth";
import { parseApiErrorPayload } from "../lib/errors";

describe("token helpers", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("happy: setToken / getToken roundtrip", () => {
    setToken("abc.def.ghi");
    expect(getToken()).toBe("abc.def.ghi");
  });

  it("fail/edge: clearToken deja null", () => {
    setToken("abc");
    clearToken();
    expect(getToken()).toBeNull();
  });
});

describe("api base url", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("happy: en host local detectApiBaseUrl usa proxy same-origin", () => {
    expect(detectApiBaseUrl()).toBe("/api-backend");
    expect(getApiBaseUrl()).toBe("/api-backend");
  });

  it("edge: override en localStorage se respeta fuera de Codespaces", () => {
    setStoredApiBaseUrl("http://127.0.0.1:8000");
    expect(getApiBaseUrl()).toBe("http://127.0.0.1:8000");
  });

  it("Codespaces: auto-detect apunta al puerto 8000 del host", () => {
    const original = window.location;
    Object.defineProperty(window, "location", {
      configurable: true,
      value: {
        protocol: "https:",
        hostname: "amusing-space-3001.app.github.dev",
        port: "",
        origin: "https://amusing-space-3001.app.github.dev",
      },
    });
    localStorage.setItem("brasaland_api_base_url", "/api-backend");
    expect(detectApiBaseUrl()).toBe(
      "https://amusing-space-8000.app.github.dev"
    );
    expect(getApiBaseUrl()).toBe("https://amusing-space-8000.app.github.dev");
    Object.defineProperty(window, "location", {
      configurable: true,
      value: original,
    });
  });
});

describe("networkErrorMessage", () => {
  it("happy: Failed to fetch → mensaje legible con CTA implícita", () => {
    const msg = networkErrorMessage(
      new Error("Failed to fetch"),
      "/api-backend"
    );
    expect(msg).toMatch(/No se pudo conectar/);
    expect(msg).toMatch(/api-backend/);
  });

  it("fail mode: otros errores se reenvían", () => {
    expect(networkErrorMessage(new Error("boom"), "http://x")).toBe("boom");
  });
});

describe("parseApiErrorPayload", () => {
  it("happy: errors[] del handler 400", () => {
    const parsed = parseApiErrorPayload({
      detail: "Revisa los campos marcados",
      errors: [{ field: "email", message: "Email no válido" }],
    });
    expect(parsed.message).toMatch(/Revisa/);
    expect(parsed.fieldErrors.email).toBe("Email no válido");
  });

  it("fail mode: payload vacío / no objeto", () => {
    const parsed = parseApiErrorPayload(null);
    expect(parsed.message).toMatch(/No se pudo completar/);
    expect(parsed.fieldErrors).toEqual({});
  });
});
