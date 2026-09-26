from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import Client

from auth.dependencies import get_current_user
from dependencies import get_supabase_user_client
from models import User


class Project(BaseModel):
    name: str
    description: str
    tech_stack: str
    github_url: str
    live_link: str


router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/")
def get_all_projects(
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    result = supabase.table("projects").select("*").eq("user_uuid", current_user.user_uuid).execute()
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return {"projects": result.data or []}


@router.get("/{project_id}")
def get_project(
    project_id: int,
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    result = (
        supabase.table("projects")
        .select("*")
        .eq("id", project_id)
        .eq("user_uuid", current_user.user_uuid)
        .maybe_single()
        .execute()
    )
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    if not result.data:
        raise HTTPException(status_code=404, detail="Project not found for the given id")
    return result.data


@router.post("/add-project")
def add_project(
    project: Project,
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    payload = {
        "name": project.name,
        "description": project.description,
        "tech_stack": project.tech_stack,
        "github_url": project.github_url,
        "live_link": project.live_link,
        "user_uuid": current_user.user_uuid,
    }
    result = supabase.table("projects").insert(payload).execute()
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return {"message": f"Project: {project.name} have been added successfully"}


@router.put("/edit-project/{project_id}")
def edit_project(
    project: Project,
    project_id: int,
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    payload = {
        "name": project.name,
        "description": project.description,
        "tech_stack": project.tech_stack,
        "github_url": project.github_url,
        "live_link": project.live_link,
    }
    result = (
        supabase.table("projects")
        .update(payload)
        .eq("id", project_id)
        .eq("user_uuid", current_user.user_uuid)
        .execute()
    )
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return {"message": f"Project: {project.name} has been updated successfully"}


@router.delete("/delete-project/{project_id}")
def delete_project(
    project_id: int,
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    result = (
        supabase.table("projects")
        .delete()
        .eq("id", project_id)
        .eq("user_uuid", current_user.user_uuid)
        .execute()
    )
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return {"message": f"Project:{project_id} has been deleted successfully"}

