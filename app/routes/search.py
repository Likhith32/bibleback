"""
Search routes — smart search with suggestions fallback.
"""
import logging
from fastapi import APIRouter, Query, HTTPException
from app.services.search_service import search_service
from app.services.verse_service import verse_service
from app.utils.formatter import highlight_keywords

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/search")
async def search(q: str = Query(..., min_length=1, description="Search query")):
    try:
        results, query_type = await search_service.parse_query_and_search(q)

        # Apply keyword highlighting for keyword / topic searches
        if query_type == "keyword":
            for r in results:
                r["english"] = highlight_keywords(r.get("english", ""), q)
                r["telugu"] = highlight_keywords(r.get("telugu", ""), q)

        # If no results, try to get suggestions
        suggestions = []
        if not results:
            suggestions = await verse_service.get_suggestions(q)

        logger.info("Search [%s] q=%r → %d results, %d suggestions",
                     query_type, q, len(results), len(suggestions))

        return {
            "success": True,
            "query": q,
            "query_type": query_type,
            "total": len(results),
            "results": results,
            "suggestions": suggestions,
        }

    except Exception as e:
        logger.error("Search error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Search failed")
