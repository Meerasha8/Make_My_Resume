import json
import re
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from dependencies import get_db
from models import (
    Achievements,
    Certificates,
    Educations,
    Internship,
    Projects,
    ResumeHistory,
    Skills,
    User,
    UserDetails,
    _uuid_value,
)
from resume_service import ResumeContent, ResumeService, group_skills

router = APIRouter(prefix="/resume", tags=["Resume"])


class ResumeRequest(BaseModel):
    job_description: str
    template_style: str | None = "ats"


class ResumeJobResponse(BaseModel):
    job_id: str
    status: str
    message: str


class ResumeGenerationStatusResponse(BaseModel):
    job_id: str
    status: str
    download_url: str | None = None
    error: str | None = None


class ResumeHistoryItem(BaseModel):
    id: int
    job_id: str
    status: str
    job_description: str
    template_style: str | None = "ats"
    created_at: datetime | None = None
    download_url: str | None = None


class ResumeHistoryListResponse(BaseModel):
    items: list[ResumeHistoryItem]
    limit: int
    offset: int


def _stored_content(job: ResumeHistory) -> ResumeContent:
    """Read resume_content back as a ResumeContent.

    The Supabase column is `text`, not `jsonb`, so the saved JSON comes back as a string. Resumes made before the fixed
    skill categories stored skills as a flat list of names; those are regrouped so old resumes still download.
    """
    raw = job.resume_content
    if isinstance(raw, str):
        raw = json.loads(raw) if raw.strip() else {}
    raw = dict(raw or {})
    skills = raw.get("skills") or []
    if skills and all(isinstance(skill, str) for skill in skills):
        raw["skills"] = [group.model_dump() for group in group_skills([(skill, None) for skill in skills])]
    return ResumeContent.model_validate(raw)


def _collect_user_resume_data(db: Session, user_uuid: str) -> dict[str, Any]:
    user_details = db.query(UserDetails).filter(UserDetails.user_uuid == user_uuid).first()
    education = db.query(Educations).filter(Educations.user_uuid == user_uuid).all()
    certificates = db.query(Certificates).filter(Certificates.user_uuid == user_uuid).all()
    internship = db.query(Internship).filter(Internship.user_uuid == user_uuid).all()
    achievements = db.query(Achievements).filter(Achievements.user_uuid == user_uuid).all()
    projects = db.query(Projects).filter(Projects.user_uuid == user_uuid).all()
    skills = db.query(Skills).filter(Skills.user_uuid == user_uuid).all()

    return {
        "user_details": {
            "name": user_details.name if user_details else None,
            "email": user_details.email_id if user_details else None,
            "phone": user_details.mobile_number if user_details else None,
            "github": user_details.github_url if user_details else None,
            "linkedin": user_details.linkedin_url if user_details else None,
            "portfolio": user_details.portfolio_link if user_details else None,
            "location": user_details.location if user_details else None,
            "profession_summary": user_details.profession_summary if user_details else None,
        },
        "education": [
            {
                "course_name": item.course_name,
                "college_name": item.college_name,
                "location": item.location,
                "start_year": item.start_year,
                "end_year": item.end_year,
                "cgpa": item.cgpa,
            }
            for item in education
        ],
        "certificates": [
            {"certificate_name": item.certificate_name, "certificate_issuer": item.certificate_issuer}
            for item in certificates
        ],
        "internship": [
            {
                "role": item.role,
                "company_name": item.company_name,
                "description": item.description,
                "duration": getattr(item, "Duration", getattr(item, "duration", "")),
            }
            for item in internship
        ],
        "achievements": [{"description": item.description} for item in achievements],
        "projects": [
            {
                "name": item.name,
                "description": item.description,
                "tech_stack": item.tech_stack,
                "github_url": item.github_url,
                "live_link": item.live_link,
            }
            for item in projects
        ],
        "skills": [{"name": item.name, "description": item.description} for item in skills],
    }


