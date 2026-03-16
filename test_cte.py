import json
from app.database.db import execute_query

def test():
    query = """
    WITH matched_verses AS (
        SELECT
            CASE
                WHEN book LIKE '{%' THEN (book::json->>'english')
                ELSE book
            END AS norm_book,
            chapter,
            verse
        FROM verses
        WHERE text ILIKE '%faith%' OR book ILIKE '%faith%' OR (book LIKE '{%' AND (book::json->>'english') ILIKE '%faith%')
        GROUP BY norm_book, chapter, verse
        LIMIT 10
    )
    SELECT
        m.norm_book,
        m.chapter,
        m.verse,
        MAX(CASE WHEN LOWER(v.language) = 'english' THEN v.text END) AS english,
        MAX(CASE WHEN LOWER(v.language) = 'telugu'  THEN v.text END) AS telugu
    FROM matched_verses m
    JOIN verses v ON 
        (
            v.book = m.norm_book 
            OR (v.book LIKE '{%' AND (v.book::json->>'english') = m.norm_book)
        )
        AND v.chapter = m.chapter
        AND v.verse = m.verse
    GROUP BY m.norm_book, m.chapter, m.verse
    ORDER BY m.chapter, m.verse
    """
    rows = execute_query(query)

    with open('out_cte.json', 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    test()
