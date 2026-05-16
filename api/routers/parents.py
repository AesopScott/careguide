from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from firebase_admin import firestore

from middleware.auth import require_practitioner
from services.firebase import get_db

router = APIRouter()


class ParentCreate(BaseModel):
    family_group_id: str
    first_name: str
    last_name: str
    care_level: str = ""
    dob: Optional[str] = None
    state: Optional[str] = None
    invite_email: Optional[str] = None


class ParentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    care_level: Optional[str] = None
    dob: Optional[str] = None
    state: Optional[str] = None
    invite_email: Optional[str] = None


def _assert_owns_group(db, group_id: str, uid: str) -> None:
    snap = db.collection("family_groups").document(group_id).get()
    if not snap.exists or snap.to_dict().get("practitioner_id") != uid:
        raise HTTPException(status_code=403, detail="Access denied")


@router.post("/")
def create_parent(body: ParentCreate, user=Depends(require_practitioner)):
    db = get_db()
    _assert_owns_group(db, body.family_group_id, user["uid"])

    data: dict = {
        "family_group_id": body.family_group_id,
        "practitioner_id": user["uid"],
        "first_name":      body.first_name,
        "last_name":       body.last_name,
        "care_level":      body.care_level,
        "created_at":      firestore.SERVER_TIMESTAMP,
        "updated_at":      firestore.SERVER_TIMESTAMP,
    }
    if body.dob:          data["dob"]          = body.dob
    if body.state:        data["state"]        = body.state
    if body.invite_email: data["invite_email"] = body.invite_email

    doc_ref = db.collection("parents").document()
    doc_ref.set(data)
    return {"id": doc_ref.id, **data}


@router.get("/")
def list_parents(
    family_group_id: str = Query(..., description="Family group id to filter parents by"),
    user=Depends(require_practitioner),
):
    db = get_db()
    _assert_owns_group(db, family_group_id, user["uid"])
    parents = db.collection("parents") \
                .where("family_group_id", "==", family_group_id) \
                .stream()
    return [{"id": p.id, **p.to_dict()} for p in parents]


@router.get("/{parent_id}")
def get_parent(parent_id: str, user=Depends(require_practitioner)):
    db = get_db()
    snap = db.collection("parents").document(parent_id).get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="Parent not found")
    data = snap.to_dict()
    _assert_owns_group(db, data.get("family_group_id", ""), user["uid"])
    return {"id": snap.id, **data}


@router.patch("/{parent_id}")
def update_parent(parent_id: str, body: ParentUpdate, user=Depends(require_practitioner)):
    db = get_db()
    doc_ref = db.collection("parents").document(parent_id)
    snap = doc_ref.get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="Parent not found")
    _assert_owns_group(db, snap.to_dict().get("family_group_id", ""), user["uid"])

    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    updates["updated_at"] = firestore.SERVER_TIMESTAMP

    doc_ref.update(updates)
    return {"id": parent_id, **updates}


@router.delete("/{parent_id}")
def delete_parent(parent_id: str, user=Depends(require_practitioner)):
    db = get_db()
    doc_ref = db.collection("parents").document(parent_id)
    snap = doc_ref.get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="Parent not found")
    _assert_owns_group(db, snap.to_dict().get("family_group_id", ""), user["uid"])

    doc_ref.delete()
    return {"id": parent_id, "deleted": True}
