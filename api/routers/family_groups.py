from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from middleware.auth import require_practitioner
from services.firebase import get_db

router = APIRouter()


class FamilyGroupCreate(BaseModel):
    name: str
    care_level: str = ""


class InviteRequest(BaseModel):
    email: str
    family_name: str = ""


@router.get("/")
def list_family_groups(user=Depends(require_practitioner)):
    """List family groups owned by the calling practitioner."""
    db = get_db()
    groups = db.collection("family_groups") \
               .where("practitioner_id", "==", user["uid"]) \
               .stream()
    return [{"id": g.id, **g.to_dict()} for g in groups]


@router.post("/")
def create_family_group(body: FamilyGroupCreate, user=Depends(require_practitioner)):
    """Create a new family group owned by the calling practitioner."""
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    data = {
        "name":            body.name,
        "practitioner_id": user["uid"],
        "care_level":      body.care_level,
        "status":          "active",
        "urgent_flags":    [],
        "created_at":      now,
        "updated_at":      now,
    }
    doc_ref = db.collection("family_groups").document()
    doc_ref.set(data)
    return {"id": doc_ref.id, **data}


@router.get("/{group_id}")
def get_family_group(group_id: str, user=Depends(require_practitioner)):
    """Get a single family group the caller owns."""
    db = get_db()
    snap = db.collection("family_groups").document(group_id).get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="Family group not found")
    data = snap.to_dict()
    if data.get("practitioner_id") != user["uid"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return {"id": snap.id, **data}


@router.post("/{group_id}/invite")
def invite_family_member(group_id: str, body: InviteRequest, user=Depends(require_practitioner)):
    """
    Send a family-member invite. Currently a stub — the full invite-acceptance
    flow (signup page, family + family_group_id claim setter) is not yet
    implemented. Returns 501 so callers don't silently assume success.

    When the family flow is built, this endpoint should:
      1. Verify the caller owns the family_group.
      2. Generate a one-time invite token, store in `family_invitations` with
         family_group_id and an expiry.
      3. Send an email via Brevo with a link to /accept-invite.html?token=...
      4. The accept page creates the Firebase Auth user and calls
         /auth/accept-invite, which sets {family: True, family_group_id: ...}
         claims and deletes the token.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Family-member invite flow is not yet implemented.",
    )
