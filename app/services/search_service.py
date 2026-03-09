"""
Search service — smart query parsing with grouped English+Telugu results and cache.
"""
import re
import logging
from app.database.db import execute_query
from app.utils.gemini import gemini_service
from app.utils.cache import verse_cache

logger = logging.getLogger(__name__)

# Patterns that trigger AI verse search
_AI_PREFIXES = ("verses about", "verses on", "bible verses about")

# Simple heuristic for detecting question-like input
_QUESTION_STARTERS = (
    "how", "why", "what", "when", "where", "who", "which",
    "can", "should", "does", "is", "are", "will", "do",
)

# ── Grouped SQL that returns English+Telugu in one row ──────────
_GROUPED_VERSE_SQL = """
    SELECT
        book,
        chapter,
        verse,
        MAX(CASE WHEN LOWER(language) = 'english' THEN text END) AS english,
        MAX(CASE WHEN LOWER(language) = 'telugu'  THEN text END) AS telugu
    FROM verses
    WHERE {where_clause}
    GROUP BY book, chapter, verse
    ORDER BY chapter, verse
    LIMIT {limit}
"""


def _build_grouped_rows(rows):
    """Convert grouped SQL rows into dicts."""
    if not rows:
        return []
    return [
        {
            "book": r[0],
            "chapter": r[1],
            "verse": r[2],
            "english": r[3] or "",
            "telugu": r[4] or "",
        }
        for r in rows
    ]


class SearchService:

    # ── public entry point ──────────────────────────────────────

    async def parse_query_and_search(self, query: str):
        """
        Detect query type and dispatch to the right handler.
        Returns (results_list, query_type_string).
        """
        q = query.strip()
        q_lower = q.lower()

        # 1 ▸ Exact verse  (e.g.  John 3:16)
        if ":" in q:
            m = re.match(r"(.+?)\s+(\d+):(\d+)", q)
            if m:
                book, ch, vs = m.group(1), m.group(2), m.group(3)
                results = await self.get_exact_verse(book, ch, vs)
                return results, "exact"

        # 2 ▸ Full chapter  (e.g.  Psalm 23)
        m = re.match(r"^(.+?)\s+(\d+)$", q)
        if m:
            book, ch = m.group(1), m.group(2)
            results = await self.get_full_chapter(book, ch)
            return results, "chapter"

        # 3 ▸ AI verse search  (e.g.  "verses about hope")
        if any(q_lower.startswith(p) for p in _AI_PREFIXES):
            results = await self.semantic_ai_search(q)
            return results, "ai"

        # 4 ▸ Question → Ask Bible  (e.g.  "How to overcome fear?")
        first_word = q_lower.split()[0] if q_lower else ""
        if first_word in _QUESTION_STARTERS or q.endswith("?"):
            results = await self.semantic_ai_search(q)
            return results, "ask"

        # 5 ▸ Keyword / topic search
        results = await self.keyword_search(q)
        return results, "keyword"

    # ── individual strategies ───────────────────────────────────

    async def get_exact_verse(self, book: str, chapter: str, verse: str):
        cache_key = verse_cache.make_key("verse", book, chapter, verse)
        cached = verse_cache.get(cache_key)
        if cached is not None:
            logger.info("Cache hit for %s %s:%s", book, chapter, verse)
            return cached

        where = "LOWER(book) LIKE LOWER(%s) AND chapter = %s AND verse = %s"
        sql = _GROUPED_VERSE_SQL.format(where_clause=where, limit=1)
        rows = execute_query(sql, (f"{book.strip()}%", int(chapter), int(verse)))
        results = _build_grouped_rows(rows)

        if results:
            verse_cache.set(cache_key, results)
        return results

    async def get_full_chapter(self, book: str, chapter: str):
        cache_key = verse_cache.make_key("chapter", book, chapter)
        cached = verse_cache.get(cache_key)
        if cached is not None:
            logger.info("Cache hit for %s chapter %s", book, chapter)
            return cached

        where = "LOWER(book) LIKE LOWER(%s) AND chapter = %s"
        sql = _GROUPED_VERSE_SQL.format(where_clause=where, limit=200)
        rows = execute_query(sql, (f"{book.strip()}%", int(chapter)))
        results = _build_grouped_rows(rows)

        if results:
            verse_cache.set(cache_key, results)
        return results

    async def keyword_search(self, keyword: str):
        cache_key = verse_cache.make_key("kw", keyword)
        cached = verse_cache.get(cache_key)
        if cached is not None:
            return cached

        like = f"%{keyword}%"
        where = "text ILIKE %s OR book ILIKE %s"
        sql = _GROUPED_VERSE_SQL.format(where_clause=where, limit=10)
        rows = execute_query(sql, (like, like))
        results = _build_grouped_rows(rows)

        if results:
            verse_cache.set(cache_key, results, ttl=1800)
        return results

    async def semantic_ai_search(self, query: str):
        prompt = (
            f"Find Bible verses related to: {query}. "
            "Return ONLY verse references, one per line, in the format: Book Chapter:Verse"
        )
        ai_output = await gemini_service.get_response(prompt)
        if not ai_output:
            return []

        all_verses = []
        for line in ai_output.strip().splitlines():
            m = re.search(r"(\d?\s?[A-Za-z]+(?:\s[A-Za-z]+)*)\s+(\d+):(\d+)", line)
            if m:
                book, ch, vs = m.group(1).strip(), m.group(2), m.group(3)
                v = await self.get_exact_verse(book, ch, vs)
                if v:
                    all_verses.extend(v)
            if len(all_verses) >= 10:
                break
        return all_verses[:10]


search_service = SearchService()
