from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from middleware.auth import require_practitioner
from services.firebase import get_db

router = APIRouter()

class MedicationCreate(BaseModel):
    family_group_id: str
    parent_id: str
    name: str
    dosage: str
    frequency: str
    active: bool = True

@router.post("/")
def add_medication(body: MedicationCreate, user=Depends(require_practitioner)):
    db = get_db()
    group_ref = db.collection("familyGroups").document(body.family_group_id).get()
    if not group_ref.exists or group_ref.to_dict().get("practitioner_id") != user["uid"]:
        raise HTTPException(status_code=403, detail="Access denied")
    doc_ref = db.collection("familyGroups").document(body.family_group_id) \
                .collection("medications").document()
    data = {
        "parent_id": body.parent_id,
        "name": body.name,
        "dosage": body.dosage,
        "frequency": body.frequency,
        "active": body.active,
    }
    doc_ref.set(data)
    return {"id": doc_ref.id, **data}

@router.get("/{group_id}")
def list_medications(group_id: str, user=Depends(require_practitioner)):
    db = get_db()
    group_ref = db.collection("familyGroups").document(group_id).get()
    if not group_ref.exists or group_ref.to_dict().get("practitioner_id") != user["uid"]:
        raise HTTPException(status_code=403, detail="Access denied")
    meds = db.collection("familyGroups").document(group_id).collection("medications").stream()
    return [{"id": m.id, **m.to_dict()} for m in meds]
