from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from middleware.auth import require_practitioner
from services.firebase import get_db

router = APIRouter()

class FamilyGroupCreate(BaseModel):
    name: str
    members: list[str] = []

@router.get("/")
def list_family_groups(user=Depends(require_practitioner)):
    db = get_db()
    groups = db.collection("familyGroups") \
               .where("practitioner_id", "==", user["uid"]) \
               .stream()
    return [{"id": g.id, **g.to_dict()} for g in groups]

@router.post("/")
def create_family_group(body: FamilyGroupCreate, user=Depends(require_practitioner)):
    db = get_db()
    doc_ref = db.collection("familyGroups").document()
    data = {
        "name": body.name,
        "practitioner_id": user["uid"],
        "members": body.members,
    }
    doc_ref.set(data)
    return {"id": doc_ref.id, **data}

@router.get("/{group_id}")
def get_family_group(group_id: str, user=Depends(require_practitioner)):
    db = get_db()
    doc = db.collection("familyGroups").document(group_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Group not found")
    data = doc.to_dict()
    if data.get("practitioner_id") != user["uid"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return {"id": doc.id, **data}
