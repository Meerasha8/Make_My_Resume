from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from dependencies import get_db
from embedding_utils import relevance_scores
from llm import chat_completion
from models import (
    Achievements,
    Certificates,
    ChatHistory,
    DocumentEmbedding,
    Educations,
    Internship,
    Projects,
    Skills,
    User,
    UserDetails,
    _uuid_value,
)


class AskRequest(BaseModel):
    question: str


class SourceReference(BaseModel):
    source_table: str
    source_id: int


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceReference]


class ChatHistoryItem(BaseModel):
    id: int
    question: str
    answer: str
    sources: list[SourceReference] | None = None
    created_at: datetime | None = None


class ChatHistoryListResponse(BaseModel):
    items: list[ChatHistoryItem]
    limit: int
    offset: int


router = APIRouter(prefix="/ai", tags=["AI Service"])


def _iter_structured_profile_rows(db: Session, user_uuid: str):
    tables = [
        ("projects", Projects),
        ("skills", Skills),
        ("education", Educations),
        ("internship", Internship),
        ("achievements", Achievements),
        ("certificates", Certificates),
        ("user_details", UserDetails),
    ]

    for source_table, model in tables:
        rows = db.query(model).filter(model.user_uuid == user_uuid).all()
        for row in rows:
            yield source_table, row


def _describe(kind: str, *fields: tuple[str, object]) -> str:
    # Skip empty fields so the retriever and the LLM never see "GitHub: None".
    parts = [f"{label}: {value}" for label, value in fields if value not in (None, "")]
    return f"{kind}. " + ". ".join(parts) + "."


def _structured_profile_context(db: Session, user_uuid: str) -> list[tuple[str, int, str]]:
    chunks: list[tuple[str, int, str]] = []
    for source_table, row in _iter_structured_profile_rows(db, user_uuid):
        if source_table == "projects":
            content = _describe("Project", ("Name", row.name), ("Description", row.description), ("Tech stack", row.tech_stack),
                                ("GitHub", row.github_url), ("Live link", row.live_link))
        elif source_table == "skills":
            # Plain "Skill: X." embeds best for chat (measured); a "Name:" label made "Git" outrank GitHub contact rows.
            content = f"Skill: {row.name}." + (f" {row.description}" if row.description else "")
        elif source_table == "education":
            years = "-".join(str(year) for year in (row.start_year, row.end_year) if year)
            content = _describe("Education", ("Course", row.course_name), ("College", row.college_name), ("CGPA", row.cgpa),
                                ("Years", years), ("Location", row.location))
        elif source_table == "user_details":
            content = _describe("User details / contact information", ("Name", row.name), ("Mobile", row.mobile_number),
                                ("Email", row.email_id), ("GitHub", row.github_url), ("LinkedIn", row.linkedin_url),
                                ("Portfolio", row.portfolio_link), ("Location", row.location), ("Summary", row.profession_summary))
        elif source_table == "internship":
            content = _describe("Internship / work experience", ("Company", row.company_name), ("Role", row.role),
                                ("Description", row.description), ("Duration", row.duration))
        elif source_table == "achievements":
            content = _describe("Achievement", ("Description", row.description))
        elif source_table == "certificates":
            content = _describe("Certificate", ("Name", row.certificate_name), ("Issuer", row.certificate_issuer))
        else:
            continue
        chunks.append((source_table, row.id, content))
    return chunks


RETRIEVAL_TOP_K = 8
MAX_PER_SECTION = 4  # stops many short rows (e.g. 30 skills) from filling the whole top-k
MAX_CONTEXT_CHUNKS = 20

# Questions that name a whole section ("list my projects") get every row of it, not just the top matches.
SECTION_KEYWORDS = {
    "projects": ("project",),
    "skills": ("skill", "technolog", "tech stack"),
    "education": ("educat", "cgpa", "college", "degree", "universit"),
    "internship": ("intern", "experience", "worked at", "job"),
    "achievements": ("achiev", "award", "hackathon", "competition"),
    "certificates": ("certif",),
    "user_details": ("contact", "email", "phone", "linkedin", "github profile", "portfolio"),
}


