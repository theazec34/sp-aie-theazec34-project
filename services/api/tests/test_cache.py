"""TTL cache behaviour for summary + suppliers list (with invalidation)."""

from __future__ import annotations

from app.cache import incidents_cache, suppliers_cache


def test_incidents_summary_cache_hit_and_invalidation(client):
    incidents_cache.clear()

    first = client.get("/api/incidents/summary")
    assert first.status_code == 200
    assert first.headers.get("X-Cache") == "MISS"
    body = first.json()

    second = client.get("/api/incidents/summary")
    assert second.status_code == 200
    assert second.headers.get("X-Cache") == "HIT"
    assert second.json() == body

    created = client.post(
        "/api/incidents",
        json={
            "title": "Cache invalidation probe",
            "description": "Ensures summary cache clears on write.",
            "category": "other",
            "origin": "internal",
            "branch": "central",
        },
    )
    assert created.status_code == 201

    third = client.get("/api/incidents/summary")
    assert third.status_code == 200
    assert third.headers.get("X-Cache") == "MISS"
    assert third.json()["total"] >= body["total"]


def test_suppliers_list_cache_hit_and_invalidation(client, auth_header):
    suppliers_cache.clear()

    first = client.get("/suppliers", headers=auth_header)
    assert first.status_code == 200
    assert first.headers.get("X-Cache") == "MISS"
    count = len(first.json())

    second = client.get("/suppliers", headers=auth_header)
    assert second.status_code == 200
    assert second.headers.get("X-Cache") == "HIT"
    assert len(second.json()) == count

    filtered = client.get("/suppliers?country=Colombia", headers=auth_header)
    assert filtered.status_code == 200
    assert filtered.headers.get("X-Cache") == "MISS"

    filtered_hit = client.get("/suppliers?country=Colombia", headers=auth_header)
    assert filtered_hit.status_code == 200
    assert filtered_hit.headers.get("X-Cache") == "HIT"

    # Write path clears list namespace so next unfiltered read is a miss.
    create = client.post(
        "/suppliers",
        headers=auth_header,
        json={
            "name": "Cache Probe Supplier",
            "country": "USA",
            "categories": ["packaging"],
            "rate_per_unit": 3.5,
            "currency": "USD",
            "status": "active",
        },
    )
    assert create.status_code == 201

    after_write = client.get("/suppliers", headers=auth_header)
    assert after_write.status_code == 200
    assert after_write.headers.get("X-Cache") == "MISS"
    assert len(after_write.json()) == count + 1
