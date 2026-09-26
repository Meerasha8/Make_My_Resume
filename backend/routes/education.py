from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import Client

from auth.dependencies import get_current_user
from dependencies import get_supabase_user_client
from models import User


class Education(BaseModel):
    course_name: str
    cgpa: float
    start_year: int
    end_year: int
    college_name: str
    location: str


router = APIRouter(prefix="/education", tags=["Education"])


@router.get("/")
def get_all_education(
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    result = supabase.table("education").select("*").eq("user_uuid", current_user.user_uuid).execute()
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return {"Educations": result.data or []}


@router.get("/get-education/{education_id}")
def get_education(
    education_id: int,
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    result = (
        supabase.table("education")
        .select("*")
        .eq("id", education_id)
        .eq("user_uuid", current_user.user_uuid)
        .maybe_single()
        .execute()
    )
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    if not result.data:
        raise HTTPException(status_code=404, detail="Education not found for the given id")
    return result.data


@router.post("/add-education")
def add_education(
    education: Education,
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    payload = {
        "course_name": education.course_name,
        "cgpa": education.cgpa,
        "start_year": education.start_year,
        "end_year": education.end_year,
        "college_name": education.college_name,
        "location": education.location,
        "user_uuid": current_user.user_uuid,
    }
    result = supabase.table("education").insert(payload).execute()
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return {"message": f"new education added successfully {education.course_name}"}


@router.put("/edit-education/{education_id}")
def edit_education(
    education: Education,
    education_id: int,
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    payload = {
        "course_name": education.course_name,
        "cgpa": education.cgpa,
        "start_year": education.start_year,
        "end_year": education.end_year,
        "college_name": education.college_name,
        "location": education.location,
    }
    result = (
        supabase.table("education")
        .update(payload)
        .eq("id", education_id)
        .eq("user_uuid", current_user.user_uuid)
        .execute()
    )
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return {"message": f"education edited successfully {education.course_name}"}


@router.delete("/delete-education/{education_id}")
def delete_education(
    education_id: int,
    supabase: Client = Depends(get_supabase_user_client),
    current_user: User = Depends(get_current_user),
):
    result = (
        supabase.table("education")
        .delete()
        .eq("id", education_id)
        .eq("user_uuid", current_user.user_uuid)
        .execute()
    )
    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))
    return {"message": f"education deleted successfully {education_id}"}
