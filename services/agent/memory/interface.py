"""Explicit read/write memory interface used by the LangGraph agent.

Memory is never implicit system-prompt accumulation and never touches RAG.
"""

from __future__ import annotations

from agent.memory.audit import append_audit
from agent.memory.confirm import ConfirmResult, classify_confirmation
from agent.memory.models import (
    AuditRecord,
    DecisionOutcome,
    MemoryEntry,
    MemoryProposal,
    PendingProposal,
)
from agent.memory.pending import clear_pending, get_pending, set_pending
from agent.memory.policy import extract_location, forbidden_reason
from agent.memory.self_eval import evaluate_for_memory, format_proposal_question
from agent.memory.store import MEMORY_NAMESPACE, get_memory_store


class AgentMemory:
    """Facade: read / propose / confirm / audit / consolidate."""

    namespace = MEMORY_NAMESPACE  # brasaland_agent_memory — not *_knowledge

    def read_relevant(self, question: str, *, limit: int = 8) -> list[MemoryEntry]:
        store = get_memory_store()
        loc = extract_location(question)
        if loc:
            hits = store.read(location=loc, limit=limit)
            if hits:
                return hits
        return store.read(limit=limit)

    def format_context(self, entries: list[MemoryEntry]) -> str:
        if not entries:
            return ""
        lines = ["[agent_memory — approved operational facts]"]
        for e in entries:
            loc = e.location or "global"
            lines.append(f"- ({loc}/{e.category.value}) {e.fact}")
        return "\n".join(lines)

    def self_evaluate(self, user_message: str, agent_answer: str = "") -> MemoryProposal | None:
        result = evaluate_for_memory(user_message, agent_answer)
        if not result.memorable or result.propuesta_memoria is None:
            return None
        # Policy double-check on proposed fact
        if forbidden_reason(result.propuesta_memoria.fact):
            return None
        return result.propuesta_memoria

    def propose(
        self,
        session_id: str,
        proposal: MemoryProposal,
        *,
        allow_if_pending: bool = False,
    ) -> str | None:
        """
        Attach proposal to the user-facing answer. Does NOT write memory.
        Returns None if another proposal is already pending (unless cleared).
        """
        existing = get_pending(session_id)
        if existing is not None and not allow_if_pending:
            return None
        set_pending(PendingProposal(session_id=session_id, proposal=proposal))
        return format_proposal_question(proposal)

    def handle_confirmation(
        self,
        session_id: str,
        user_message: str,
        *,
        user_id: str | None = None,
    ) -> tuple[str, DecisionOutcome | None, ConfirmResult | None]:
        """
        If a proposal is pending, classify the user message and resolve it.

        Returns (status_message, outcome, confirm_result).
        status_message empty means "no pending — continue normal flow".
        """
        pending = get_pending(session_id)
        if pending is None:
            return "", None, None

        result = classify_confirmation(user_message)
        proposal = pending.proposal

        if result.label == "approve":
            outcome = DecisionOutcome.APPROVED
            self._commit(proposal, user_id=user_id)
            clear_pending(session_id)
            msg = self._ack(proposal.language, "approved")
        elif result.label == "edit" and result.edited_fact:
            if forbidden_reason(result.edited_fact):
                outcome = DecisionOutcome.DISCARDED_POLICY
                clear_pending(session_id)
                msg = self._ack(proposal.language, "policy")
            else:
                edited = proposal.model_copy(update={"fact": result.edited_fact})
                outcome = DecisionOutcome.EDITED
                self._commit(edited, user_id=user_id)
                clear_pending(session_id)
                proposal = edited
                msg = self._ack(proposal.language, "edited")
        elif result.label == "reject":
            outcome = DecisionOutcome.REJECTED
            clear_pending(session_id)
            msg = self._ack(proposal.language, "rejected")
        elif result.label == "topic_change":
            outcome = DecisionOutcome.DISCARDED_TOPIC_CHANGE
            clear_pending(session_id)
            # No approval by silence; continue so caller can answer the new topic
            msg = ""
        else:
            # ambiguous → discard by default (never silent approve)
            outcome = DecisionOutcome.DISCARDED_AMBIGUOUS
            clear_pending(session_id)
            msg = self._ack(proposal.language, "ambiguous")

        append_audit(
            AuditRecord(
                session_id=session_id,
                proposal=proposal,
                outcome=outcome,
                user_message=user_message,
                confirm_label=result.label,
                edited_fact=result.edited_fact,
                metadata={"user_id": user_id},
            )
        )
        return msg, outcome, result

    def _commit(self, proposal: MemoryProposal, *, user_id: str | None) -> MemoryEntry:
        entry = MemoryEntry(
            fact=proposal.fact,
            location=proposal.location,
            category=proposal.category,
            language=proposal.language,
            source_message=proposal.source_message,
            proposal_id=proposal.proposal_id,
            approved_by=user_id,
        )
        return get_memory_store().write(entry)

    @staticmethod
    def _ack(lang: str, kind: str) -> str:
        es = {
            "approved": "Hecho. Lo recordaré en próximas conversaciones.",
            "edited": "Hecho. Guardé la versión editada.",
            "rejected": "Entendido. No lo guardaré.",
            "ambiguous": (
                "No quedó claro si debía recordarlo; lo descarto por defecto "
                "(no asumo aprobación)."
            ),
            "policy": "No puedo guardar ese dato (política de memoria). Descartado.",
        }
        en = {
            "approved": "Done. I'll remember that next time.",
            "edited": "Done. Saved the edited version.",
            "rejected": "Understood. I won't save it.",
            "ambiguous": (
                "It wasn't clear whether to remember that; discarding by default "
                "(no silent approval)."
            ),
            "policy": "I can't store that (memory policy). Discarded.",
        }
        table = en if lang == "en" else es
        return table[kind]


def get_agent_memory() -> AgentMemory:
    return AgentMemory()
