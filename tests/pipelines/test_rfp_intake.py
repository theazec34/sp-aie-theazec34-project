"""Unit tests for RFP intake classifier + department workers + graph smoke."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
for _p in (_REPO, _REPO / "services", _REPO / "services" / "api"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from data.pipelines.rfp_intake.classifier import classify_rfp  # noqa: E402
from data.pipelines.rfp_intake.graph import run_rfp_intake  # noqa: E402
from data.pipelines.rfp_intake.workers import run_worker  # noqa: E402

_SEEDS = _REPO / "rfp-requests" / "brasaland"


def _md(name: str) -> str:
    return (_SEEDS / name).read_text(encoding="utf-8")


def test_classifier_accepts_formal_sunset_bay():
    result = classify_rfp(_md("brasaland-request-1.md"))
    assert result["is_rfp"] is True
    assert result["client_name"] == "Sunset Bay Resorts"
    assert "training" in result["departments_needed"]
    assert set(result["departments_needed"]) >= {
        "marketing",
        "operaciones",
        "procurement",
        "training",
    }


def test_classifier_accepts_informal_andes_tech():
    result = classify_rfp(_md("brasaland-request-2.md"))
    assert result["is_rfp"] is True
    assert result["client_name"] == "Andes Tech Solutions"
    assert "marketing" in result["departments_needed"]
    assert "operaciones" in result["departments_needed"]
    assert "procurement" in result["departments_needed"]
    # Informal standard menu — training should not be required
    assert "training" not in result["departments_needed"]


def test_classifier_rejects_franchise_inquiry():
    result = classify_rfp(_md("brasaland-request-3.md"))
    assert result["is_rfp"] is False
    assert result["departments_needed"] == []
    assert "franquicia" in (result["notes"] or "").lower() or "no es" in (
        result["notes"] or ""
    ).lower()


def test_operaciones_worker_does_not_invent_figures():
    md = _md("brasaland-request-2.md")
    meta = {
        "client_name": "Andes Tech Solutions",
        "budget_range": "USD 45,000 / año",
    }
    out = run_worker("operaciones", md, meta)
    assert out["department_id"] == "operaciones"
    assert out["contact_name"] == "Felipe Guerrero"
    assert out["key_aspects"]
    # Must not invent a montaje SLA under 10 days
    joined = " ".join(out["key_aspects"]).lower()
    assert "5 días hábiles" not in joined
    assert "3 días" not in joined


def test_marketing_worker_surfaces_client():
    out = run_worker(
        "marketing",
        _md("brasaland-request-1.md"),
        {"client_name": "Sunset Bay Resorts", "deadline": "15 November 2026"},
    )
    assert out["contact_name"] == "Camila Ospina"
    assert any("Sunset Bay" in a for a in out["key_aspects"])


def test_unknown_department_escalates_to_open_question():
    out = run_worker("legal", "some text", {})
    assert out["key_aspects"] == []
    assert any("BRIEFING" in q for q in out["open_questions"])


def test_graph_accepts_formal_md_fixture(tmp_path: Path):
    src = _SEEDS / "brasaland-request-1.md"
    dest = tmp_path / "r1.md"
    dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    final = run_rfp_intake(ticket_id=1, pdf_path=str(dest))
    assert final["status"] == "analisis_completo"
    assert final["synthesizer"]
    depts = {r["department_id"] for r in final["worker_results"]}
    assert "training" in depts
    assert "marketing" in depts
    # Claves normalizadas para persistencia SQLModel / UI
    meta = final["metadata"]
    assert meta.get("classifier_confidence") is not None
    assert meta.get("classifier_notes")
    assert any(
        line.startswith("Fecha límite:")
        for line in (final["synthesizer"].get("summary_lines") or [])
    )


def test_normalize_departments_aliases():
    from data.pipelines.rfp_intake.departments_ref import normalize_departments

    assert normalize_departments(["ops", "compras", "legal-desconocido"]) == [
        "marketing",
        "operaciones",
        "procurement",
    ]


def test_graph_discards_invalid_md_fixture(tmp_path: Path):
    src = _SEEDS / "brasaland-request-3.md"
    dest = tmp_path / "r3.md"
    dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    final = run_rfp_intake(ticket_id=3, pdf_path=str(dest))
    assert final["status"] == "descartado"
    assert final["worker_results"] == []
    assert final.get("discard_reason")


@pytest.mark.parametrize(
    "pdf_name,expect_status",
    [
        ("brasaland-request-1.pdf", "analisis_completo"),
        ("brasaland-request-2.pdf", "analisis_completo"),
        ("brasaland-request-3.pdf", "descartado"),
    ],
)
def test_graph_against_seed_pdfs(tmp_path: Path, pdf_name: str, expect_status: str):
    src = _SEEDS / pdf_name
    if not src.exists():
        pytest.skip(f"missing seed {pdf_name}")
    dest = tmp_path / pdf_name
    dest.write_bytes(src.read_bytes())
    final = run_rfp_intake(ticket_id=99, pdf_path=str(dest))
    assert final["status"] == expect_status
