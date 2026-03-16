import json
from app.database.db import execute_query

def test():
    query = """
    SELECT
        CASE
            WHEN book LIKE '{%' THEN (book::json->>'english')
            ELSE book
        END as norm_book,
        chapter,
        verse,
        MAX(CASE WHEN LOWER(language) = 'english' THEN text END) AS english,
        MAX(CASE WHEN LOWER(language) = 'telugu'  THEN text END) AS telugu
    FROM verses
    WHERE 
        (
            book ILIKE 'John%' 
            OR (book LIKE '{%' AND (book::json->>'english') ILIKE 'John%')
        )
        AND chapter = 3 AND verse = 16
    GROUP BY norm_book, chapter, verse
    """
    rows = execute_query(query)

    with open('out3.json', 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    test()
