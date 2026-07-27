/**
 * @jest-environment jsdom
 */
import {
  clearToken,
  getToken,
  networkErrorMessage,
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

describe("networkErrorMessage", () => {
  it("happy: Failed to fetch → mensaje legible con CTA implícita", () => {
    const msg = networkErrorMessage(
      new Error("Failed to fetch"),
      "https://example-8000.app.github.dev"
    );
    expect(msg).toMatch(/No se pudo conectar/);
    expect(msg).toMatch(/8000/);
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
