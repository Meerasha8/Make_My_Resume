from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import Client

from auth.dependencies import get_current_user
from dependencies import get_supabase_user_client
from models import User


class UserDetailsPayload(BaseModel):
    name: str | None = None
    mobile_number: str | None = None
    email_id: str | None = None
    github_url: str | None = None
    linkedin_url: str | None = None
    portfolio_link: str | None = None
    location: str | None = None
    profession_summary: str | None = None


router = APIRouter(prefix="/user-details", tags=["User Details"])


@router.get("/")
def get_user_details(
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    result = (
        supabase.table("user_details")
        .select("*")
        .eq("user_uuid", current_user.user_uuid)
        .maybe_single()
        .execute()
    )
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return result.data or {}


@router.post("/upsert")
def upsert_user_details(
    payload: UserDetailsPayload,
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    data = {key: value for key, value in payload.model_dump().items() if value is not None}
    data["user_uuid"] = current_user.user_uuid

    result = supabase.table("user_details").upsert(data, on_conflict="user_uuid").execute()
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return {"message": "user details saved successfully", "data": result.data}


@router.put("/")
def update_user_details(
    payload: UserDetailsPayload,
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    data = {key: value for key, value in payload.model_dump().items() if value is not None}
    result = (
        supabase.table("user_details")
        .update(data)
        .eq("user_uuid", current_user.user_uuid)
        .execute()
    )
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return {"message": "user details updated successfully", "data": result.data}


@router.delete("/")
def delete_user_details(
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    result = (
        supabase.table("user_details")
        .delete()
        .eq("user_uuid", current_user.user_uuid)
        .execute()
    )
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return {"message": "user details deleted successfully"}
