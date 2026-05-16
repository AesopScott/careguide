from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from middleware.auth import require_practitioner
from services.firebase import get_db

router = APIRouter()


class ParentCreate(BaseModel):
    family_group_id: str
    first_name: str
    last_name: str = ""
    dob: str = ""
    state: str = ""
    care_level: str = ""
    invite_email: str | None = None


def _verify_group_ownership(db, group_id: str, uid: str):
    """Confirm the family_group exists and is owned by the calling practitioner."""
    group_snap = db.collection("family_groups").document(group_id).get()
    if not group_snap.exists:
        raise HTTPException(status_code=404, detail="Family group not found")
    if group_snap.to_dict().get("practitioner_id") != uid:
        raise HTTPException(status_code=403, detail="Access denied")


@router.post("/")
def create_parent(body: ParentCreate, user=Depends(require_practitioner)):
    """Create a top-level parent record linked by family_group_id."""
    db = get_db()
    _verify_group_ownership(db, body.family_group_id, user["uid"])

    now = datetime.now(timezone.utc).isoformat()
    data = {
        "family_group_id": body.family_group_id,
        "practitioner_id": user["uid"],
        "first_name":      body.first_name,
        "last_name":       body.last_name,
        "dob":             body.dob,
        "state":           body.state,
        "care_level":      body.care_level,
        "invite_email":    body.invite_email,
        "created_at":      now,
        "updated_at":      now,
    }
    doc_ref = db.collection("parents").document()
    doc_ref.set(data)
    return {"id": doc_ref.id, **data}


@router.get("/{group_id}")
def list_parents(group_id: str, user=Depends(require_practitioner)):
    """List parents for a family group the caller owns."""
    db = get_db()
    _verify_group_ownership(db, group_id, user["uid"])

    parents = db.collection("parents") \
                .where("family_group_id", "==", group_id) \
                .stream()
    return [{"id": p.id, **p.to_dict()} for p in parents]
