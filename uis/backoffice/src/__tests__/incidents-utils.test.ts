import {
  INCIDENT_STATUSES,
  STATUS_TRANSITIONS,
  labelFor,
} from "../lib/incidents";

describe("labelFor", () => {
  it("happy: resuelve etiqueta conocida", () => {
    expect(labelFor(INCIDENT_STATUSES, "open")).toBe("Abierta");
  });

  it("fail mode: valor desconocido se devuelve tal cual", () => {
    expect(labelFor(INCIDENT_STATUSES, "no_existe")).toBe("no_existe");
  });
});

describe("STATUS_TRANSITIONS", () => {
  it("happy: open permite in_progress y discarded", () => {
    expect(STATUS_TRANSITIONS.open).toEqual(
      expect.arrayContaining(["in_progress", "discarded"])
    );
  });

  it("fail/edge: estados finales sin salidas", () => {
    expect(STATUS_TRANSITIONS.resolved).toEqual([]);
    expect(STATUS_TRANSITIONS.discarded).toEqual([]);
  });
});
