"""
Verse service — suggestions with prefix search + fuzzy (pg_trgm) fallback.
"""
import logging
from app.database.db import execute_query
from app.services.search_service import search_service

logger = logging.getLogger(__name__)


class VerseService:

    async def get_verse(self, book: str, chapter: int, verse: int):
        return await search_service.get_exact_verse(book, str(chapter), str(verse))

    async def get_suggestions(self, partial_query: str):
        """
        3-step suggestion logic:
          Step 1 — Prefix search on book names
          Step 2 — Contains search (for partial matches like 'char' → '1 Chronicles')
          Step 3 — Fuzzy search (pg_trgm) if prefix+contains return nothing
          Step 4 — Add chapter + verse combos for matched books
        """
        pq = partial_query.strip()
        if not pq:
            return []

        suggestions: list[str] = []
        matched_books: list[str] = []

        # ── Step 1: Prefix search ───────────────────────────────
        prefix_sql = """
            SELECT DISTINCT book
            FROM verses
            WHERE LOWER(book) LIKE LOWER(%s)
            ORDER BY similarity(book, %s) DESC
            LIMIT 6
        """
        prefix_results = execute_query(prefix_sql, (f"{pq}%", pq))
        if prefix_results:
            matched_books = [r[0] for r in prefix_results]
            logger.info("Prefix search '%s' → %d books", pq, len(matched_books))

        # ── Step 2: Contains search (handles 'char' → '1 Chronicles') ──
        if not matched_books:
            contains_sql = """
                SELECT DISTINCT book
                FROM verses
                WHERE LOWER(book) LIKE LOWER(%s)
                ORDER BY similarity(book, %s) DESC
                LIMIT 6
            """
            contains_results = execute_query(contains_sql, (f"%{pq}%", pq))
            if contains_results:
                matched_books = [r[0] for r in contains_results]
                logger.info("Contains search '%s' → %d books", pq, len(matched_books))

        # ── Step 3: Fuzzy search fallback (pg_trgm) ─────────────
        if not matched_books:
            fuzzy_sql = """
                SELECT DISTINCT book, similarity(book, %s) AS sim
                FROM verses
                WHERE similarity(book, %s) > 0.2
                ORDER BY sim DESC
                LIMIT 5
            """
            fuzzy_results = execute_query(fuzzy_sql, (pq, pq))
            if fuzzy_results:
                matched_books = [r[0] for r in fuzzy_results]
                logger.info("Fuzzy search '%s' → %d books", pq, len(matched_books))

        suggestions.extend(matched_books)

        # ── Step 4: Add chapter + verse combos ──────────────────
        if len(matched_books) == 1:
            book_name = matched_books[0]

            ch_sql = """
                SELECT DISTINCT chapter
                FROM verses
                WHERE book = %s
                ORDER BY chapter
                LIMIT 5
            """
            chapters = execute_query(ch_sql, (book_name,))
            if chapters:
                for (ch,) in chapters:
                    suggestions.append(f"{book_name} {ch}")

                first_ch = chapters[0][0]
                vs_sql = """
                    SELECT DISTINCT verse
                    FROM verses
                    WHERE book = %s AND chapter = %s
                    ORDER BY verse
                    LIMIT 3
                """
                verses = execute_query(vs_sql, (book_name, first_ch))
                if verses:
                    for (vs,) in verses:
                        suggestions.append(f"{book_name} {first_ch}:{vs}")

        return suggestions[:10]


verse_service = VerseService()
