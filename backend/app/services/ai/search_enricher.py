import asyncio
import hashlib
import json

from duckduckgo_search import DDGS

from app.core.config import settings
from app.core.redis import get_redis
from app.schemas import SearchPayload, SearchResultItem


class DuckDuckGoSearchProvider:
    async def search(self, query: str, max_results: int) -> list[SearchResultItem]:
        def _run() -> list[SearchResultItem]:
            items: list[SearchResultItem] = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    items.append(
                        SearchResultItem(
                            query=query,
                            title=r.get("title", ""),
                            snippet=r.get("body", r.get("snippet", "")),
                            url=r.get("href", r.get("link", "")),
                        )
                    )
            return items

        return await asyncio.wait_for(asyncio.to_thread(_run), timeout=3.0)


class SearXNGSearchProvider:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def search(self, query: str, max_results: int) -> list[SearchResultItem]:
        import httpx

        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(
                f"{self.base_url}/search",
                params={"q": query, "format": "json", "categories": "general"},
            )
            response.raise_for_status()
            data = response.json()
            items: list[SearchResultItem] = []
            for r in data.get("results", [])[:max_results]:
                items.append(
                    SearchResultItem(
                        query=query,
                        title=r.get("title", ""),
                        snippet=r.get("content", ""),
                        url=r.get("url", ""),
                    )
                )
            return items


def _cache_key(query: str) -> str:
    normalized = query.strip().lower()
    digest = hashlib.sha256(normalized.encode()).hexdigest()
    return f"search:v1:{digest}"


class SearchEnricher:
    def __init__(self) -> None:
        provider = settings.search_provider.lower()
        if provider == "searxng":
            self.provider = SearXNGSearchProvider(settings.searxng_base_url)
        else:
            self.provider = DuckDuckGoSearchProvider()

    async def enrich(self, queries: list[str]) -> SearchPayload:
        queries = [q.strip() for q in queries if q.strip()][: settings.search_max_queries]
        if not queries:
            return SearchPayload(search_status="failed")

        redis = await get_redis()
        all_results: list[SearchResultItem] = []
        executed: list[str] = []
        partial = False

        for query in queries:
            cache_key = _cache_key(query)
            cached = await redis.get(cache_key)
            if cached:
                for item in json.loads(cached):
                    all_results.append(SearchResultItem(**item))
                executed.append(query)
                continue
            try:
                results = await self.provider.search(query, settings.search_max_results)
                await redis.setex(
                    cache_key,
                    settings.search_cache_ttl_seconds,
                    json.dumps([r.model_dump() for r in results]),
                )
                all_results.extend(results)
                executed.append(query)
            except Exception:
                partial = True

        if not all_results:
            return SearchPayload(queries_executed=executed, search_status="failed")
        status = "partial" if partial else "ok"
        return SearchPayload(queries_executed=executed, results=all_results, search_status=status)
