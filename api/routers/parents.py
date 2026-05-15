from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from middleware.auth import require_practitioner
from services.firebase import get_db

router = APIRouter()

class ParentCreate(BaseModel):
    family_group_id: str
    name: str
    dob: str
    care_level: str = ""

@router.post("/")
def create_parent(body: ParentCreate, user=Depends(require_practitioner)):
    db = get_db()
    group_ref = db.collection("familyGroups").document(body.family_group_id).get()
    if not group_ref.exists or group_ref.to_dict().get("practitioner_id") != user["uid"]:
        raise HTTPException(status_code=403, detail="Access denied")
    doc_ref = db.collection("familyGroups").document(body.family_group_id) \
                .collection("parents").document()
    data = {"name": body.name, "dob": body.dob, "care_level": body.care_level}
    doc_ref.set(data)
    return {"id": doc_ref.id, **data}

@router.get("/{group_id}")
def list_parents(group_id: str, user=Depends(require_practitioner)):
    db = get_db()
    group_ref = db.collection("familyGroups").document(group_id).get()
    if not group_ref.exists or group_ref.to_dict().get("practitioner_id") != user["uid"]:
        raise HTTPException(status_code=403, detail="Access denied")
    parents = db.collection("familyGroups").document(group_id).collection("parents").stream()
    return [{"id": p.id, **p.to_dict()} for p in parents]
