import asyncio
import html
import re
from typing import Any, Dict, List, Optional

import aiohttp

from config import (
    CROSSREF_MAILTO,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    SOURCE_SEARCH_TIMEOUT,
)


def clean_text(value: str, limit: int = 240) -> str:
    without_tags = re.sub(r"<[^>]+>", "", value or "")
    normalized = " ".join(html.unescape(without_tags).split())

    if len(normalized) <= limit:
        return normalized

    return normalized[: limit - 1].rstrip() + "…"


def build_query(
    title: str,
    description: Optional[str]
) -> str:
    if description:
        return f"{title} {description[:180]}"

    return title


async def search_wikipedia(
    session: aiohttp.ClientSession,
    query: str
) -> List[Dict[str, str]]:
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": 3,
        "utf8": 1,
        "format": "json",
    }

    async with session.get(
        "https://uk.wikipedia.org/w/api.php",
        params=params
    ) as response:
        response.raise_for_status()
        data = await response.json()

    results = []

    for item in data.get("query", {}).get("search", []):
        page_id = item.get("pageid")

        if not page_id:
            continue

        results.append(
            {
                "kind": "Wikipedia",
                "title": clean_text(item.get("title", "")),
                "summary": clean_text(item.get("snippet", "")),
                "url": f"https://uk.wikipedia.org/?curid={page_id}",
            }
        )

    return results


async def search_crossref(
    session: aiohttp.ClientSession,
    query: str
) -> List[Dict[str, str]]:
    params = {
        "query": query,
        "rows": 3,
        "select": "DOI,title,URL,author,container-title",
    }

    if CROSSREF_MAILTO:
        params["mailto"] = CROSSREF_MAILTO

    async with session.get(
        "https://api.crossref.org/works",
        params=params
    ) as response:
        response.raise_for_status()
        data = await response.json()

    results = []

    for item in (
        data.get("message", {}).get("items", [])
    ):
        titles = item.get("title") or []
        title = titles[0] if titles else "Наукова публікація"

        containers = item.get("container-title") or []
        container = containers[0] if containers else ""

        authors = []

        for author in item.get("author", [])[:3]:
            full_name = " ".join(
                part
                for part in [
                    author.get("given", ""),
                    author.get("family", ""),
                ]
                if part
            )

            if full_name:
                authors.append(full_name)

        details = ", ".join(authors)

        if container:
            details = (
                f"{details}. {container}"
                if details
                else container
            )

        url = item.get("URL")

        if not url:
            doi = item.get("DOI")
            url = f"https://doi.org/{doi}" if doi else ""

        if not url:
            continue

        results.append(
            {
                "kind": "Crossref",
                "title": clean_text(title),
                "summary": clean_text(details or "Наукове джерело"),
                "url": url,
            }
        )

    return results


def deduplicate_sources(
    sources: List[Dict[str, str]]
) -> List[Dict[str, str]]:
    unique = []
    seen_urls = set()

    for source in sources:
        url = source.get("url", "").strip()

        if not url or url in seen_urls:
            continue

        seen_urls.add(url)
        unique.append(source)

    return unique[:6]


def extract_openai_output(data: Dict[str, Any]) -> str:
    direct_text = data.get("output_text")

    if direct_text:
        return clean_text(str(direct_text), limit=1000)

    chunks = []

    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                text = content.get("text", "")

                if text:
                    chunks.append(text)

    return clean_text("\n".join(chunks), limit=1000)


async def create_ai_hint(
    session: aiohttp.ClientSession,
    task_title: str,
    task_description: Optional[str],
    sources: List[Dict[str, str]]
) -> Optional[str]:
    if not OPENAI_API_KEY or not OPENAI_MODEL:
        return None

    source_lines = "\n".join(
        f"- {source['title']} ({source['kind']})"
        for source in sources
    )

    prompt = (
        "Завдання користувача:\n"
        f"{task_title}\n\n"
        f"Опис: {task_description or 'немає'}\n\n"
        "Нижче наведено реальні знайдені джерела:\n"
        f"{source_lines}\n\n"
        "Українською мовою дай коротку практичну підказку "
        "до 5 речень: з чого почати, як використати ці джерела "
        "і яку просту структуру матеріалу обрати. "
        "Не вигадуй нових джерел, назв або посилань."
    )

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENAI_MODEL,
        "instructions": (
            "Ти допомагаєш планувати навчальні та дослідницькі "
            "завдання. Пиши стисло, конкретно й без вигаданих фактів."
        ),
        "input": prompt,
        "max_output_tokens": 350,
    }

    try:
        async with session.post(
            "https://api.openai.com/v1/responses",
            headers=headers,
            json=payload
        ) as response:
            if response.status >= 400:
                return None

            data = await response.json()
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return None

    return extract_openai_output(data) or None


async def find_sources(
    task_title: str,
    task_description: Optional[str]
) -> Dict[str, Any]:
    timeout = aiohttp.ClientTimeout(
        total=SOURCE_SEARCH_TIMEOUT
    )
    headers = {
        "User-Agent": (
            "TasklyTelegramBot/1.0 "
            "(educational software project)"
        )
    }

    query = build_query(task_title, task_description)

    async with aiohttp.ClientSession(
        timeout=timeout,
        headers=headers
    ) as session:
        results = await asyncio.gather(
            search_wikipedia(session, query),
            search_crossref(session, query),
            return_exceptions=True
        )

        sources = []

        for result in results:
            if isinstance(result, list):
                sources.extend(result)

        sources = deduplicate_sources(sources)

        ai_hint = None

        if sources:
            ai_hint = await create_ai_hint(
                session=session,
                task_title=task_title,
                task_description=task_description,
                sources=sources
            )

    return {
        "sources": sources,
        "ai_hint": ai_hint,
    }


def is_research_task(
    title: str,
    description: Optional[str]
) -> bool:
    text = f"{title} {description or ''}".lower()
    markers = {
        "статт",
        "реферат",
        "дослід",
        "курсова",
        "диплом",
        "презентац",
        "доповід",
        "есе",
        "аналіз",
        "джерел",
        "матеріал",
        "підготувати тему",
        "написати",
    }

    return any(marker in text for marker in markers)
