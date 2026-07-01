#!/usr/bin/env python3
"""Print match-of-day search results and parser output for tuning."""
from __future__ import annotations

import asyncio
import json
import sys

from app.services.ai.match_context import now_msk
from app.services.ai.search_enricher import SearchEnricher
from app.services.match_of_day import MatchOfDayService
from app.services.match_of_day_parser import pick_fixture_from_search


async def main() -> int:
    now = now_msk()
    svc = MatchOfDayService()
    queries = svc._build_queries(now)
    print(f"MSK now: {now.isoformat()}\n")
    print("Queries:")
    for q in queries:
        print(f"  - {q}")

    search = SearchEnricher()
    payload = await search.enrich(queries)
    print(f"\nSearch status: {payload.search_status}, results: {len(payload.results)}\n")

    for idx, item in enumerate(payload.results[:20], start=1):
        print(f"[{idx}] query={item.query[:50]}")
        print(f"    title:   {item.title[:120]}")
        print(f"    snippet: {(item.snippet or '')[:160]}")
        print(f"    url:     {item.url[:100]}")
        print()

    picked = pick_fixture_from_search(payload.results)
    print("Parser pick:")
    print(json.dumps(picked, ensure_ascii=False, indent=2) if picked else "  (none)")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
