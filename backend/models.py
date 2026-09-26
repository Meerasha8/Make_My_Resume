from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from database import Base, engine
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from pydantic import BaseModel

try:
    from sqlalchemy.dialects.postgresql import UUID as PGUUID
except Exception:  # pragma: no cover
    PGUUID = None


def _uuid_column(*, nullable: bool = False, index: bool = False):
    backend = engine.url.get_backend_name() if engine is not None else ""
    if backend == "sqlite" or PGUUID is None:
        return Column(String(36), nullable=nullable, index=index)
    return Column(PGUUID(as_uuid=True), nullable=nullable, index=index)


def _uuid_value(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)  # uuid.UUID -> canonical dashed form, matching the job ids used in URLs


class User(BaseModel):
    user_uuid: str
    email: str | None = None


class UserDetails(Base):
    
    __tablename__ = "user_details"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    mobile_number = Column(String(20), index=True)
    email_id = Column(String(40), index=True)
    github_url = Column(String(40), index=True)
    linkedin_url = Column(String(40), index=True)
    portfolio_link = Column(String(40), index=True)
    location = Column(String(40), index=True)
    profession_summary = Column(String(255), index=True)
    user_uuid = _uuid_column(nullable=False)



class Educations(Base):
    
    __tablename__ = "education"
    id = Column(Integer, primary_key=True, index=True)
    course_name = Column(String(50),index=True)
    cgpa = Column(Float,index=True)
    start_year = Column(Integer,index=True)
    end_year = Column(Integer,index=True)
    college_name = Column(String(50), index=True)
    location = Column(String(50),index=True)
    user_uuid = _uuid_column(nullable=False)


    
class Certificates(Base):
    
    __tablename__= "certificates"
    id = Column(Integer, primary_key=True, index=True)
    certificate_issuer = Column(String(255),index=True)
    certificate_name = Column(String(50), index=True)
    user_uuid = _uuid_column(nullable=False)

    
class Internship(Base):
    
    __tablename__="internship"
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(50), index=True)
    role = Column(String(20), index=True)
    description = Column(String(255),index=True)
    duration = Column(String(20),index=True)
    user_uuid = _uuid_column(nullable=False)

    
class Achievements(Base):
    
    __tablename__="achievements"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String(255),index=True)
    user_uuid = _uuid_column(nullable=False)
    

class Projects(Base):
    
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    description = Column(String(255), index=True)
    tech_stack = Column(String(50),index=True)
    github_url = Column(String(255), index=True)
    live_link = Column(String(255), index=True)
    user_uuid = _uuid_column(nullable=False)
    
class Skills(Base):

    __tablename__ = "skills"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    description = Column(String(255), index=True)
    user_uuid = _uuid_column(nullable=False)


class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, index=True)
    user_uuid = _uuid_column(nullable=False, index=True)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    sources = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ResumeHistory(Base):
    __tablename__ = "resume_history"
    id = Column(Integer, primary_key=True, index=True)
    job_id = _uuid_column(nullable=False, index=True)
    user_uuid = _uuid_column(nullable=False, index=True)
    job_description = Column(String, nullable=False)
    status = Column(String(20), nullable=False, default="queued")
    download_url = Column(String, nullable=True)
    error = Column(String, nullable=True)
    template_style = Column(String(50), nullable=True, default="modern")
    resume_content = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class DocumentEmbedding(Base):
    __tablename__ = "document_embeddings"
    id = Column(Integer, primary_key=True)
    user_uuid = _uuid_column(nullable=False)
    source_table = Column(String, nullable=False)
    source_id = Column(Integer, nullable=False)
    content = Column(String, nullable=False)
    embedding = Column(Vector(384))