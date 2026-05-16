from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from middleware.auth import require_practitioner
from services.firebase import get_db

router = APIRouter()


class MedicationCreate(BaseModel):
    family_group_id: str
    parent_id: str | None = None
    name: str
    dosage: str = ""
    frequency: str = ""
    active: bool = True


def _verify_group_ownership(db, group_id: str, uid: str):
    """Confirm the family_group exists and is owned by the calling practitioner."""
    group_snap = db.collection("family_groups").document(group_id).get()
    if not group_snap.exists:
        raise HTTPException(status_code=404, detail="Family group not found")
    if group_snap.to_dict().get("practitioner_id") != uid:
        raise HTTPException(status_code=403, detail="Access denied")


@router.post("/")
def add_medication(body: MedicationCreate, user=Depends(require_practitioner)):
    """Create a top-level medication record linked by family_group_id."""
    db = get_db()
    _verify_group_ownership(db, body.family_group_id, user["uid"])

    now = datetime.now(timezone.utc).isoformat()
    data = {
        "family_group_id": body.family_group_id,
        "parent_id":       body.parent_id,
        "name":            body.name,
        "dosage":          body.dosage,
        "frequency":       body.frequency,
        "active":          body.active,
        "created_at":      now,
        "updated_at":      now,
    }
    doc_ref = db.collection("medications").document()
    doc_ref.set(data)
    return {"id": doc_ref.id, **data}


@router.get("/{group_id}")
def list_medications(group_id: str, user=Depends(require_practitioner)):
    """List medications for a family group the caller owns, newest first."""
    db = get_db()
    _verify_group_ownership(db, group_id, user["uid"])

    meds = db.collection("medications") \
             .where("family_group_id", "==", group_id) \
             .order_by("created_at", direction="DESCENDING") \
             .stream()
    return [{"id": m.id, **m.to_dict()} for m in meds]
