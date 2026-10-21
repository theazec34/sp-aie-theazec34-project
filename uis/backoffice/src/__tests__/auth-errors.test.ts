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

  it("happy: detectApiBaseUrl usa proxy same-origin", () => {
    expect(detectApiBaseUrl()).toBe("/api-backend");
    expect(getApiBaseUrl()).toBe("/api-backend");
  });

  it("edge: override en localStorage se respeta", () => {
    setStoredApiBaseUrl("http://127.0.0.1:8000");
    expect(getApiBaseUrl()).toBe("http://127.0.0.1:8000");
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
