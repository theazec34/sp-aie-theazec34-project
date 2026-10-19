"""Persistence helpers for RFP tickets (SQLModel Session)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session, select

from app.rfp.departments import DEPARTMENTS
from app.rfp.models import DepartmentSection, RfpMetadata, RfpTicket
from app.rfp.schemas import (
    DepartmentSectionOut,
    RfpMetadataOut,
    RfpTicketOut,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_ticket(
    session: Session,
    *,
    raw_pdf_path: str,
    original_filename: str,
) -> RfpTicket:
    ticket = RfpTicket(
        status="analizando",
        raw_pdf_path=raw_pdf_path,
        original_filename=original_filename,
    )
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket


def get_ticket(session: Session, ticket_id: int) -> RfpTicket | None:
    return session.get(RfpTicket, ticket_id)


def list_tickets(session: Session, *, limit: int = 50) -> list[RfpTicket]:
    stmt = select(RfpTicket).order_by(RfpTicket.id.desc()).limit(limit)
    return list(session.exec(stmt).all())


def update_ticket_status(
    session: Session,
    ticket_id: int,
    status: str,
    *,
    discard_reason: str | None = None,
    markdown_path: str | None = None,
    error_message: str | None = None,
    handoff_ready: bool | None = None,
    synthesizer_payload: dict[str, Any] | None = None,
) -> RfpTicket | None:
    ticket = session.get(RfpTicket, ticket_id)
    if ticket is None:
        return None
    ticket.status = status
    ticket.updated_at = _now()
    if discard_reason is not None:
        ticket.discard_reason = discard_reason
    if markdown_path is not None:
        ticket.markdown_path = markdown_path
    if error_message is not None:
        ticket.error_message = error_message
    if handoff_ready is not None:
        ticket.handoff_ready = handoff_ready
    if synthesizer_payload is not None:
        ticket.synthesizer_payload_json = json.dumps(
            synthesizer_payload, ensure_ascii=False
        )
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket


def upsert_metadata(session: Session, ticket_id: int, data: dict[str, Any]) -> RfpMetadata:
    existing = session.exec(
        select(RfpMetadata).where(RfpMetadata.ticket_id == ticket_id)
    ).first()
    payload = {
        "client_name": data.get("client_name"),
        "location": data.get("location"),
        "service_type": data.get("service_type"),
        "scope": data.get("scope"),
        "deadline": data.get("deadline"),
        "budget_range": data.get("budget_range"),
        "departments_needed_json": json.dumps(
            data.get("departments_needed") or [], ensure_ascii=False
        ),
        "flesch_kincaid": data.get("flesch_kincaid"),
        "gunning_fog": data.get("gunning_fog"),
        "word_count": data.get("word_count"),
        "is_rfp": bool(data.get("is_rfp")),
        "classifier_confidence": data.get("classifier_confidence"),
        "classifier_notes": data.get("classifier_notes"),
        "open_questions_json": json.dumps(
            data.get("open_questions") or [], ensure_ascii=False
        ),
    }
    if existing:
        for k, v in payload.items():
            setattr(existing, k, v)
        meta = existing
    else:
        meta = RfpMetadata(ticket_id=ticket_id, **payload)
    session.add(meta)
    session.commit()
    session.refresh(meta)
    return meta


def replace_department_sections(
    session: Session,
    ticket_id: int,
    sections: list[dict[str, Any]],
) -> list[DepartmentSection]:
    old = session.exec(
        select(DepartmentSection).where(DepartmentSection.ticket_id == ticket_id)
    ).all()
    for row in old:
        session.delete(row)
    session.commit()

    created: list[DepartmentSection] = []
    for sec in sections:
        dept = sec["department_id"]
        info = DEPARTMENTS.get(dept, {})
        row = DepartmentSection(
            ticket_id=ticket_id,
            department_id=dept,
            key_aspects_json=json.dumps(sec.get("key_aspects") or [], ensure_ascii=False),
            open_questions_json=json.dumps(
                sec.get("open_questions") or [], ensure_ascii=False
            ),
            contact_name=sec.get("contact_name") or info.get("owner"),
        )
        session.add(row)
        created.append(row)
    session.commit()
    for row in created:
        session.refresh(row)
    return created


def ticket_to_out(session: Session, ticket: RfpTicket) -> RfpTicketOut:
    meta = session.exec(
        select(RfpMetadata).where(RfpMetadata.ticket_id == ticket.id)
    ).first()
    sections = session.exec(
        select(DepartmentSection).where(DepartmentSection.ticket_id == ticket.id)
    ).all()
    meta_out = None
    if meta:
        meta_out = RfpMetadataOut(
            client_name=meta.client_name,
            location=meta.location,
            service_type=meta.service_type,
            scope=meta.scope,
            deadline=meta.deadline,
            budget_range=meta.budget_range,
            departments_needed=json.loads(meta.departments_needed_json or "[]"),
            flesch_kincaid=meta.flesch_kincaid,
            gunning_fog=meta.gunning_fog,
            word_count=meta.word_count,
            is_rfp=meta.is_rfp,
            classifier_confidence=meta.classifier_confidence,
            classifier_notes=meta.classifier_notes,
            open_questions=json.loads(meta.open_questions_json or "[]"),
        )
    synth = None
    if ticket.synthesizer_payload_json:
        try:
            synth = json.loads(ticket.synthesizer_payload_json)
        except json.JSONDecodeError:
            synth = {"raw": ticket.synthesizer_payload_json}
    return RfpTicketOut(
        ticket_id=ticket.id or 0,
        status=ticket.status,
        original_filename=ticket.original_filename,
        raw_pdf_path=ticket.raw_pdf_path,
        markdown_path=ticket.markdown_path,
        discard_reason=ticket.discard_reason,
        handoff_ready=ticket.handoff_ready,
        error_message=ticket.error_message,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        metadata=meta_out,
        department_sections=[
            DepartmentSectionOut(
                department_id=s.department_id,
                contact_name=s.contact_name,
                key_aspects=json.loads(s.key_aspects_json or "[]"),
                open_questions=json.loads(s.open_questions_json or "[]"),
                approval_status=s.approval_status,
            )
            for s in sections
        ],
        synthesizer_summary=synth,
    )
