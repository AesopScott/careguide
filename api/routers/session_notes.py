from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from firebase_admin import firestore

from middleware.auth import require_practitioner
from services.firebase import get_db

router = APIRouter()


NoteType = Literal["check-in", "assessment", "care-plan", "family", "crisis", "other"]


class SessionNoteCreate(BaseModel):
    family_group_id: str
    type:            NoteType = "check-in"
    text:            str
    billable_minutes: Optional[int] = None


class SessionNoteUpdate(BaseModel):
    type:             Optional[NoteType] = None
    text:             Optional[str] = None
    billable_minutes: Optional[int] = None


def _assert_owns_group(db, group_id: str, uid: str) -> None:
    snap = db.collection("family_groups").document(group_id).get()
    if not snap.exists or snap.to_dict().get("practitioner_id") != uid:
        raise HTTPException(status_code=403, detail="Access denied")


def _assert_owns_note(db, note_id: str, uid: str) -> dict:
    snap = db.collection("session_notes").document(note_id).get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="Session note not found")
    data = snap.to_dict()
    _assert_owns_group(db, data.get("family_group_id", ""), uid)
    return data


@router.post("/")
def create_session_note(body: SessionNoteCreate, user=Depends(require_practitioner)):
    """Create a session note keyed to a family group the caller owns."""
    db = get_db()
    _assert_owns_group(db, body.family_group_id, user["uid"])

    data: dict = {
        "family_group_id":  body.family_group_id,
        "practitioner_id":  user["uid"],
        "type":             body.type,
        "text":             body.text,
        "billable_minutes": body.billable_minutes,
        "created_at":       firestore.SERVER_TIMESTAMP,
        "updated_at":       firestore.SERVER_TIMESTAMP,
    }
    doc_ref = db.collection("session_notes").document()
    doc_ref.set(data)
    return {"id": doc_ref.id, **data}


@router.get("/")
def list_session_notes(
    family_group_id: str = Query(..., description="Family group id to filter notes by"),
    user=Depends(require_practitioner),
):
    """List session notes for a family group the caller owns, newest first."""
    db = get_db()
    _assert_owns_group(db, family_group_id, user["uid"])
    notes = db.collection("session_notes") \
              .where("family_group_id", "==", family_group_id) \
              .order_by("created_at", direction=firestore.Query.DESCENDING) \
              .stream()
    return [{"id": n.id, **n.to_dict()} for n in notes]


@router.get("/{note_id}")
def get_session_note(note_id: str, user=Depends(require_practitioner)):
    db = get_db()
    data = _assert_owns_note(db, note_id, user["uid"])
    return {"id": note_id, **data}


@router.patch("/{note_id}")
def update_session_note(note_id: str, body: SessionNoteUpdate, user=Depends(require_practitioner)):
    db = get_db()
    _assert_owns_note(db, note_id, user["uid"])

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    updates["updated_at"] = firestore.SERVER_TIMESTAMP

    db.collection("session_notes").document(note_id).update(updates)
    return {"id": note_id, **updates}


@router.delete("/{note_id}")
def delete_session_note(note_id: str, user=Depends(require_practitioner)):
    db = get_db()
    _assert_owns_note(db, note_id, user["uid"])
    db.collection("session_notes").document(note_id).delete()
    return {"id": note_id, "deleted": True}
