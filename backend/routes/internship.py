from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import Client

from auth.dependencies import get_current_user
from dependencies import get_supabase_user_client
from models import User


class InternData(BaseModel):
    company_name: str
    role: str
    description: str
    duration: str


router = APIRouter(prefix="/internship", tags=["Internship"])


@router.get("/")
def get_internship_data(
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    result = supabase.table("internship").select("*").eq("user_uuid", current_user.user_uuid).execute()
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return {"internship": result.data or []}


@router.get("/{internship_id}")
def get_internship(
    internship_id: int,
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    result = (
        supabase.table("internship")
        .select("*")
        .eq("id", internship_id)
        .eq("user_uuid", current_user.user_uuid)
        .maybe_single()
        .execute()
    )
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    if not result.data:
        raise HTTPException(status_code=404, detail="Internship not found for the given id")
    return result.data


@router.post("/add-internship")
def add_internship(
    internship: InternData,
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    payload = {
        "company_name": internship.company_name,
        "role": internship.role,
        "description": internship.description,
        "duration": internship.duration,
        "user_uuid": current_user.user_uuid,
    }
    result = supabase.table("internship").insert(payload).execute()
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return {"message": f"Internship: {internship.company_name} have been added successfully"}


@router.put("/edit-internship/{internship_id}")
def edit_internship(
    internship: InternData,
    internship_id: int,
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    payload = {
        "company_name": internship.company_name,
        "role": internship.role,
        "description": internship.description,
        "duration": internship.duration,
    }
    result = (
        supabase.table("internship")
        .update(payload)
        .eq("id", internship_id)
        .eq("user_uuid", current_user.user_uuid)
        .execute()
    )
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return {"message": f"Internship:{internship.company_name} has been updated successfully"}


@router.delete("/delete-internship/{internship_id}")
def delete_internship(
    internship_id: int,
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    result = (
        supabase.table("internship")
        .delete()
        .eq("id", internship_id)
        .eq("user_uuid", current_user.user_uuid)
        .execute()
    )
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return {"message": f"Internship:{internship_id} have been deleted successfully"}

