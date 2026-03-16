"""
Search service — smart query parsing with grouped English+Telugu results and cache.
"""
import re
import logging
from app.database.db import execute_query
from app.utils.gemini import gemini_service
from app.utils.cache import verse_cache

logger = logging.getLogger(__name__)

# Bible Book Mapping for Verse ID
BIBLE_BOOKS = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth",
    "1 Samuel", "2 Samuel", "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra",
    "Nehemiah", "Esther", "Job", "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon",
    "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
    "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah",
    "Malachi", "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians",
    "2 Corinthians", "Galatians", "Ephesians", "Philippians", "Colossians", "1 Thessalonians",
    "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews", "James",
    "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation"
]
BOOK_MAP = {book.lower(): i+1 for i, book in enumerate(BIBLE_BOOKS)}
BOOK_MAP["psalm"] = 19 # Alias

# Patterns that trigger AI verse search
_AI_PREFIXES = ("verses about", "verses on", "bible verses about")

# Simple heuristic for detecting question-like input
_QUESTION_STARTERS = (
    "how", "why", "what", "when", "where", "who", "which",
    "can", "should", "does", "is", "are", "will", "do",
)

# ── Grouped SQL that returns English+Telugu in one row ──────────
_GROUPED_VERSE_SQL = """
    WITH matched_verses AS (
        SELECT
            CASE
                WHEN book LIKE '{{%%' THEN (book::json->>'english')
                ELSE book
            END AS norm_book,
            chapter,
            verse
        FROM verses
        WHERE {where_clause}
        GROUP BY norm_book, chapter, verse
        ORDER BY chapter, verse
        LIMIT {limit}
    )
    SELECT
        m.norm_book AS book,
        m.chapter,
        m.verse,
        MAX(CASE WHEN LOWER(v.language) = 'english' THEN v.text END) AS english,
        MAX(CASE WHEN LOWER(v.language) = 'telugu'  THEN v.text END) AS telugu
    FROM matched_verses m
    JOIN verses v ON 
        (
            v.book = m.norm_book 
            OR (v.book LIKE '{{%%' AND (v.book::json->>'english') = m.norm_book)
        )
        AND v.chapter = m.chapter
        AND v.verse = m.verse
    GROUP BY m.norm_book, m.chapter, m.verse
    ORDER BY m.chapter, m.verse
"""

# ── FTS SQL with Ranking ──────────────────────────────────────
_FTS_GROUPED_VERSE_SQL = """
    WITH matched_verses AS (
        SELECT
            CASE
                WHEN book LIKE '{{%%' THEN (book::json->>'english')
                ELSE book
            END AS norm_book,
            chapter,
            verse,
            ts_rank_cd(search_vector, plainto_tsquery('english', %s)) +
            ts_rank_cd(search_vector_telugu, plainto_tsquery('simple', %s)) AS rank
        FROM verses
        WHERE 
            search_vector @@ plainto_tsquery('english', %s)
            OR
            search_vector_telugu @@ plainto_tsquery('simple', %s)
        ORDER BY rank DESC
        LIMIT {limit}
    )
    SELECT
        m.norm_book AS book,
        m.chapter,
        m.verse,
        MAX(CASE WHEN LOWER(v.language) = 'english' THEN v.text END) AS english,
        MAX(CASE WHEN LOWER(v.language) = 'telugu'  THEN v.text END) AS telugu
    FROM matched_verses m
    JOIN verses v ON 
        (
            v.book = m.norm_book 
            OR (v.book LIKE '{{%%' AND (v.book::json->>'english') = m.norm_book)
        )
        AND v.chapter = m.chapter
        AND v.verse = m.verse
    GROUP BY m.norm_book, m.chapter, m.verse, m.rank
    ORDER BY m.rank DESC
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

        # Use Verse Mapping Index for < 1ms lookup
        book_id = BOOK_MAP.get(book.lower().strip())
        if book_id:
            vid = (book_id * 100000) + (int(chapter) * 1000) + int(verse)
            where = "verse_id = %s"
            sql = _GROUPED_VERSE_SQL.format(where_clause=where, limit=1)
            rows = execute_query(sql, (vid,))
        else:
            # Fallback for unknown book nicknames
            where = "(book ILIKE %s OR (book LIKE '{%%' AND (book::json->>'english') ILIKE %s)) AND chapter = %s AND verse = %s"
            sql = _GROUPED_VERSE_SQL.format(where_clause=where, limit=1)
            rows = execute_query(sql, (f"{book.strip()}%", f"{book.strip()}%", int(chapter), int(verse)))
        
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

        # Use Verse Mapping Index range for fast loading
        book_id = BOOK_MAP.get(book.lower().strip())
        if book_id:
            start_vid = (book_id * 100000) + (int(chapter) * 1000) + 0
            end_vid = (book_id * 100000) + (int(chapter) * 1000) + 999
            where = "verse_id BETWEEN %s AND %s"
            sql = _GROUPED_VERSE_SQL.format(where_clause=where, limit=200)
            rows = execute_query(sql, (start_vid, end_vid))
        else:
            # Fallback
            where = "(book ILIKE %s OR (book LIKE '{%%' AND (book::json->>'english') ILIKE %s)) AND chapter = %s"
            sql = _GROUPED_VERSE_SQL.format(where_clause=where, limit=200)
            rows = execute_query(sql, (f"{book.strip()}%", f"{book.strip()}%", int(chapter)))
            
        results = _build_grouped_rows(rows)

        if results:
            verse_cache.set(cache_key, results)
        return results

    async def keyword_search(self, keyword: str):
        cache_key = verse_cache.make_key("kw", keyword)
        cached = verse_cache.get(cache_key)
        if cached is not None:
            return cached

        # Use Full-Text Search (FTS) for speed and ranking
        sql = _FTS_GROUPED_VERSE_SQL.format(limit=15)
        # We pass the keyword 4 times: 2 for ranking, 2 for filtering
        rows = execute_query(sql, (keyword, keyword, keyword, keyword))
        results = _build_grouped_rows(rows)

        # Fallback: if FTS returns nothing (e.g. stop words only or very short words),
        # we can do a partial ILIKE as a last resort (Bible names etc)
        if not results and len(keyword) > 2:
            logger.info("FTS yielded no results for '%s', falling back to ILIKE", keyword)
            like = f"%{keyword}%"
            where = """
                book ILIKE %s
                OR (book LIKE '{%%' AND (book::json->>'english') ILIKE %s)
                OR EXISTS (
                    SELECT 1 FROM verses v2
                    WHERE v2.chapter = verses.chapter
                    AND v2.verse = verses.verse
                    AND v2.text ILIKE %s
                )
            """
            sql_fallback = _GROUPED_VERSE_SQL.format(where_clause=where, limit=10)
            rows = execute_query(sql_fallback, (like, like, like))
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
