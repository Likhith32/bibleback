"""
AI service — explanations, sermons, cross-references, expand, and Ask-the-Bible.
"""
import re
import logging
from app.utils.gemini import gemini_service, RateLimitError
from app.services.search_service import search_service

logger = logging.getLogger(__name__)


class AIService:

    # ── Explanation ─────────────────────────────────────────────

    async def explain_verse(self, verse_text: str):
        if not verse_text:
            return {"error": "verse_text is required"}

        if gemini_service is None:
            return {"error": "Gemini service failed to initialize — check GEMINI_API_KEY in .env"}

        prompt = f"""
You are a biblical scholar and theologian.

Explain the following Bible verse deeply but clearly.

Verse:
"{verse_text}"

Return ONLY valid JSON. Do not include explanations outside JSON.

{{
  "meaning": "clear theological explanation",
  "historical_context": "background of author, audience, and time",
  "life_application": "how believers today can apply this verse",
  "related_verses": ["Book Chapter:Verse", "Book Chapter:Verse"]
}}
"""
        try:
            result = await gemini_service.get_response(prompt, is_json=True)
        except RateLimitError as e:
            return {"error": str(e)}
        return result or {
            "meaning": "Explanation unavailable",
            "historical_context": "",
            "life_application": "",
            "related_verses": [],
        }

    # ── Sermon Generator ───────────────────────────────────────

    async def generate_sermon(self, verse_text: str):
        if not verse_text:
            return {"error": "verse_text is required"}

        prompt = f"""
You are an experienced pastor preparing a sermon.

Generate a short sermon based on:
"{verse_text}"

Return ONLY valid JSON. Do not include explanations outside JSON.

{{
  "title": "sermon title",
  "introduction": "opening paragraph",
  "points": ["point 1", "point 2", "point 3"],
  "conclusion": "closing paragraph"
}}
"""
        try:
            result = await gemini_service.get_response(prompt, is_json=True)
        except RateLimitError as e:
            return {"error": str(e)}
        return result or {
            "title": "",
            "introduction": "",
            "points": [],
            "conclusion": "",
        }

    # ── Cross References ───────────────────────────────────────

    async def get_cross_references(self, verse_text: str):
        if not verse_text:
            return {"source_verse": "", "references": []}

        prompt = (
            f"You are a biblical scholar. "
            f"Find 5 cross-reference Bible verses for: \"{verse_text}\". "
            "Return ONLY verse references (e.g. John 3:16), one per line. "
            "Do not include explanations."
        )
        try:
            raw = await gemini_service.get_response(prompt)
        except RateLimitError as e:
            return {"error": str(e)}
        if not raw:
            return {"source_verse": verse_text, "references": []}

        refs = []
        for line in raw.strip().splitlines():
            m = re.search(r"(\d?\s?[A-Za-z]+(?:\s[A-Za-z]+)*)\s+(\d+):(\d+)", line)
            if m:
                book, ch, vs = m.group(1).strip(), m.group(2), m.group(3)
                found = await search_service.get_exact_verse(book, ch, vs)
                if found:
                    refs.extend(found)
        return {"source_verse": verse_text, "references": refs[:5]}

    # ── Ask the Bible ──────────────────────────────────────────

    async def ask_bible(self, user_query: str):
        if not user_query:
            return {"verses": [], "explanation": "", "prayer": ""}

        prompt = f"""
You are a compassionate Bible teacher.

Answer this question using the Bible: "{user_query}"

Return ONLY valid JSON. Do not include explanations outside JSON.

{{
  "verses": ["Book Chapter:Verse", "Book Chapter:Verse"],
  "explanation": "detailed biblical explanation",
  "prayer": "a short comforting prayer"
}}
"""
        try:
            ai_data = await gemini_service.get_response(prompt, is_json=True)
        except RateLimitError as e:
            return {"error": str(e)}
        if not ai_data:
            return {"verses": [], "explanation": "", "prayer": ""}

        verse_details = []
        for ref in ai_data.get("verses", []):
            found = await search_service.parse_query_and_search(ref)
            results = found[0] if isinstance(found, tuple) else found
            if results:
                verse_details.extend(results)

        return {
            "verses": verse_details[:5],
            "explanation": ai_data.get("explanation", ""),
            "prayer": ai_data.get("prayer", ""),
        }

    # ── Expand Verse Study ────────────────────────────────────

    async def expand_verse(self, verse_text: str):
        if not verse_text:
            return {"error": "verse_text is required"}

        prompt = f"""
You are a biblical scholar and theologian.

Expand this Bible verse for in-depth study:
"{verse_text}"

Return ONLY valid JSON. Do not include explanations outside JSON.

{{
  "context": "historical and cultural context of this verse",
  "meaning": "detailed theological meaning and interpretation",
  "application": "practical application for modern life",
  "cross_references": ["Book Chapter:Verse", "Book Chapter:Verse", "Book Chapter:Verse"]
}}
"""
        try:
            result = await gemini_service.get_response(prompt, is_json=True)
        except RateLimitError as e:
            return {"error": str(e)}
        if not result:
            return {
                "context": "",
                "meaning": "",
                "application": "",
                "cross_references": [],
            }

        # Fetch actual verse data for cross references
        cross_ref_details = []
        for ref in result.get("cross_references", []):
            found = await search_service.parse_query_and_search(ref)
            results = found[0] if isinstance(found, tuple) else found
            if results:
                cross_ref_details.extend(results)

        return {
            "context": result.get("context", ""),
            "meaning": result.get("meaning", ""),
            "application": result.get("application", ""),
            "cross_references": cross_ref_details[:5],
        }


ai_service = AIService()
