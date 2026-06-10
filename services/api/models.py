"""Pydantic models for API request/response."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class CourseSummary(BaseModel):
    course_id: str
    name: str
    materials_count: int
    stage: str
    due_items_count: int
    last_reviewed: Optional[str] = None


class InitReviewResponse(BaseModel):
    course_id: str
    review_dir: str
    created: list[str]
    skipped: list[str]


class MaterialFile(BaseModel):
    id: str
    path: str
    name: str
    material_type: Literal[
        "slides",
        "past_exam",
        "mock_exam",
        "homework_answer",
        "teacher_focus",
        "notes",
        "textbook",
        "other",
    ]
    ext: str
    status: str
    tags: list[str] = []


class MaterialsListResponse(BaseModel):
    course_id: str
    files: list[MaterialFile]


class Evidence(BaseModel):
    source_file: str
    reason: str


class Priority(BaseModel):
    topic: str
    chapter: Optional[str] = None
    weight: int
    question_types: list[str]
    evidence: list[Evidence]
    recommended_action: str


class ExamAnalysisResponse(BaseModel):
    analysis_id: str
    course_id: str
    priorities_count: int
    confidence: str
    priorities: list[Priority]


class GeneratedQuestion(BaseModel):
    id: str
    course_id: str
    question_type: str
    topic: str
    prompt: str
    expected_answer: str
    scoring_points: list[str]
    difficulty: str
    label: str
    time_limit_sec: int


class GenerateQuestionsResponse(BaseModel):
    questions_count: int
    question_ids: list[str]
    questions: list[GeneratedQuestion]


class PlanResponse(BaseModel):
    goal: str
    minutes: Optional[int] = None
    days: Optional[int] = None
    first_action: str
    plan_md: str


class StartSessionRequest(BaseModel):
    source: Literal["generated", "due", "cards"] = "generated"
    limit: int = Field(default=5, ge=1, le=50)


class QuestionResponse(BaseModel):
    session_id: str
    question_index: int
    total_questions: int
    question: GeneratedQuestion | dict


class AnswerRequest(BaseModel):
    session_id: str
    answer: str


class GradingResponse(BaseModel):
    verdict: Literal["correct", "partial", "wrong"]
    score_hint: str
    covered_points: list[str]
    omissions: list[str]
    better_answer: str
    follow_up_question: str
    card_id: Optional[str] = None
    has_next: bool = False
    next_question: Optional[dict] = None
    awaiting_rating: bool = False


class RateResponse(BaseModel):
    card_id: Optional[str] = None
    rating: str
    due: str
    has_next: bool
    question_index: Optional[int] = None
    total_questions: Optional[int] = None
    next_question: Optional[dict] = None


class AgentRunRequest(BaseModel):
    course_id: str
    message: str
    goal: Literal["pass", "score_high"] = "pass"


class AgentRunResponse(BaseModel):
    intent: str
    state_before: str
    tool_called: Optional[str] = None
    state_after: str
    message: str
    next_action: dict
    artifacts: list[str] = []
    warnings: list[str] = []
