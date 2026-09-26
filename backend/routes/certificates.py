from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import Client

from auth.dependencies import get_current_user
from dependencies import get_supabase_user_client
from models import User


class Certificate(BaseModel):
    certificate_issuer: str
    certificate_name: str


router = APIRouter(prefix="/certificates", tags=["Certificates"])


@router.get("/")
def get_all_certificates(
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    result = supabase.table("certificates").select("*").eq("user_uuid", current_user.user_uuid).execute()
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return {"certificates": result.data or []}


@router.get("/get-certificate/{certificate_id}")
def get_certificate(
    certificate_id: int,
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    result = (
        supabase.table("certificates")
        .select("*")
        .eq("id", certificate_id)
        .eq("user_uuid", current_user.user_uuid)
        .maybe_single()
        .execute()
    )
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    if not result.data:
        raise HTTPException(status_code=404, detail="Certificate not found for the given id")
    return result.data


@router.post("/add-certificate")
def add_certificate(
    certificate: Certificate,
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    payload = {
        "certificate_issuer": certificate.certificate_issuer,
        "certificate_name": certificate.certificate_name,
        "user_uuid": current_user.user_uuid,
    }
    result = supabase.table("certificates").insert(payload).execute()
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return {"Certificate added successfully": result.data}


@router.put("/edit-certificate/{certificate_id}")
def edit_certificate(
    certificate: Certificate,
    certificate_id: int,
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    payload = {
        "certificate_issuer": certificate.certificate_issuer,
        "certificate_name": certificate.certificate_name,
    }
    result = (
        supabase.table("certificates")
        .update(payload)
        .eq("id", certificate_id)
        .eq("user_uuid", current_user.user_uuid)
        .execute()
    )
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return {"Certificate updated": result.data}


@router.delete("/delete-certificate/{certificate_id}")
def delete_certificate(
    certificate_id: int,
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    result = (
        supabase.table("certificates")
        .delete()
        .eq("id", certificate_id)
        .eq("user_uuid", current_user.user_uuid)
        .execute()
    )
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return {"Certificate deleted": result.data}
