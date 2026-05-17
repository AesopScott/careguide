import anthropic
import json
import os
import re

_client = None

SYSTEM_PROMPT = """You are a helpful assistant embedded in CareGuide, a platform for
geriatric care professionals and families managing elder care.

You help with: care plan drafting, summarizing intake interviews, drafting progress notes,
answering Medicare/insurance questions, and supporting family coordination.

You do NOT provide medical diagnoses, legal advice, or specific medication recommendations.
Always recommend consulting the appropriate licensed professional for those matters.
All AI-generated content should be reviewed by the practitioner before clinical use."""

def get_client() -> anthropic.Anthropic:
    global _client
    if not _client:
        _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client

def complete(prompt: str, model: str = "claude-haiku-4-5-20251001", max_tokens: int = 1024) -> str:
    client = get_client()
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text

def draft_care_plan(intake_transcript: str) -> str:
    prompt = f"""Draft a structured care plan based on this intake interview transcript.
Include: presenting situation, functional status, safety concerns, support network,
recommended interventions, and follow-up actions.

Transcript:
{intake_transcript}"""
    return complete(prompt, model="claude-sonnet-4-6", max_tokens=2048)

def draft_session_note(transcript: str) -> str:
    prompt = f"""Draft a professional progress note from this session transcript.
Include: date of service, presenting concerns, interventions provided,
client response, plan for next session. Format as a clinical progress note.

Transcript:
{transcript}"""
    return complete(prompt, model="claude-sonnet-4-6", max_tokens=1024)

def answer_question(question: str, context: str = "") -> str:
    prompt = f"{f'Context: {context}\n\n' if context else ''}Question: {question}"
    return complete(prompt, model="claude-haiku-4-5-20251001", max_tokens=512)


CARE_PLAN_SECTION_KEYS = (
    "situation",
    "goals",
    "interventions",
    "family_role",
    "barriers",
    "next_steps",
)

INTAKE_SECTION_LABELS = {
    "client_context":    "Client Context",
    "current_situation": "Current Situation",
    "medical_history":   "Medical History",
    "care_needs":        "Care Needs",
    "goals":             "Goals",
}

INTAKE_FIELD_LABELS = {
    "age":          "Age",
    "diagnosis":    "Diagnosis",
    "living":       "Living Situation",
    "caregivers":   "Caregivers",
    "prompt":       "Reason for Reaching Out",
    "functioning":  "Current Functioning",
    "changes":      "Recent Changes",
    "conditions":   "Conditions",
    "medications":  "Medications",
    "allergies":    "Allergies",
    "social":       "Social History",
    "challenges":   "Challenges",
    "services":     "Services in Place",
    "safety":       "Safety Concerns",
    "family":       "Family Dynamics",
    "client":       "Client Goals",
    "practitioner": "Practitioner Goals",
    "other":        "Other Notes",
}


def _flatten_intake(intake: dict) -> str:
    lines = []
    for section_key, fields in intake.items():
        if not isinstance(fields, dict):
            continue
        section_label = INTAKE_SECTION_LABELS.get(section_key, section_key.replace("_", " ").title())
        lines.append(f"## {section_label}")
        for field_key, value in fields.items():
            if not value:
                continue
            field_label = INTAKE_FIELD_LABELS.get(field_key, field_key.replace("_", " ").title())
            lines.append(f"- **{field_label}:** {value}")
        lines.append("")
    return "\n".join(lines).strip() or "(No intake content provided.)"


def _extract_json(text: str) -> dict | None:
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else text
    brace_match = re.search(r"\{.*\}", candidate, re.DOTALL)
    if not brace_match:
        return None
    try:
        return json.loads(brace_match.group(0))
    except json.JSONDecodeError:
        return None


def draft_intake_care_plan(intake: dict) -> dict:
    """Map a structured intake into care-plan sections and a short summary.

    Returns a dict with `sections` (the six care-plan section keys → strings) and
    `intake_summary` (one short paragraph). On parse failure, sections is empty
    and intake_summary holds the raw Claude output so the client still renders.
    """
    intake_block = _flatten_intake(intake)
    section_list = ", ".join(CARE_PLAN_SECTION_KEYS)

    prompt = f"""You will draft a care plan from a practitioner's intake responses.

Return ONLY a JSON object — no prose, no markdown fences — with these exact keys:
- "situation": string (markdown allowed) — the current care situation, living arrangement, and key context.
- "goals": string — short-term and long-term care goals.
- "interventions": string — specific interventions, services, and supports.
- "family_role": string — family members involved, their roles, and communication preferences.
- "barriers": string — known barriers to care, risk factors, and mitigation strategies.
- "next_steps": string — concrete action items and who is responsible.
- "intake_summary": string — one short paragraph (3-5 sentences) synthesizing the case for the practitioner.

All section keys must be present even if a section is brief. Use the practitioner's own wording where helpful, expand where the intake is sparse, and flag uncertainty rather than inventing clinical facts.

Intake responses:
{intake_block}

JSON object with keys [{section_list}, intake_summary]:"""

    raw = complete(prompt, model="claude-sonnet-4-6", max_tokens=2048)
    parsed = _extract_json(raw)

    if not parsed or not isinstance(parsed, dict):
        return {
            "sections": {key: "" for key in CARE_PLAN_SECTION_KEYS},
            "intake_summary": raw.strip(),
        }

    sections = {key: str(parsed.get(key, "") or "") for key in CARE_PLAN_SECTION_KEYS}
    summary = str(parsed.get("intake_summary", "") or "").strip()
    return {"sections": sections, "intake_summary": summary}
