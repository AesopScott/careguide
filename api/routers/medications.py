from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Literal, Optional
from firebase_admin import firestore

from middleware.auth import require_practitioner
from services.firebase import get_db

router = APIRouter()

MedStatus = Literal["active", "inactive"]


class MedicationCreate(BaseModel):
    family_group_id: str
    name: str
    dosage:     Optional[str] = None
    frequency:  Optional[str] = None
    prescriber: Optional[str] = None
    start_date: Optional[str] = None
    status:     MedStatus = "active"
    notes:      Optional[str] = None


class MedicationUpdate(BaseModel):
    name:       Optional[str] = None
    dosage:     Optional[str] = None
    frequency:  Optional[str] = None
    prescriber: Optional[str] = None
    start_date: Optional[str] = None
    status:     Optional[MedStatus] = None
    notes:      Optional[str] = None


def _assert_owns_group(db, group_id: str, uid: str) -> None:
    snap = db.collection("family_groups").document(group_id).get()
    if not snap.exists or snap.to_dict().get("practitioner_id") != uid:
        raise HTTPException(status_code=403, detail="Access denied")


@router.post("/")
def create_medication(body: MedicationCreate, user=Depends(require_practitioner)):
    db = get_db()
    _assert_owns_group(db, body.family_group_id, user["uid"])

    data: dict = {
        "family_group_id": body.family_group_id,
        "practitioner_id": user["uid"],
        "name":            body.name,
        "dosage":          body.dosage,
        "frequency":       body.frequency,
        "prescriber":      body.prescriber,
        "start_date":      body.start_date,
        "status":          body.status,
        "notes":           body.notes,
        "created_at":      firestore.SERVER_TIMESTAMP,
        "updated_at":      firestore.SERVER_TIMESTAMP,
    }

    doc_ref = db.collection("medications").document()
    doc_ref.set(data)
    return {"id": doc_ref.id, **data}


@router.get("/")
def list_medications(
    family_group_id: str = Query(..., description="Family group id to filter medications by"),
    user=Depends(require_practitioner),
):
    db = get_db()
    _assert_owns_group(db, family_group_id, user["uid"])
    meds = db.collection("medications") \
             .where("family_group_id", "==", family_group_id) \
             .order_by("created_at", direction=firestore.Query.DESCENDING) \
             .stream()
    return [{"id": m.id, **m.to_dict()} for m in meds]


@router.get("/{med_id}")
def get_medication(med_id: str, user=Depends(require_practitioner)):
    db = get_db()
    snap = db.collection("medications").document(med_id).get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="Medication not found")
    data = snap.to_dict()
    _assert_owns_group(db, data.get("family_group_id", ""), user["uid"])
    return {"id": snap.id, **data}


@router.patch("/{med_id}")
def update_medication(med_id: str, body: MedicationUpdate, user=Depends(require_practitioner)):
    db = get_db()
    doc_ref = db.collection("medications").document(med_id)
    snap = doc_ref.get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="Medication not found")
    _assert_owns_group(db, snap.to_dict().get("family_group_id", ""), user["uid"])

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    updates["updated_at"] = firestore.SERVER_TIMESTAMP

    doc_ref.update(updates)
    return {"id": med_id, **updates}


@router.delete("/{med_id}")
def delete_medication(med_id: str, user=Depends(require_practitioner)):
    db = get_db()
    doc_ref = db.collection("medications").document(med_id)
    snap = doc_ref.get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="Medication not found")
    _assert_owns_group(db, snap.to_dict().get("family_group_id", ""), user["uid"])

    doc_ref.delete()
    return {"id": med_id, "deleted": True}
