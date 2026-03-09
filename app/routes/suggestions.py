"""
Suggestions route — autocomplete endpoint.
"""
import logging
from fastapi import APIRouter, Query, HTTPException
from app.services.verse_service import verse_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/suggest")
async def suggest(q: str = Query(..., min_length=1)):
    try:
        suggestions = await verse_service.get_suggestions(q)
        return {"success": True, "suggestions": suggestions}
    except Exception as e:
        logger.error("Suggestion error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Suggestions failed")
