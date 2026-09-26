import json
import os
import unittest
from uuid import UUID
from unittest.mock import patch

os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("SUPABASE_DB_URL", "sqlite:///./test.db")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from auth.dependencies import get_current_user
from database import Base
from dependencies import get_db
from mains import dapp
from models import (
    Achievements,
    Certificates,
    ChatHistory,
    DocumentEmbedding,
    Educations,
    Internship,
    Projects,
    ResumeHistory,
    Skills,
    User,
    UserDetails,
)
from resume_service import ResumeContent
import llm as llm_module
from routes import ai_chat as ai_chat_module, resume as resume_module


class DocumentEmbeddingRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        sqlite_tables = [
            Projects.__table__,
            Skills.__table__,
            Educations.__table__,
            Internship.__table__,
            Achievements.__table__,
            Certificates.__table__,
            UserDetails.__table__,
            DocumentEmbedding.__table__,
            ChatHistory.__table__,
            ResumeHistory.__table__,
        ]
        Base.metadata.drop_all(bind=engine, tables=sqlite_tables)
        Base.metadata.create_all(bind=engine, tables=sqlite_tables)

        def override_get_db():
            db = self.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        async def override_get_current_user():
            return User(user_uuid="00000000-0000-0000-0000-000000000001", email="user@example.com")

        dapp.dependency_overrides[get_db] = override_get_db
        dapp.dependency_overrides[get_current_user] = override_get_current_user
        self.client = TestClient(dapp)

        self.session = self.TestingSessionLocal()
        self.session.add(
            Projects(
                name="Portfolio app",
                description="Built a portfolio app",
                tech_stack="FastAPI",
                github_url="https://example.com",
                live_link="https://app.example.com",
                user_uuid="00000000-0000-0000-0000-000000000001",
            )
        )
        self.session.commit()
        self.session.close()

    def test_create_and_list_document_embeddings(self) -> None:
        response = self.client.post(
            "/document-embeddings/",
            json={
                "source_table": "projects",
                "source_id": 1,
                "content": "hello world",
                "embedding": [0.1 + index * 0.001 for index in range(384)],
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["content"], "hello world")
        self.assertEqual(payload["source_table"], "projects")

        list_response = self.client.get("/document-embeddings/")
        self.assertEqual(list_response.status_code, 200, list_response.text)
        self.assertEqual(len(list_response.json()), 1)

    def test_ai_ask_uses_structured_fallback(self) -> None:
        class FakeChatCompletion:
            def create(self, **kwargs):
                return type("Response", (), {"choices": [type("Choice", (), {"message": type("Message", (), {"content": "The user built a portfolio app."})()})()]})()

        class FakeClient:
            def __init__(self, *args, **kwargs):
                self.chat = type("Chat", (), {"completions": type("Completions", (), {"create": FakeChatCompletion().create})()})()

        with patch.object(llm_module, "Groq", FakeClient):
            response = self.client.post(
                "/ai/ask",
                json={"question": "What did this user build?"},
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertIn("portfolio app", payload["answer"].lower())
        self.assertTrue(payload["sources"])

        history_response = self.client.get("/ai/history")
        self.assertEqual(history_response.status_code, 200, history_response.text)
        self.assertEqual(len(history_response.json()["items"]), 1)

    def test_resume_history_is_persisted_and_listed(self) -> None:
        class FakeResumeService:
            def select_resume_content(self, *args, **kwargs):
                return ResumeContent()

            def render_docx(self, *args, **kwargs):
                return b"PK\x03\x04"

        with patch.object(resume_module, "ResumeService", FakeResumeService):
            response = self.client.post(
                "/resume/generate",
                json={"job_description": "Senior backend engineer"},
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["status"], "completed")

        history_response = self.client.get("/resume/history")
        self.assertEqual(history_response.status_code, 200, history_response.text)
        self.assertEqual(len(history_response.json()["items"]), 1)
        self.assertEqual(history_response.json()["items"][0]["job_description"], "Senior backend engineer")

        # Nothing is written to disk: the DOCX is rebuilt from the stored content (survives Render restarts).
        download = self.client.get(f"/resume/generate/{payload['job_id']}/download")
        self.assertEqual(download.status_code, 200, download.text)
        self.assertTrue(download.content.startswith(b"PK"))  # DOCX files are zip archives
        self.assertIn("attachment;", download.headers["content-disposition"])

    def test_download_handles_text_column_and_old_format(self) -> None:
        # Supabase stores resume_content in a `text` column (JSON string), and older resumes used a flat skills list.
        session = self.TestingSessionLocal()
        old_format = {"summary": "x", "skills": ["Python", "PostgreSQL", "Docker"], "experience": [], "projects": [
            {"name": "Portfolio app", "highlights": ["Built it"]}], "education": [], "certificates": []}
        new_format = {"skills": [{"category": "Languages", "items": ["Python"]}], "projects": [], "achievements": ["Won"]}
        for job_id, content in (("11111111-1111-1111-1111-111111111111", json.dumps(old_format)),
                                ("22222222-2222-2222-2222-222222222222", json.dumps(new_format))):
            session.add(ResumeHistory(job_id=job_id, user_uuid="00000000-0000-0000-0000-000000000001",
                                      job_description="jd", status="completed", resume_content=content))
        session.commit()
        session.close()

        for job_id in ("11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222"):
            response = self.client.get(f"/resume/generate/{job_id}/download")
            self.assertEqual(response.status_code, 200, response.text)
            self.assertTrue(response.content.startswith(b"PK"))

        preview = self.client.get("/resume/generate/11111111-1111-1111-1111-111111111111/preview").json()
        self.assertEqual([group["category"] for group in preview["content"]["skills"]], ["Languages", "Databases", "Deployment & Tools"])


class RetrievalTests(unittest.TestCase):
    USER = "00000000-0000-0000-0000-000000000002"

    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(bind=engine)
        self.db = sessionmaker(bind=engine)()
        self.db.add_all(
            [
                Projects(name="Hostify", description="Event ticketing platform with Razorpay payments", tech_stack="Django",
                         github_url="", live_link="", user_uuid=self.USER),
                Projects(name="Smart EB Tracker", description="IoT app with ESP32 sensor tracking electricity usage",
                         tech_stack="React Native", github_url="", live_link="", user_uuid=self.USER),
                Projects(name="Chess Engine", description="Minimax search with alpha-beta pruning", tech_stack="C++",
                         github_url="", live_link="", user_uuid=self.USER),
                Educations(course_name="B.E. CSE", cgpa=8.21, start_year=2024, end_year=2028,
                           college_name="Chennai Institute of Technology", location="Chennai", user_uuid=self.USER),
                Achievements(description="Winner of Eco Verse Hackathon", user_uuid=self.USER),
                *[Skills(name=name, description="", user_uuid=self.USER) for name in ("Python", "Docker", "React", "PostgreSQL", "AWS", "Git")],
            ]
        )
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()

    def _sources(self, question):
        return [(table, content) for table, _, content in ai_chat_module._retrieve_context(self.db, self.USER, question)]

    def test_most_relevant_row_is_ranked_first(self) -> None:
        self.assertEqual(self._sources("What is my CGPA?")[0][0], "education")
        self.assertIn("Smart EB Tracker", self._sources("Which of my work involves IoT hardware?")[0][1])
        self.assertIn("Hostify", self._sources("Have I integrated payments?")[0][1])

    def test_retrieval_limits_context_to_top_k(self) -> None:
        self.assertLessEqual(len(self._sources("Do I know Docker?")), ai_chat_module.RETRIEVAL_TOP_K)

    def test_section_questions_include_every_row_of_that_section(self) -> None:
        sources = self._sources("List all my projects")
        self.assertEqual(sum(table == "projects" for table, _ in sources), 3)


class SkillCategoryTests(unittest.TestCase):
    def test_skills_use_fixed_categories_in_fixed_order(self) -> None:
        from resume_service import SKILL_CATEGORIES, group_skills

        groups = group_skills(
            [
                ("Kubernetes", None), ("Next.js", None), ("Operating Systems", None), ("MongoDB", None), ("FastAPI", None),
                ("PostgreSQL", "Backend"),
                ("TypeScript", "Databases"), ("Data Structures & Algorithms", None), ("Python", None),
            ]
        )
        self.assertEqual([group.category for group in groups], SKILL_CATEGORIES)
        by_category = {group.category: group.items for group in groups}
        self.assertEqual(by_category["Languages"], ["TypeScript", "Python"])  # order preserved, bogus AI category ignored
        self.assertEqual(by_category["Backend"], ["FastAPI"])
        self.assertEqual(by_category["Databases"], ["MongoDB", "PostgreSQL"])
        self.assertEqual(by_category["Frontend"], ["Next.js"])
        self.assertEqual(by_category["Deployment & Tools"], ["Kubernetes"])
        self.assertEqual(by_category["Core Concepts"], ["Operating Systems", "Data Structures & Algorithms"])

    def test_unknown_skill_uses_ai_category_when_valid(self) -> None:
        from resume_service import SKILL_CATEGORIES, categorize_skill

        self.assertEqual(categorize_skill("Pandas", "Backend"), "Backend")
        self.assertIn(categorize_skill("Pandas", "Data Science"), SKILL_CATEGORIES)
        self.assertEqual(categorize_skill("ScyllaDB"), "Databases")  # not in the dictionary: caught by the "...DB" name rule


if __name__ == "__main__":
    unittest.main()
