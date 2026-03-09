"""
Daily verse service — random verse with AI-generated reflection.
"""
import logging
from app.database.db import execute_query
from app.utils.gemini import gemini_service

logger = logging.getLogger(__name__)


class DailyService:

    async def get_daily_verse(self):
        # Pick a random English verse
        sql = """
            SELECT book, chapter, verse, text
            FROM verses
            WHERE LOWER(language) = 'english'
            ORDER BY RANDOM()
            LIMIT 1
        """
        row = execute_query(sql, fetch_all=False)
        if not row:
            logger.warning("No verses found in database")
            return {
                "verse": {"book": "", "chapter": 0, "verse": 0, "english": "", "telugu": ""},
                "explanation": "",
                "prayer": "",
                "reflection": "",
            }

        book, chapter, verse, text = row

        # Fetch Telugu translation
        telugu_sql = """
            SELECT text FROM verses
            WHERE book = %s
              AND chapter = %s
              AND verse   = %s
              AND LOWER(language) = 'telugu'
        """
        telugu_row = execute_query(telugu_sql, (book, chapter, verse), fetch_all=False)
        telugu_text = telugu_row[0] if telugu_row else ""

        # AI reflection
        prompt = f"""Provide a daily reflection for the Bible verse {book} {chapter}:{verse} — "{text}"
Return a JSON object with exactly these keys:
{{
  "explanation": "verse explanation",
  "prayer": "a short prayer",
  "reflection": "a thought for the day"
}}"""
        ai_meta = await gemini_service.get_response(prompt, is_json=True)

        return {
            "verse": {
                "book": book,
                "chapter": chapter,
                "verse": verse,
                "english": text,
                "telugu": telugu_text,
            },
            "explanation": (ai_meta or {}).get("explanation", ""),
            "prayer": (ai_meta or {}).get("prayer", ""),
            "reflection": (ai_meta or {}).get("reflection", ""),
        }


daily_service = DailyService()
