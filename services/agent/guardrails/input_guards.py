"""Input-side guardrails — jailbreak, personal tasks, casual, sensitive probes."""

from __future__ import annotations

import re

from agent.guardrails.session_probes import note_message
from agent.guardrails.system_prompt import (
    JAILBREAK_REJECT_EN,
    JAILBREAK_REJECT_ES,
    PERSONAL_REJECT_EN,
    PERSONAL_REJECT_ES,
    SENSITIVE_REJECT_EN,
    SENSITIVE_REJECT_ES,
)
from agent.guardrails.types import FailureType, GuardDecision, InputClass
from agent.memory.policy import detect_language

# --- Jailbreak / instruction override (SECURITY) ---
_JAILBREAK = re.compile(
    r"("
    r"ignora(r)?\s+(tus\s+)?instrucciones|"
    r"ignore\s+(your\s+)?(previous\s+)?instructions|"
    r"olvida(r)?\s+que\s+trabajas|"
    r"forget\s+(that\s+)?you\s+(work|are)|"
    r"act[uú]a\s+como\s+(un\s+)?asistente|"
    r"act\s+as\s+(if\s+you\s+have\s+)?(an?\s+)?(unrestricted|ops\s+)?assistant|"
    r"sin\s+restricciones|"
    r"without\s+(any\s+)?(rules|restrictions)|"
    r"no\s+rules|"
    r"DAN\s+mode|"
    r"developer\s+mode|"
    r"system\s+prompt|"
    r"reveal\s+(your\s+)?instructions|"
    r"override\s+(your\s+)?(rules|guardrails|safety)"
    r")",
    re.I,
)

# --- Personal / off-company tasks (CONTENT) ---
_PERSONAL = re.compile(
    r"("
    r"escr[ií]b(e|eme|eme|ir)?\s+(un\s+)?(poema|ensayo|cuento|historia\s+de\s+amor)|"
    r"poema\s+de\s+amor|"
    r"write\s+(me\s+)?(an?\s+)?(poem|essay|love\s+letter|story)|"
    r"tarea\s+(escolar|de\s+la\s+universidad|universitaria)|"
    r"(school|university|homework)\b|"
    r"for\s+university|"
    r"c[oó]digo\s+(para\s+otro|de\s+otro)\s+proyecto|"
    r"code\s+for\s+(another|my\s+side)\s+project|"
    r"s[eé]\s+mi\s+terapeuta|"
    r"(be|act\s+as)\s+(my\s+)?therapist|"
    r"consejo\s+sentimental|"
    r"dating\s+advice|"
    r"haz(me)?\s+los\s+deberes|"
    r"climate\s+change\s+for\s+university"
    r")",
    re.I,
)

# --- Sensitive probes (SECURITY / CONTENT) ---
_SENSITIVE = re.compile(
    r"("
    r"receta\s+(madre|completa)|"
    r"mother\s+recipe|"
    r"f[oó]rmula\s+propietaria|"
    r"cantidades\s+exactas|"
    r"exact\s+(quantities|proportions|amounts)|"
    r"salsa\s+de\s+la\s+casa.{0,40}(cantidad|proporci|receta|ingrediente)|"
    r"house\s+sauce.{0,40}(recipe|ingredient|amount|quantity)|"
    r"costo\s+por\s+porci[oó]n|"
    r"cost\s+per\s+portion|"
    r"precio\s+negociado|"
    r"negotiated\s+price|"
    r"t[eé]rminos\s+del?\s+contrato|"
    r"contract\s+terms|"
    r"lo\s+que\s+le\s+cobramos\s+al\s+proveedor|"
    r"n[oó]mina|payroll|salario\s+de|"
    r"evaluaci[oó]n\s+de\s+desempe[nñ]o|"
    r"performance\s+review"
    r")",
    re.I,
)

# Single-ingredient gradual asks about the house sauce
_GRADUAL_RECIPE = re.compile(
    r"("
    r"(primer|segundo|tercer|otro|next|first|second|third)\s+ingrediente|"
    r"(dime|tell\s+me)\s+(solo\s+)?(el|un|one|the)\s+ingrediente|"
    r"ingrediente\s+\d|"
    r"qu[eé]\s+lleva\s+la\s+salsa|"
    r"what\s+(goes\s+into|is\s+in)\s+the\s+(house\s+)?sauce"
    r")",
    re.I,
)

# Casual / trivia (CONTENT redirect, not block)
_CASUAL = re.compile(
    r"("
    r"^(buenos\s+d[ií]as|buenas\s+tardes|buenas\s+noches|hola|hey|hi|hello|"
    r"good\s+(morning|afternoon|evening))[\s!.?¿¡]*$|"
    r"qu[eé]\s+tal\s+(tu\s+)?turno|"
    r"how('?s|\s+is)\s+(your\s+)?shift|"
    r"qu[eé]\s+hora\s+es\s+en|"
    r"what\s+time\s+is\s+it\s+in|"
    r"capital\s+de\s+\w+|capital\s+of\s+\w+"
    r")",
    re.I,
)

