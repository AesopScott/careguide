import anthropic
import os

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
