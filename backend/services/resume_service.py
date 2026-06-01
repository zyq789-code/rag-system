import uuid
import json
import aiofiles
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from models.resume import ResumeAnalysis
from repositories.resume import ResumeRepository
from integrations.document_parser import DocumentParser
from integrations.llm.base import LLMProvider
from core.exceptions import ProcessingError


RESUME_PROMPT = """请分析以下简历内容，并以 JSON 格式返回分析结果。

返回格式：
{{
  "overall_score": 0-100的综合评分,
  "summary": "一段话总结",
  "skills": [{{"name": "技能名", "level": "beginner/intermediate/expert", "years": 工作年限}}],
  "strengths": ["优势1", "优势2"],
  "gaps": ["不足1", "不足2"],
  "interview_questions": [
    {{
      "question": "面试题",
      "category": "technical/behavioral/project",
      "difficulty": "easy/medium/hard",
      "expected_points": ["要点1", "要点2"]
    }}
  ]
}}

简历内容：
{resume_text}"""

INTERVIEW_PROMPT = """基于以下简历分析结果，生成 5 道针对性面试题。

分析结果：
{analysis_json}

请以 JSON 数组格式返回，每个元素包含 question, category, difficulty, expected_points 字段。"""


class ResumeService:
    def __init__(self, session: AsyncSession, llm: LLMProvider, upload_dir: str = "./uploads"):
        self.session = session
        self.repo = ResumeRepository(session)
        self.llm = llm
        self.parser = DocumentParser()
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def upload(self, file: UploadFile) -> ResumeAnalysis:
        if not file.filename:
            raise ProcessingError("No filename provided")

        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext not in {"pdf", "docx", "txt"}:
            raise ProcessingError(f"Unsupported file type: {ext}")

        unique_name = f"{uuid.uuid4().hex}.{ext}"
        file_path = self.upload_dir / unique_name
        content = await file.read()

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        resume = ResumeAnalysis(
            filename=file.filename,
            file_path=str(file_path),
            status="processing",
        )
        await self.repo.create(resume)

        try:
            text = self.parser.parse(str(file_path), ext)
            prompt = RESUME_PROMPT.format(resume_text=text[:4000])
            response = await self.llm.chat([{"role": "user", "content": prompt}])

            result = self._parse_json(response)
            resume.analysis_result = result
            resume.status = "completed"
        except Exception as e:
            from loguru import logger
            logger.error(f"Resume analysis failed: {e}")
            resume.status = "failed"

        await self.session.flush()
        await self.session.refresh(resume)
        return resume

    async def get(self, resume_id: uuid.UUID) -> ResumeAnalysis:
        resume = await self.repo.get_by_id(resume_id)
        if resume is None:
            raise ProcessingError(f"Resume {resume_id} not found")
        return resume

    async def generate_interview_questions(self, resume_id: uuid.UUID) -> list[dict]:
        resume = await self.get(resume_id)
        if not resume.analysis_result:
            raise ProcessingError("Resume analysis not completed")

        prompt = INTERVIEW_PROMPT.format(analysis_json=json.dumps(resume.analysis_result, ensure_ascii=False))
        response = await self.llm.chat([{"role": "user", "content": prompt}])
        return self._parse_json(response)

    def _parse_json(self, text: str) -> dict | list:
        try:
            if "```" in text:
                json_str = text.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
                return json.loads(json_str.strip())
            return json.loads(text.strip())
        except json.JSONDecodeError:
            return {"raw_response": text}
