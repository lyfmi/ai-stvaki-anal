import asyncio
import hashlib
import json
import logging

from duckduckgo_search import DDGS

from app.core.config import settings
from app.core.redis import get_redis
from app.schemas import SearchPayload, SearchResultItem

logger = logging.getLogger(__name__)


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

        return await asyncio.wait_for(asyncio.to_thread(_run), timeout=8.0)


class SearXNGSearchProvider:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def search(self, query: str, max_results: int) -> list[SearchResultItem]:
        import httpx

        async with httpx.AsyncClient(timeout=8.0) as client:
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
                        snippet=r.get("content", r.get("snippet", "")),
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
        self.searxng = SearXNGSearchProvider(settings.searxng_base_url)
        self.ddg = DuckDuckGoSearchProvider()
        preferred = settings.search_provider.lower()
        if preferred == "duckduckgo":
            self.providers = [self.ddg, self.searxng]
        else:
            self.providers = [self.searxng, self.ddg]

    async def _search_query(self, query: str, max_results: int) -> list[SearchResultItem]:
        last_error: Exception | None = None
        for provider in self.providers:
            name = type(provider).__name__
            try:
                results = await provider.search(query, max_results)
                if results:
                    return results
                logger.warning("Search provider %s returned no results for: %s", name, query)
            except Exception as exc:
                last_error = exc
                logger.warning("Search provider %s failed for %s: %s", name, query, exc)
        if last_error:
            raise last_error
        return []

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
                results = await self._search_query(query, settings.search_max_results)
                if results:
                    await redis.setex(
                        cache_key,
                        settings.search_cache_ttl_seconds,
                        json.dumps([r.model_dump() for r in results]),
                    )
                    all_results.extend(results)
                    executed.append(query)
                else:
                    partial = True
            except Exception as exc:
                logger.error("All search providers failed for %s: %s", query, exc)
                partial = True

        if not all_results:
            return SearchPayload(queries_executed=executed, search_status="failed")
        status = "partial" if partial else "ok"
        return SearchPayload(queries_executed=executed, results=all_results, search_status=status)
