"""
J.A.R.V.I.S. Public API Integrations
-------------------------------------
Zero-configuration public APIs — no API keys required.
Powered by the public-apis/public-apis collection.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

import aiohttp

logger = logging.getLogger("jarvis.public_apis")

# ──────────────────────────────────────────────────────────────
# Shared HTTP session helpers
# ──────────────────────────────────────────────────────────────

_SESSION: Optional[aiohttp.ClientSession] = None
_SESSION_LOCK = asyncio.Lock()


async def _get_session() -> aiohttp.ClientSession:
    global _SESSION
    if _SESSION is None or _SESSION.closed:
        async with _SESSION_LOCK:
            if _SESSION is None or _SESSION.closed:
                _SESSION = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=15),
                    headers={"User-Agent": "JARVIS-Agent/1.0"},
                )
    return _SESSION


async def _fetch_json(url: str, params: Optional[Dict] = None) -> Optional[Dict]:
    """GET a URL and return parsed JSON, or None on failure."""
    session = await _get_session()
    try:
        async with session.get(url, params=params) as resp:
            if resp.status == 200:
                return await resp.json()
            logger.warning("API %s returned %s", url, resp.status)
            return None
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        logger.warning("API %s failed: %s", url, e)
        return None


async def _fetch_text(url: str) -> Optional[str]:
    """GET a URL and return raw text, or None on failure."""
    session = await _get_session()
    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.text()
            return None
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        logger.warning("API %s failed: %s", url, e)
        return None


async def close_session():
    """Gracefully close the shared aiohttp session."""
    global _SESSION
    if _SESSION and not _SESSION.closed:
        await _SESSION.close()


# ══════════════════════════════════════════════════════════════
# 1. CoinGecko — Cryptocurrency prices
# ══════════════════════════════════════════════════════════════

_BASE_COINGECKO = "https://api.coingecko.com/api/v3"


async def crypto_price(coin_id: str = "bitcoin", vs_currency: str = "usd") -> Dict[str, Any]:
    """Get current cryptocurrency price and 24h change."""
    url = f"{_BASE_COINGECKO}/simple/price"
    params = {
        "ids": coin_id.lower(),
        "vs_currencies": vs_currency.lower(),
        "include_24hr_change": "true",
        "include_market_cap": "true",
    }
    data = await _fetch_json(url, params)
    if not data or coin_id.lower() not in data:
        return {"error": f"Coin '{coin_id}' not found", "hint": "Try: bitcoin, ethereum, solana, dogecoin, cardano"}

    info = data[coin_id.lower()]
    return {
        "coin": coin_id,
        "price": info.get(vs_currency.lower(), 0),
        "change_24h": info.get(f"{vs_currency.lower()}_24h_change", 0),
        "market_cap": info.get(f"{vs_currency.lower()}_market_cap", 0),
        "currency": vs_currency.upper(),
        "_service": "CoinGecko",
    }


async def crypto_list() -> List[Dict[str, Any]]:
    """List top 10 cryptocurrencies."""
    url = f"{_BASE_COINGECKO}/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 10, "page": 1}
    data = await _fetch_json(url, params)
    if not data:
        return [{"error": "Failed to fetch market data"}]
    return [
        {
            "rank": c["market_cap_rank"],
            "name": c["name"],
            "symbol": c["symbol"].upper(),
            "price": c["current_price"],
            "change_24h": c["price_change_percentage_24h"],
            "market_cap": c["market_cap"],
        }
        for c in data
    ]


# ══════════════════════════════════════════════════════════════
# 2. Frankfurter — Currency exchange rates
# ══════════════════════════════════════════════════════════════

_BASE_FRANKFURTER = "https://api.frankfurter.dev"


async def exchange_rate(from_currency: str, to_currency: str, amount: float = 1.0) -> Dict[str, Any]:
    """Convert an amount between currencies."""
    url = f"{_BASE_FRANKFURTER}/latest"
    params = {
        "from": from_currency.upper(),
        "to": to_currency.upper(),
    }
    data = await _fetch_json(url, params)
    if not data:
        return {"error": f"Exchange rate lookup failed for {from_currency} → {to_currency}"}

    rates = data.get("rates", {})
    rate = rates.get(to_currency.upper())
    if rate is None:
        return {"error": f"Currency '{to_currency}' not supported", "hint": "Try: USD, EUR, GBP, JPY, CNY, KRW"}

    return {
        "from": from_currency.upper(),
        "to": to_currency.upper(),
        "rate": rate,
        "amount": amount,
        "result": round(amount * rate, 2),
        "date": data.get("date", ""),
        "_service": "Frankfurter",
    }


async def exchange_supported_currencies() -> Dict[str, Any]:
    """List all supported currencies."""
    url = f"{_BASE_FRANKFURTER}/currencies"
    data = await _fetch_json(url)
    if not data:
        return {"error": "Failed to fetch supported currencies"}
    return {"currencies": data, "count": len(data), "_service": "Frankfurter"}


# ══════════════════════════════════════════════════════════════
# 3. Free Dictionary API
# ══════════════════════════════════════════════════════════════

_BASE_DICT = "https://api.dictionaryapi.dev/api/v2/entries/en"


async def dictionary_lookup(word: str) -> Dict[str, Any]:
    """Look up an English word definition, pronunciation, and examples."""
    url = f"{_BASE_DICT}/{word.lower().strip()}"
    data = await _fetch_json(url)
    if not data or not isinstance(data, list) or len(data) == 0:
        return {"error": f"Word '{word}' not found in dictionary"}

    entry = data[0]
    meanings = entry.get("meanings", [])
    phonetics = entry.get("phonetics", [])

    # Get phonetic text and audio
    phonetic_text = entry.get("phonetic", "")
    audio_url = ""
    for p in phonetics:
        if p.get("audio"):
            audio_url = p["audio"]
            if not phonetic_text:
                phonetic_text = p.get("text", "")
            break

    # Extract definitions grouped by part of speech
    definitions_by_pos = {}
    for m in meanings:
        pos = m.get("partOfSpeech", "unknown")
        defs = []
        for d in m.get("definitions", [])[:3]:  # max 3 per part of speech
            defs.append(
                {
                    "definition": d.get("definition", ""),
                    "example": d.get("example", ""),
                }
            )
        definitions_by_pos[pos] = defs

    return {
        "word": entry.get("word", word),
        "phonetic": phonetic_text,
        "audio_url": audio_url,
        "definitions": definitions_by_pos,
        "total_meanings": len(meanings),
        "_service": "Free Dictionary API",
    }


# ══════════════════════════════════════════════════════════════
# 4. Nager.Date — Public holidays
# ══════════════════════════════════════════════════════════════

_BASE_NAGER = "https://date.nager.at/api/v3"


async def public_holidays(year: int, country_code: str = "CN") -> Dict[str, Any]:
    """Get public holidays for a given year and country."""
    url = f"{_BASE_NAGER}/publicholidays/{year}/{country_code.upper()}"
    data = await _fetch_json(url)
    if not data:
        return {"error": f"No holiday data for {country_code} in {year}", "hint": "Try: CN, US, JP, GB, KR, HK"}

    holidays = [
        {
            "date": h.get("date", ""),
            "name": h.get("localName", h.get("name", "")),
            "global": h.get("global", True),
            "types": h.get("types", []),
        }
        for h in data
    ]

    # Filter upcoming holidays (from today)
    today = datetime.now().strftime("%Y-%m-%d")
    upcoming = [h for h in holidays if h["date"] >= today][:5]

    return {
        "country": country_code.upper(),
        "year": year,
        "total_holidays": len(holidays),
        "holidays": holidays,
        "upcoming": upcoming,
        "_service": "Nager.Date",
    }


async def next_public_holidays(country_code: str = "CN") -> Dict[str, Any]:
    """Get the next upcoming public holidays."""
    today = datetime.now()
    # Try current year and next
    result = await public_holidays(today.year, country_code)
    if "error" in result:
        return result
    if not result.get("upcoming"):
        # Try next year
        result = await public_holidays(today.year + 1, country_code)
    return result


async def country_list() -> Dict[str, Any]:
    """List available countries for holiday data."""
    url = f"{_BASE_NAGER}/availableCountries"
    data = await _fetch_json(url)
    if not data:
        return {"error": "Failed to fetch country list"}

    countries = [{"code": c["countryCode"], "name": c["name"]} for c in data]
    return {"countries": countries, "count": len(countries), "_service": "Nager.Date"}


# ══════════════════════════════════════════════════════════════
# 5. JokeAPI — Multi-language jokes
# ══════════════════════════════════════════════════════════════

_BASE_JOKE = "https://v2.jokeapi.dev/joke"


async def tell_joke(
    category: str = "Any",
    lang: str = "en",
    blacklist: str = "nsfw,explicit",
) -> Dict[str, Any]:
    """Get a random joke. Categories: Any, Programming, Misc, Dark, Pun, Spooky, Christmas."""
    url = f"{_BASE_JOKE}/{category}"
    params = {
        "lang": lang,
        "blacklistFlags": blacklist,
        "safe-mode": "",
    }
    data = await _fetch_json(url, params)
    if not data or data.get("error", False):
        return {"error": "Failed to fetch joke", "hint": "Try categories: Programming, Misc, Dark, Pun, Any"}

    if data.get("type") == "twopart":
        return {
            "setup": data.get("setup", ""),
            "delivery": data.get("delivery", ""),
            "category": data.get("category", ""),
            "type": "twopart",
            "safe": data.get("safe", True),
            "_service": "JokeAPI",
        }
    else:
        return {
            "joke": data.get("joke", ""),
            "category": data.get("category", ""),
            "type": "single",
            "safe": data.get("safe", True),
            "_service": "JokeAPI",
        }


# ══════════════════════════════════════════════════════════════
# 6. Open Library — Book search
# ══════════════════════════════════════════════════════════════

_BASE_OL = "https://openlibrary.org"


async def search_books(query: str, limit: int = 5) -> Dict[str, Any]:
    """Search for books by title, author, or ISBN."""
    url = f"{_BASE_OL}/search.json"
    params = {"q": query, "limit": min(limit, 20), "fields": "title,author_name,first_publish_year,isbn,cover_i,key"}
    data = await _fetch_json(url, params)
    if not data:
        return {"error": f"Book search failed for '{query}'"}

    docs = data.get("docs", [])
    books = []
    for d in docs[:limit]:
        cover_id = d.get("cover_i")
        books.append(
            {
                "title": d.get("title", "Unknown"),
                "author": ", ".join(d.get("author_name", ["Unknown"])),
                "year": d.get("first_publish_year"),
                "isbn": d.get("isbn", [None])[0] if d.get("isbn") else None,
                "cover_url": f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else None,
                "url": f"https://openlibrary.org{d.get('key', '')}" if d.get("key") else None,
            }
        )

    return {
        "query": query,
        "total_found": data.get("numFound", 0),
        "books": books,
        "_service": "Open Library",
    }


async def book_by_isbn(isbn: str) -> Dict[str, Any]:
    """Look up a book by its ISBN number."""
    url = f"{_BASE_OL}/api/books"
    params = {"bibkeys": f"ISBN:{isbn}", "format": "json", "jscmd": "data"}
    data = await _fetch_json(url, params)
    if not data:
        return {"error": f"ISBN '{isbn}' not found"}

    key = f"ISBN:{isbn}"
    info = data.get(key, {})
    if not info:
        return {"error": f"ISBN '{isbn}' not found"}

    return {
        "title": info.get("title", ""),
        "authors": [a.get("name", "") for a in info.get("authors", [])],
        "publish_date": info.get("publish_date", ""),
        "pages": info.get("number_of_pages"),
        "cover": info.get("cover", {}).get("medium") or info.get("cover", {}).get("large"),
        "url": info.get("url"),
        "_service": "Open Library",
    }


# ══════════════════════════════════════════════════════════════
# Convenience: get all public API capabilities as a list
# ══════════════════════════════════════════════════════════════

PUBLIC_API_DESCRIPTIONS = {
    "crypto_price": {
        "description": "Get cryptocurrency price and 24h change",
        "params": {"coin_id": "str (e.g. bitcoin, ethereum)", "vs_currency": "str (e.g. usd, cny)"},
        "example": 'crypto_price("bitcoin", "usd")',
    },
    "crypto_list": {
        "description": "List top 10 cryptocurrencies by market cap",
        "params": {},
        "example": "crypto_list()",
    },
    "exchange_rate": {
        "description": "Convert between currencies",
        "params": {"from_currency": "str", "to_currency": "str", "amount": "float"},
        "example": 'exchange_rate("USD", "CNY", 100)',
    },
    "dictionary_lookup": {
        "description": "Look up English word definition, phonetic, examples",
        "params": {"word": "str"},
        "example": 'dictionary_lookup("serendipity")',
    },
    "public_holidays": {
        "description": "Get public holidays for a country and year",
        "params": {"year": "int", "country_code": "str (ISO 3166-1 alpha-2)"},
        "example": 'public_holidays(2026, "CN")',
    },
    "next_public_holidays": {
        "description": "Get next upcoming public holidays",
        "params": {"country_code": "str"},
        "example": 'next_public_holidays("CN")',
    },
    "tell_joke": {
        "description": "Get a random joke (safe mode on)",
        "params": {"category": "str (Any/Programming/Misc/Dark/Pun)", "lang": "str (en/de/es)"},
        "example": 'tell_joke("Programming", "en")',
    },
    "search_books": {
        "description": "Search for books by title/author",
        "params": {"query": "str", "limit": "int"},
        "example": 'search_books("Three Body Problem", 5)',
    },
    "book_by_isbn": {
        "description": "Look up a book by ISBN",
        "params": {"isbn": "str"},
        "example": 'book_by_isbn("9787559634603")',
    },
}
