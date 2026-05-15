from fastapi import APIRouter, Depends
from pydantic import BaseModel
from middleware.auth import require_auth, require_practitioner
from services.claude import draft_care_plan, draft_session_note, answer_question

router = APIRouter()

class TranscriptRequest(BaseModel):
    transcript: str

class QuestionRequest(BaseModel):
    question: str
    context: str = ""

@router.post("/care-plan-draft")
def create_care_plan_draft(body: TranscriptRequest, user=Depends(require_practitioner)):
    return {"draft": draft_care_plan(body.transcript)}

@router.post("/session-note-draft")
def create_session_note_draft(body: TranscriptRequest, user=Depends(require_practitioner)):
    return {"draft": draft_session_note(body.transcript)}

@router.post("/ask")
def ask_question(body: QuestionRequest, user=Depends(require_auth)):
    return {"answer": answer_question(body.question, body.context)}
