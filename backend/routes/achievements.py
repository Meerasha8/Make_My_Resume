from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import Client

from auth.dependencies import get_current_user
from dependencies import get_supabase_user_client
from models import User


class Achievement(BaseModel):
    description: str


router = APIRouter(prefix="/achievement", tags=["Achievement"])


@router.get("/")
def get_all_achievement(
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    result = supabase.table("achievements").select("*").eq("user_uuid", current_user.user_uuid).execute()
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return {"Achievements": result.data or []}


@router.get("/get-achievement/{achievement_id}")
def get_achievement(
    achievement_id: int,
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    result = (
        supabase.table("achievements")
        .select("*")
        .eq("id", achievement_id)
        .eq("user_uuid", current_user.user_uuid)
        .maybe_single()
        .execute()
    )
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    if not result.data:
        raise HTTPException(status_code=404, detail="achievement not found for the given id")
    return result.data


@router.post("/add-achievement")
def add_achievement(
    achievement: Achievement,
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    payload = {"description": achievement.description, "user_uuid": current_user.user_uuid}
    result = supabase.table("achievements").insert(payload).execute()
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return {"message": f"new achievement added successfully {achievement.description}"}


@router.put("/edit-achievement/{achievement_id}")
def edit_achievement(
    achievement: Achievement,
    achievement_id: int,
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    payload = {"description": achievement.description}
    result = (
        supabase.table("achievements")
        .update(payload)
        .eq("id", achievement_id)
        .eq("user_uuid", current_user.user_uuid)
        .execute()
    )
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return {"message": f"achievement edited successfully {achievement.description}"}


@router.delete("/delete-achievement/{achievement_id}")
def delete_achievement(
    achievement_id: int,
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    result = (
        supabase.table("achievements")
        .delete()
        .eq("id", achievement_id)
        .eq("user_uuid", current_user.user_uuid)
        .execute()
    )
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return {"message": f"achievement deleted successfully {achievement_id}"}
