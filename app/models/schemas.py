"""
Pydantic schemas for structured API responses.
"""
from pydantic import BaseModel
from typing import List, Optional, Any


# ── Verse Models ────────────────────────────────────────────────

class VerseBase(BaseModel):
    book: str
    chapter: int
    verse: int
    text: str
    language: str


class VerseDetail(BaseModel):
    book: str
    chapter: int
    verse: int
    english: str = ""
    telugu: str = ""


# ── Search Response ─────────────────────────────────────────────

class SearchResponse(BaseModel):
    query: str
    query_type: str          # "exact" | "chapter" | "keyword" | "ai" | "ask"
    total: int
    results: List[VerseDetail]
    cached: bool = False


# ── AI Response Models ──────────────────────────────────────────

class AIExplanation(BaseModel):
    meaning: str = ""
    historical_context: str = ""
    life_application: str = ""


class AISermon(BaseModel):
    title: str = ""
    introduction: str = ""
    points: List[str] = []
    conclusion: str = ""


class AIAskResponse(BaseModel):
    verses: List[VerseDetail] = []
    explanation: str = ""
    prayer: str = ""


class AICrossRefResponse(BaseModel):
    source_verse: str
    references: List[VerseDetail] = []


# ── Daily Verse ─────────────────────────────────────────────────

class DailyVerseResponse(BaseModel):
    verse: VerseDetail
    explanation: str = ""
    prayer: str = ""
    reflection: str = ""


# ── TTS ─────────────────────────────────────────────────────────

class TTSResponse(BaseModel):
    book: str
    chapter: int
    verse: int
    text: str
    tts_text: str


# ── Export Request ──────────────────────────────────────────────

class ExportRequest(BaseModel):
    content: str
    title: str = "Bible Study Notes"


# ── Generic wrapper ─────────────────────────────────────────────

class APIResponse(BaseModel):
    success: bool = True
    data: Any = None
    error: Optional[str] = None