@router.post("/generate", response_model=ResumeJobResponse)
def generate_resume_job(
    payload: ResumeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_uuid = current_user.user_uuid
    job_id = uuid.uuid4()
    template = payload.template_style or "ats"

    job_record = ResumeHistory(
        job_id=_uuid_value(job_id),
        user_uuid=_uuid_value(user_uuid),
        job_description=payload.job_description,
        status="queued",
        template_style=template,
    )
    db.add(job_record)
    db.commit()
    db.refresh(job_record)

    try:
        user_data = _collect_user_resume_data(db, user_uuid)
        service = ResumeService()
        content = service.select_resume_content(payload.job_description, user_data)
        service.render_docx(content, user_data.get("user_details"))  # fail the job now if rendering would fail
        job_record.status = "completed"
        job_record.download_url = f"/resume/generate/{job_id}/download"
        job_record.resume_content = content.model_dump()
        job_record.error = None
    except Exception as exc:
        job_record.status = "failed"
        job_record.error = str(exc)
        job_record.download_url = None

    db.commit()
    db.refresh(job_record)

    return ResumeJobResponse(
        job_id=str(job_id),
        status=job_record.status,
        message="Resume generation completed" if job_record.status == "completed" else "Resume generation failed",
    )


@router.get("/generate/{job_id}/preview")
def resume_job_preview(
    job_id: str,
    db: Session = Depends(get_db),
):
    job = db.query(ResumeHistory).filter(ResumeHistory.job_id == _uuid_value(job_id)).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    user_data = _collect_user_resume_data(db, job.user_uuid)
    try:
        content = _stored_content(job).model_dump() if job.resume_content else None
    except (ValueError, ValidationError):
        content = None
    if not content:
        service = ResumeService()
        content = service.select_resume_content(job.job_description, user_data).model_dump()

    return {
        "job_id": str(job.job_id),
        "status": job.status,
        "template_style": getattr(job, "template_style", "ats") or "ats",
        "job_description": job.job_description,
        "user_details": user_data.get("user_details", {}),
        "content": content,
    }


@router.get("/generate/{job_id}", response_model=ResumeGenerationStatusResponse)
def resume_job_status(
    job_id: str,
    db: Session = Depends(get_db),
):
    job = db.query(ResumeHistory).filter(ResumeHistory.job_id == _uuid_value(job_id)).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return ResumeGenerationStatusResponse(
        job_id=str(job.job_id),
        status=job.status,
        download_url=job.download_url if job.status == "completed" else None,
        error=job.error,
    )


@router.get("/generate/{job_id}/download")
@router.post("/generate/{job_id}/download")
def resume_job_download(
    job_id: str,
    db: Session = Depends(get_db),
):
    job = (
        db.query(ResumeHistory)
        .filter(ResumeHistory.job_id == _uuid_value(job_id))
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "completed":
        raise HTTPException(status_code=409, detail="Resume generation is not complete yet")

    # The DOCX is rebuilt from the stored content instead of being kept on disk, because hosts like Render
    # wipe the filesystem on every restart/redeploy.
    try:
        content = _stored_content(job)
    except (ValueError, ValidationError):  # json.JSONDecodeError is a ValueError
        raise HTTPException(status_code=410, detail="This resume was made by an older version of the app. Please generate it again.")
    user_details = _collect_user_resume_data(db, job.user_uuid)["user_details"]
    doc_bytes = ResumeService().render_docx(content, user_details)

    filename = re.sub(r"[^A-Za-z0-9]+", "_", user_details.get("name") or "Resume").strip("_") or "Resume"
    return Response(
        content=doc_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}_Resume.docx"'},
    )


@router.get(
    "/history",
    response_model=ResumeHistoryListResponse,
    summary="List the authenticated user's resume generation history",
    description="Return a paginated list of resume generation jobs for the authenticated user.",
)
def resume_history(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_uuid = _uuid_value(current_user.user_uuid)
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    rows = (
        db.query(ResumeHistory)
        .filter(ResumeHistory.user_uuid == user_uuid)
        .order_by(ResumeHistory.created_at.desc(), ResumeHistory.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    items = []
    for row in rows:
        description = row.job_description
        if len(description) > 100:
            description = description[:97] + "..."
        items.append(
            ResumeHistoryItem(
                id=row.id,
                job_id=str(row.job_id),
                status=row.status,
                job_description=description,
                template_style=getattr(row, "template_style", "ats") or "ats",
                created_at=row.created_at,
                download_url=row.download_url if row.status == "completed" else None,
            )
        )

    return ResumeHistoryListResponse(items=items, limit=limit, offset=offset)


@router.delete(
    "/history/{history_id}",
    summary="Delete a single resume generation history item",
)
def delete_resume_history_item(
    history_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_uuid = _uuid_value(current_user.user_uuid)
    query = db.query(ResumeHistory).filter(ResumeHistory.user_uuid == user_uuid)
    normalized_id = str(history_id).strip()

    job = None
    if normalized_id.isdigit():
        job = query.filter(ResumeHistory.id == int(normalized_id)).first()

    if not job:
        try:
            job = query.filter(ResumeHistory.job_id == _uuid_value(normalized_id)).first()
        except Exception:
            pass

    if not job:
        try:
            job = query.filter(ResumeHistory.job_id == normalized_id).first()
        except Exception:
            pass

    if not job:
        raise HTTPException(status_code=404, detail="Resume history item not found")

    db.delete(job)
    db.commit()
    return {"message": f"Resume history item {history_id} deleted successfully"}


@router.delete(
    "/history",
    summary="Clear all resume generation history for authenticated user",
)
def clear_resume_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_uuid = _uuid_value(current_user.user_uuid)
    jobs = db.query(ResumeHistory).filter(ResumeHistory.user_uuid == user_uuid).all()
    for job in jobs:
        db.delete(job)
    db.commit()
    return {"message": "All resume history cleared successfully"}
