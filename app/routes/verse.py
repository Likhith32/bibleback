"""
Verse routes — single-verse lookup, autocomplete, and TTS.
"""
import logging
from fastapi import APIRouter, Query, HTTPException
from app.services.verse_service import verse_service
from app.utils.formatter import format_verse_for_tts

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/verse")
async def get_verse(book: str, chapter: int, verse: int):
    try:
        results = await verse_service.get_verse(book, chapter, verse)
        if not results:
            raise HTTPException(status_code=404, detail="Verse not found")
        return {"success": True, "data": results[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Verse lookup error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Verse lookup failed")


@router.get("/suggest")
async def suggest(q: str = Query(..., min_length=1)):
    try:
        suggestions = await verse_service.get_suggestions(q)
        return {"success": True, "suggestions": suggestions}
    except Exception as e:
        logger.error("Suggestion error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Suggestions failed")


@router.get("/tts")
async def text_to_speech(book: str, chapter: int, verse: int):
    """Return verse text formatted for frontend Web Speech API."""
    try:
        results = await verse_service.get_verse(book, chapter, verse)
        if not results:
            raise HTTPException(status_code=404, detail="Verse not found")

        v = results[0]
        tts_text = format_verse_for_tts(
            v["book"], v["chapter"], v["verse"], v["english"]
        )
        return {
            "success": True,
            "book": v["book"],
            "chapter": v["chapter"],
            "verse": v["verse"],
            "text": v["english"],
            "tts_text": tts_text,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("TTS error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="TTS failed")
