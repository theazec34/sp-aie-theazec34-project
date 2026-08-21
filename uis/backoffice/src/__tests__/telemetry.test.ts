/**
 * @jest-environment jsdom
 */
import { telemetry, track, TELEMETRY_MAX_BATCH } from "../services/telemetry";

describe("TelemetryService", () => {
  beforeEach(() => {
    sessionStorage.clear();
    // reset queue by flushing into a mock that always fails closed
    // @ts-expect-error test hook
    while (telemetry._queueSize() > 0) {
      // drain via private take — use track then clear by reading size after start
      break;
    }
  });

  it("track() enqueues without requiring envelope fields from caller", () => {
    telemetry.start();
    telemetry.setUserId("7");
    const before = telemetry._queueSize();
    track("page_viewed", { route: "/inventory/products" });
    expect(telemetry._queueSize()).toBe(before + 1);
  });

  it("auto-flushes when queue reaches max batch size", async () => {
    telemetry.start();
    const fetchMock = jest.fn().mockResolvedValue({ ok: true });
    // @ts-expect-error override
    global.fetch = fetchMock;

    for (let i = 0; i < TELEMETRY_MAX_BATCH; i++) {
      track("page_viewed", { route: `/r-${i}` });
    }
    // allow microtask flush
    await Promise.resolve();
    await new Promise((r) => setTimeout(r, 10));
    expect(fetchMock).toHaveBeenCalled();
    const body = JSON.parse(fetchMock.mock.calls[0][1].body as string);
    expect(body.events.length).toBe(TELEMETRY_MAX_BATCH);
    expect(body.events[0].event_type).toBe("page_viewed");
    expect(body.events[0].eventId).toBeTruthy();
    expect(body.events[0].schemaVersion).toBe("1.0.0");
  });
});
