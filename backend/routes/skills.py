from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import Client

from auth.dependencies import get_current_user
from dependencies import get_supabase_user_client
from models import User


class Skill(BaseModel):
    name: str
    description: str


router = APIRouter(prefix="/skills", tags=["Skills"])


@router.get("/")
def get_all_skills(
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    result = supabase.table("skills").select("*").eq("user_uuid", current_user.user_uuid).execute()
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return result.data or []


@router.get("/{skill_id}")
def get_skill(
    skill_id: int,
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    result = (
        supabase.table("skills")
        .select("*")
        .eq("id", skill_id)
        .eq("user_uuid", current_user.user_uuid)
        .maybe_single()
        .execute()
    )
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    if not result.data:
        raise HTTPException(status_code=404, detail="Skill not found for the given id")
    return result.data


@router.post("/add-skill")
def add_skill(
    skill: Skill,
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    payload = {"name": skill.name, "description": skill.description, "user_uuid": current_user.user_uuid}
    result = supabase.table("skills").insert(payload).execute()
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return {"Skill added successfully": result.data}


@router.put("/edit-skill/{skill_id}")
def edit_skill(
    skill_data: Skill,
    skill_id: int,
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    payload = {"name": skill_data.name, "description": skill_data.description}
    result = (
        supabase.table("skills")
        .update(payload)
        .eq("id", skill_id)
        .eq("user_uuid", current_user.user_uuid)
        .execute()
    )
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return {"Skill updated": result.data}


@router.delete("/delete-skill/{skill_id}")
def delete_skill(
    skill_id: int,
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    result = (
        supabase.table("skills")
        .delete()
        .eq("id", skill_id)
        .eq("user_uuid", current_user.user_uuid)
        .execute()
    )
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return {"Skill deleted": result.data}

