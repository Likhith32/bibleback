import asyncio
import json
from app.services.search_service import search_service

async def test():
    out = {}
    r4, qtype4 = await search_service.parse_query_and_search("hope")
    out['hope'] = r4

    r5, qtype5 = await search_service.parse_query_and_search("grace")
    out['grace'] = r5

    with open('test_search_out2.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    asyncio.run(test())
