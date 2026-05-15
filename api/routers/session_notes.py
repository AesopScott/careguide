from fastapi import APIRouter, Depends
from pydantic import BaseModel
from middleware.auth import require_practitioner
from services.firebase import get_db
from services.claude import draft_session_note

router = APIRouter()

class SessionNoteCreate(BaseModel):
    transcript: str
    billable_minutes: int = 0

@router.post("/")
def create_session_note(body: SessionNoteCreate, user=Depends(require_practitioner)):
    db = get_db()
    ai_summary = draft_session_note(body.transcript)
    doc_ref = db.collection("practitioners").document(user["uid"]) \
                .collection("sessionNotes").document()
    data = {
        "transcript": body.transcript,
        "ai_summary": ai_summary,
        "billable_minutes": body.billable_minutes,
        "practitioner_id": user["uid"],
    }
    doc_ref.set(data)
    return {"id": doc_ref.id, **data}

@router.get("/")
def list_session_notes(user=Depends(require_practitioner)):
    db = get_db()
    notes = db.collection("practitioners").document(user["uid"]) \
               .collection("sessionNotes").stream()
    return [{"id": n.id, **n.to_dict()} for n in notes]
