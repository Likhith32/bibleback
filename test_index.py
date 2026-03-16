import asyncio
from app.database.db import execute_query

def add_index():
    print("Adding trigram index to the verses text column...")
    query = "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
    execute_query(query, fetch_all=False)
    
    query_idx = "CREATE INDEX IF NOT EXISTS verses_text_trgm ON verses USING gin(text gin_trgm_ops);"
    execute_query(query_idx, fetch_all=False)
    print("Done adding index.")

if __name__ == '__main__':
    add_index()
