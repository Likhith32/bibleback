"""
AI routes — explain, sermon, cross-refs, expand, ask-the-Bible.
"""
import logging
from fastapi import APIRouter, Body, HTTPException
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ai/explain")
async def explain(payload: dict = Body(...)):
    verse_text = payload.get("verse_text", "").strip()
    if not verse_text:
        raise HTTPException(status_code=400, detail="verse_text is required")
    try:
        result = await ai_service.explain_verse(verse_text)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error("Explain error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Explanation failed")


@router.post("/ai/sermon")
async def sermon(payload: dict = Body(...)):
    verse_text = payload.get("verse_text", "").strip()
    if not verse_text:
        raise HTTPException(status_code=400, detail="verse_text is required")
    try:
        result = await ai_service.generate_sermon(verse_text)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error("Sermon error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Sermon generation failed")


@router.post("/ai/crossrefs")
async def crossrefs(payload: dict = Body(...)):
    verse_text = payload.get("verse_text", "").strip()
    if not verse_text:
        raise HTTPException(status_code=400, detail="verse_text is required")
    try:
        result = await ai_service.get_cross_references(verse_text)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error("Cross-refs error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Cross-references failed")


@router.post("/ai/ask")
async def ask(payload: dict = Body(...)):
    query = payload.get("query", "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="query is required")
    try:
        result = await ai_service.ask_bible(query)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error("Ask error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Ask Bible failed")


@router.post("/ai/expand")
async def expand(payload: dict = Body(...)):
    verse_text = payload.get("verse_text", "").strip()
    if not verse_text:
        raise HTTPException(status_code=400, detail="verse_text is required")
    try:
        result = await ai_service.expand_verse(verse_text)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error("Expand error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Expand failed")
