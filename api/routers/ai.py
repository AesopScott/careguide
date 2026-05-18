from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from firebase_admin import firestore as admin_firestore
from pydantic import BaseModel
from middleware.auth import require_auth, require_practitioner
from services.claude import (
    answer_question,
    draft_care_plan,
    draft_intake_care_plan,
    draft_session_note,
)
from services.firebase import get_db

router = APIRouter()

class TranscriptRequest(BaseModel):
    transcript: str

class QuestionRequest(BaseModel):
    question: str
    context: str = ""

class IntakeRequest(BaseModel):
    family_group_id: str
    intake: Dict[str, Any]

@router.post("/care-plan-draft")
def create_care_plan_draft(body: TranscriptRequest, user=Depends(require_practitioner)):
    return {"draft": draft_care_plan(body.transcript)}

@router.post("/session-note-draft")
def create_session_note_draft(body: TranscriptRequest, user=Depends(require_practitioner)):
    return {"draft": draft_session_note(body.transcript)}

@router.post("/ask")
def ask_question(body: QuestionRequest, user=Depends(require_auth)):
    return {"answer": answer_question(body.question, body.context)}

@router.post("/intake")
def create_intake_care_plan(body: IntakeRequest, user=Depends(require_practitioner)):
    db = get_db()
    family_ref = db.collection("family_groups").document(body.family_group_id)
    family_snap = family_ref.get()
    if not family_snap.exists:
        raise HTTPException(status_code=404, detail="Family group not found")
    if family_snap.to_dict().get("practitioner_id") != user["uid"]:
        raise HTTPException(status_code=403, detail="Access denied")

    intake_ref = db.collection("intake_data").document(body.family_group_id)
    existing = intake_ref.get()
    intake_doc: Dict[str, Any] = {
        "family_group_id": body.family_group_id,
        "practitioner_id": user["uid"],
        "intake":          body.intake,
        "updated_at":      admin_firestore.SERVER_TIMESTAMP,
    }
    if not existing.exists:
        intake_doc["created_at"] = admin_firestore.SERVER_TIMESTAMP
    intake_ref.set(intake_doc, merge=True)

    result = draft_intake_care_plan(body.intake)
    return {
        "sections":       result["sections"],
        "intake_summary": result["intake_summary"],
    }