def _retrieve_context(db: Session, user_uuid: str, question: str) -> list[tuple[str, int, str]]:
    """Rank the user's profile rows (plus any documents added via /document-embeddings) against the question."""
    candidates = _structured_profile_context(db, user_uuid)
    seen = {(table, source_id) for table, source_id, _ in candidates}
    for row in db.query(DocumentEmbedding).filter(DocumentEmbedding.user_uuid == user_uuid).all():
        if row.content and (row.source_table, row.source_id) not in seen:
            candidates.append((row.source_table, row.source_id, row.content))

    if len(candidates) <= RETRIEVAL_TOP_K:
        return candidates

    scores = relevance_scores(question, [content for _, _, content in candidates])
    ranked = sorted(range(len(candidates)), key=lambda index: scores[index], reverse=True)

    lowered = question.lower()
    wanted_sections = {table for table, keywords in SECTION_KEYWORDS.items() if any(keyword in lowered for keyword in keywords)}
    selected = [index for index in ranked if candidates[index][0] in wanted_sections]
    per_section: dict[str, int] = {}
    top = []
    for index in ranked:
        table = candidates[index][0]
        if per_section.get(table, 0) < MAX_PER_SECTION:
            per_section[table] = per_section.get(table, 0) + 1
            top.append(index)
        if len(top) == RETRIEVAL_TOP_K:
            break
    selected += [index for index in top if index not in selected]
    return [candidates[index] for index in selected[:MAX_CONTEXT_CHUNKS]]


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask the profile assistant",
    description="Answer a question about the authenticated user's profile using the most relevant profile rows (hybrid semantic + keyword retrieval).",
)
def ask(
    payload: AskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_uuid = _uuid_value(current_user.user_uuid)
    context_chunks = _retrieve_context(db, user_uuid, payload.question)

    if not context_chunks:
        raise HTTPException(status_code=404, detail="No profile data found for this user")

    context = "\n\n".join(
        f"[{source_table} #{source_id}] {content}" for source_table, source_id, content in context_chunks
    )

    try:
        answer = chat_completion(
            [
                {
                    "role": "system",
                    "content": (
                        "You are answering questions about a single user's professional profile using only the provided context. "
                        "If the answer isn't in the context, say you don't have that information — don't invent details."
                    ),
                },
                {"role": "user", "content": f"Question: {payload.question}\n\nContext:\n{context}"},
            ],
            max_tokens=1024,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail="AI provider request failed. Check GROQ_API_KEY and GROQ_CHAT_MODEL.") from exc

    sources = [
        SourceReference(source_table=source_table, source_id=source_id)
        for source_table, source_id, _ in context_chunks
    ]
    answer_text = answer or "I don't have that information in the provided context."
    history_entry = ChatHistory(
        user_uuid=user_uuid,
        question=payload.question,
        answer=answer_text,
        sources=[{"source_table": item.source_table, "source_id": item.source_id} for item in sources],
    )
    db.add(history_entry)
    db.commit()
    db.refresh(history_entry)

    return AskResponse(answer=answer_text, sources=sources)


@router.get(
    "/history",
    response_model=ChatHistoryListResponse,
    summary="List the authenticated user's AI chat history",
    description="Return a paginated list of the authenticated user's recent question and answer pairs.",
)
def list_chat_history(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_uuid = _uuid_value(current_user.user_uuid)
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    rows = (
        db.query(ChatHistory)
        .filter(ChatHistory.user_uuid == user_uuid)
        .order_by(ChatHistory.created_at.desc(), ChatHistory.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    items = []
    for row in rows:
        sources = []
        for item in row.sources or []:
            if isinstance(item, dict):
                sources.append(
                    SourceReference(source_table=item.get("source_table", ""), source_id=item.get("source_id", 0))
                )
        items.append(
            ChatHistoryItem(
                id=row.id,
                question=row.question,
                answer=row.answer,
                sources=sources or None,
                created_at=row.created_at,
            )
        )

    return ChatHistoryListResponse(items=items, limit=limit, offset=offset)


@router.delete(
    "/history/{history_id}",
    summary="Delete a single AI chat history entry",
)
def delete_chat_history_item(
    history_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_uuid = _uuid_value(current_user.user_uuid)
    normalized_id = str(history_id).strip()

    entry = None
    if normalized_id.isdigit():
        entry = db.query(ChatHistory).filter(ChatHistory.user_uuid == user_uuid, ChatHistory.id == int(normalized_id)).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Chat history item not found")

    db.delete(entry)
    db.commit()
    return {"message": f"Chat history item {history_id} deleted successfully"}


@router.delete(
    "/history",
    summary="Clear all AI chat history for the authenticated user",
)
def clear_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_uuid = _uuid_value(current_user.user_uuid)
    rows = db.query(ChatHistory).filter(ChatHistory.user_uuid == user_uuid).all()

    for row in rows:
        db.delete(row)

    db.commit()
    return {"message": "All chat history cleared successfully"}

