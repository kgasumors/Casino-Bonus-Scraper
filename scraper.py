import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

SOURCE_URL = os.getenv("SOURCE_URL", "https://betproof.co.za/casino-bonuses-south-africa/")
OUTPUT_FILE = Path(os.getenv("OUTPUT_FILE", "src/data/bonuses.json"))
CASINO_COUNT = 3

# LLM settings: you can set LLM_BASE_URL to a custom endpoint if you have a proxy or local LLM server.
LLM_BASE_URL = os.getenv(
    "LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai").rstrip("/")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.6-flash")
LLM_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY", "")

USER_AGENT = "BonusResearchBot/1.0 (public research scraper)"
HEADERS = {"User-Agent": USER_AGENT}
FIELDS = ["casino_name", "bonus_offer", "wagering_requirement", "minimum_deposit"]

# ---------- Utilities ----------
def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


# ---------- Fetching (robots.txt respected, no bypassing) ----------

def check_robots(url: str) -> None:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        response = requests.get(robots_url, headers=HEADERS, timeout=15)
    except requests.RequestException as exc:
        raise RuntimeError(f"Cannot check robots.txt: {exc}") from exc

    if response.status_code != 200:
        raise RuntimeError(f"robots.txt returned HTTP {response.status_code}; stopping.")

    parser = RobotFileParser()
    parser.set_url(robots_url)
    parser.parse(response.text.splitlines())
    if not parser.can_fetch(USER_AGENT, url):
        raise RuntimeError("robots.txt disallows scraping this URL. Switch source.")


def fetch_page(url: str) -> BeautifulSoup:
    check_robots(url)
    response = requests.get(url, headers=HEADERS, timeout=20)
    if response.status_code in (401, 403, 429):
        raise RuntimeError(f"Source blocked us (HTTP {response.status_code}). Switch source.")
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


# ---------- Step 1: pull raw free-text rows from the table ----------

def casino_name_from_cell(cell) -> str:
    for a in cell.find_all("a"):
        text = clean_text(a.get_text(" ", strip=True))
        if text and not text.lower().startswith("play"):
            return text
    return clean_text(re.sub(r"Play\s*→", "", cell.get_text(" ", strip=True)))


def extract_raw_rows(soup: BeautifulSoup) -> list[dict]:
    table = soup.select_one("table.bonus-table")
    if table is None:
        raise RuntimeError("Could not find <table class='bonus-table'>.")

    header_cells = table.select("thead th") or table.select("tr:first-child th")
    headers = [clean_text(th.get_text(" ", strip=True)).lower() for th in header_cells]
    needed = ("casino", "bonus", "wagering", "min deposit")
    for name in needed:
        if name not in headers:
            raise RuntimeError(f"Table column '{name}' not found. Headers: {headers}")

    idx = {name: headers.index(name) for name in needed}
    rows = table.select("tbody tr") or table.select("tr")[1:]

    raw = []
    for row in rows:
        cells = row.find_all(["td", "th"])
        if len(cells) < len(headers):
            continue
        raw.append({
            "casino": casino_name_from_cell(cells[idx["casino"]]),
            "bonus_text": clean_text(cells[idx["bonus"]].get_text(" ", strip=True)),
            "wagering_text": clean_text(cells[idx["wagering"]].get_text(" ", strip=True)),
            "min_deposit_text": clean_text(cells[idx["min deposit"]].get_text(" ", strip=True)),
        })
        if len(raw) == CASINO_COUNT:
            break

    if len(raw) != CASINO_COUNT:
        raise RuntimeError(f"Expected {CASINO_COUNT} rows, parsed {len(raw)}.")
    return raw


# ---------- Step 2: free LLM turns free text into structured fields ----------

SYSTEM_PROMPT = """You convert free-text casino bonus terms into clean structured data.

You receive a JSON array of casinos, each with raw text for the bonus, wagering and minimum deposit.
Respond with ONLY a JSON object of the form {"casinos": [ ... ]} (no markdown, no commentary).
The array must have the same order and length as the input, one object per casino with exactly these keys:
- casino_name: copy the "casino" value exactly.
- bonus_offer: the welcome offer as a short, tidy phrase (e.g. "R25 sign-up + 50 free spins").
- wagering_requirement: the wagering terms as a short phrase, keeping any split by bonus type
  (e.g. "1x sports / 10x spins").
- minimum_deposit: the minimum deposit including currency symbol (e.g. "R10").

Use only information present in the input. Never invent or infer numbers. Use null for anything not stated."""


def call_llm(raw_rows: list[dict]) -> str:
    payload = {
        "model": LLM_MODEL,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(raw_rows, ensure_ascii=False)},
        ],
    }
    headers = {"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"}

    for attempt in range(3):
        response = requests.post(
            f"{LLM_BASE_URL}/chat/completions", headers=headers, json=payload, timeout=60
        )
        if response.status_code == 429 and attempt < 2:  # free tiers rate-limit; wait and retry
            time.sleep(5 * (attempt + 1))
            continue
        if not response.ok:
            raise RuntimeError(f"LLM API error {response.status_code}: {response.text[:300]}")
        return response.json()["choices"][0]["message"]["content"]

    raise RuntimeError("LLM API rate-limited after retries.")


def structure_with_llm(raw_rows: list[dict]) -> list[dict]:
    if not LLM_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set.")

    text = call_llm(raw_rows).strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Model did not return valid JSON: {text[:300]}") from exc

    items = parsed.get("casinos") if isinstance(parsed, dict) else parsed
    if not isinstance(items, list) or len(items) != len(raw_rows):
        raise RuntimeError("Model returned the wrong number of records.")

    results = []
    for raw, item in zip(raw_rows, items):
        if not isinstance(item, dict) or set(item) != set(FIELDS):
            raise RuntimeError(f"Model returned unexpected keys: {item}")
        if item["casino_name"] != raw["casino"]:
            raise RuntimeError(f"Casino name mismatch: {item['casino_name']!r} vs {raw['casino']!r}")
        results.append({k: item[k] for k in FIELDS})
    return results


# ---------- Main ----------

def main() -> None:
    try:
        soup = fetch_page(SOURCE_URL)
        raw_rows = extract_raw_rows(soup)
        casinos = structure_with_llm(raw_rows)

        output = {
            "source_url": SOURCE_URL,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "casinos": casinos,
        }

        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_FILE.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

        print(f"Saved {len(casinos)} casinos to {OUTPUT_FILE}")
        print(json.dumps(casinos, indent=2, ensure_ascii=False))
    except Exception as exc:
        sys.exit(f"Scraper stopped: {exc}")


if __name__ == "__main__":
    main()