# Domain hints (ops)
_DOMAIN = re.compile(
    r"("
    r"incidencia|ticket|inventario|stock|sku|procedimiento|playbook|"
    r"apertura|cierre|turno|localizaci[oó]n|location|sede|"
    r"proveedor|quality|calidad|ops|manager|brasaland|"
    r"al[eé]rgeno|loyalty|brasa\s*points|manual"
    r")",
    re.I,
)


def classify_input(
    text: str,
    *,
    session_id: str = "default",
) -> GuardDecision:
    """Deterministic input classification for the harness (no live LLM)."""
    q = (text or "").strip()
    lang = detect_language(q)
    counts = note_message(session_id, q)

    if not q:
        return GuardDecision(
            action="block",
            input_class=InputClass.PERSONAL_TASK,
            failure_type=FailureType.STRUCTURAL,
            reason_code="empty_input",
            message="",
        )

    if _JAILBREAK.search(q):
        return GuardDecision(
            action="block",
            input_class=InputClass.JAILBREAK,
            failure_type=FailureType.SECURITY,
            reason_code="jailbreak_instruction_override",
            message=JAILBREAK_REJECT_EN if lang == "en" else JAILBREAK_REJECT_ES,
            details={"variant": "instruction_override"},
        )

    if _SENSITIVE.search(q) or (
        _GRADUAL_RECIPE.search(q) and counts["recipe_probes"] >= 1
    ):
        return GuardDecision(
            action="block",
            input_class=InputClass.SENSITIVE_PROBE,
            failure_type=FailureType.SECURITY,
            reason_code="sensitive_data_probe",
            message=SENSITIVE_REJECT_EN if lang == "en" else SENSITIVE_REJECT_ES,
            details={"session_probes": counts},
        )

    # Gradual recipe: first mild ask still blocked if clearly about house sauce recipe
    if _GRADUAL_RECIPE.search(q) and re.search(r"salsa|sauce|receta|recipe", q, re.I):
        return GuardDecision(
            action="block",
            input_class=InputClass.SENSITIVE_PROBE,
            failure_type=FailureType.SECURITY,
            reason_code="gradual_recipe_probe",
            message=SENSITIVE_REJECT_EN if lang == "en" else SENSITIVE_REJECT_ES,
            details={"session_probes": counts},
        )

    # Multi-turn: 2+ recipe probes in session → block even softer phrasing
    if counts["recipe_probes"] >= 2 and re.search(
        r"\b(ingrediente|ingredient|salsa|sauce|proporci|cantidad|tercero|third)\b",
        q,
        re.I,
    ):
        return GuardDecision(
            action="block",
            input_class=InputClass.SENSITIVE_PROBE,
            failure_type=FailureType.SECURITY,
            reason_code="gradual_recipe_session",
            message=SENSITIVE_REJECT_EN if lang == "en" else SENSITIVE_REJECT_ES,
            details={"session_probes": counts},
        )

    # Soft gradual: "el tercero / proporciones" after any prior recipe probe
    if counts["recipe_probes"] >= 1 and re.search(
        r"\b(tercero|third|proporci[oó]n|exacta|cantidad)\b", q, re.I
    ):
        return GuardDecision(
            action="block",
            input_class=InputClass.SENSITIVE_PROBE,
            failure_type=FailureType.SECURITY,
            reason_code="gradual_recipe_followup",
            message=SENSITIVE_REJECT_EN if lang == "en" else SENSITIVE_REJECT_ES,
            details={"session_probes": counts},
        )

    if _PERSONAL.search(q):
        return GuardDecision(
            action="block",
            input_class=InputClass.PERSONAL_TASK,
            failure_type=FailureType.CONTENT,
            reason_code="personal_chatbot_task",
            message=PERSONAL_REJECT_EN if lang == "en" else PERSONAL_REJECT_ES,
        )

    if _CASUAL.search(q) and not _DOMAIN.search(q):
        redirect = (
            "¡Hola! Aquí para ops de Brasaland — incidentes, inventario y "
            "procedimientos de turno. ¿En qué te ayudo con tu localización?"
            if lang != "en"
            else "Hi! I'm here for Brasaland ops — incidents, inventory, and "
            "shift procedures. How can I help your location?"
        )
        return GuardDecision(
            action="redirect",
            input_class=InputClass.CASUAL,
            failure_type=FailureType.CONTENT,
            reason_code="casual_redirect",
            message=redirect,
        )

    return GuardDecision(
        action="allow",
        input_class=InputClass.DOMAIN,
        failure_type=None,
        reason_code="in_domain",
    )
