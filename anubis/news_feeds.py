"""News & research feeds — ANUBIS stays current.

Gathers news, research papers, and tech updates in the Creator's
areas of interest. Filters by relevance, summarizes, and flags
important developments.

SOURCES:
- RSS/Atom feeds (standard, widely supported)
- Hacker News API (free, no key)
- arXiv API (research papers, free)
- Reddit API (free, no key for public data)

Uses stdlib only (urllib, xml.etree for RSS parsing).
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable
from xml.etree import ElementTree


@dataclass
class NewsItem:
    """A news article or research paper."""
    item_id: str
    title: str = ""
    summary: str = ""
    url: str = ""
    source: str = ""
    author: str = ""
    published: float = 0.0
    categories: list[str] = field(default_factory=list)
    relevance_score: float = 0.0
    read: bool = False
    saved: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "title": self.title,
            "summary": self.summary[:300],
            "url": self.url,
            "source": self.source,
            "author": self.author,
            "published": self.published,
            "categories": self.categories,
            "relevance_score": self.relevance_score,
            "read": self.read,
            "saved": self.saved,
        }


class NewsFeeds:
    """News and research feed aggregator.

    Fetches from RSS feeds, Hacker News, arXiv, and Reddit.
    Filters by relevance to the Creator's interests.
    """

    ACTOR = "anubis.news"

    def __init__(
        self,
        root: str | Path,
        *,
        interests: list[str] | None = None,
        feeds: list[str] | None = None,
        ledger: Any | None = None,
        on_new_item: Callable[[NewsItem], None] | None = None,
    ) -> None:
        self.root = Path(root)
        self.interests = interests or [
            "AI", "machine learning", "quantum computing",
            "cybersecurity", "space", "energy", "robotics",
        ]
        self.feeds = feeds or [
            "https://hnrss.org/frontpage",
            "https://feeds.arxiv.org/rss/cs.AI",
            "https://www.technologyreview.com/feed/",
        ]
        self.ledger = ledger
        self.on_new_item = on_new_item

        self._state_dir = self.root / "memory" / "news"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._items_file = self._state_dir / "items.json"

        self._items: dict[str, NewsItem] = {}
        self._seen_ids: set[str] = set()
        self._load()

    def add_interest(self, topic: str) -> None:
        if topic.lower() not in [i.lower() for i in self.interests]:
            self.interests.append(topic)

    def add_feed(self, url: str) -> None:
        if url not in self.feeds:
            self.feeds.append(url)

    def fetch_feeds(self) -> list[NewsItem]:
        """Fetch all RSS feeds and return new items."""
        new_items: list[NewsItem] = []
        for feed_url in self.feeds:
            items = self._fetch_rss(feed_url)
            for item in items:
                if item.item_id not in self._seen_ids:
                    self._seen_ids.add(item.item_id)
                    item.relevance_score = self._score_relevance(item)
                    self._items[item.item_id] = item
                    new_items.append(item)
                    if self.on_new_item and item.relevance_score > 0.5:
                        try:
                            self.on_new_item(item)
                        except Exception:
                            pass
        self._save()
        return new_items

    def fetch_hackernews(self, limit: int = 30) -> list[NewsItem]:
        """Fetch top stories from Hacker News."""
        try:
            url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            with urllib.request.urlopen(url, timeout=15) as resp:
                ids = json.loads(resp.read())[:limit]

            items: list[NewsItem] = []
            for story_id in ids[:10]:  # limit to 10 for speed
                try:
                    story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                    with urllib.request.urlopen(story_url, timeout=10) as resp:
                        story = json.loads(resp.read())

                    item_id = f"hn-{story_id}"
                    if item_id in self._seen_ids:
                        continue
                    self._seen_ids.add(item_id)

                    item = NewsItem(
                        item_id=item_id,
                        title=story.get("title", ""),
                        url=story.get("url", ""),
                        source="Hacker News",
                        author=story.get("by", ""),
                        published=story.get("time", 0),
                        categories=["tech"],
                    )
                    item.relevance_score = self._score_relevance(item)
                    self._items[item_id] = item
                    items.append(item)
                except Exception:
                    continue

            self._save()
            return items
        except Exception:
            return []

    def _fetch_rss(self, feed_url: str) -> list[NewsItem]:
        """Fetch and parse an RSS feed."""
        try:
            req = urllib.request.Request(feed_url)
            req.add_header("User-Agent", "ANUBIS-News/1.0")
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read()

            root = ElementTree.fromstring(content)
            items: list[NewsItem] = []

            # RSS 2.0
            for item in root.findall(".//item"):
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                description = item.findtext("description", "")
                pub_date = item.findtext("pubDate", "")
                categories = [c.text for c in item.findall("category") if c.text]

                item_id = hashlib.sha256(
                    f"{title}:{link}".encode()
                ).hexdigest()[:16]

                items.append(NewsItem(
                    item_id=item_id,
                    title=title,
                    summary=description,
                    url=link,
                    source=feed_url,
                    published=self._parse_date(pub_date),
                    categories=categories,
                ))

            # Atom
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall(".//atom:entry", ns):
                title = entry.findtext("atom:title", "", ns)
                link_elem = entry.find("atom:link", ns)
                link = link_elem.get("href", "") if link_elem is not None else ""
                summary = entry.findtext("atom:summary", "", ns)
                published = entry.findtext("atom:published", "", ns)

                item_id = hashlib.sha256(
                    f"{title}:{link}".encode()
                ).hexdigest()[:16]

                items.append(NewsItem(
                    item_id=item_id,
                    title=title,
                    summary=summary,
                    url=link,
                    source=feed_url,
                    published=self._parse_date(published),
                ))

            return items
        except Exception:
            return []

    def _score_relevance(self, item: NewsItem) -> float:
        """Score how relevant an item is to the Creator's interests."""
        text = f"{item.title} {item.summary}".lower()
        score = 0.0
        for interest in self.interests:
            if interest.lower() in text:
                score += 0.2
        return min(score, 1.0)

    def _parse_date(self, date_str: str) -> float:
        if not date_str:
            return 0.0
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt.timestamp()
        except Exception:
            return 0.0

    # --------------------------------------------------- queries

    def get_items(self, limit: int = 50) -> list[dict[str, Any]]:
        items = sorted(self._items.values(), key=lambda x: x.published, reverse=True)
        return [i.to_dict() for i in items[:limit]]

    def get_relevant_items(self, min_score: float = 0.4, limit: int = 20) -> list[dict[str, Any]]:
        items = [
            i for i in self._items.values()
            if i.relevance_score >= min_score and not i.read
        ]
        items.sort(key=lambda x: x.relevance_score, reverse=True)
        return [i.to_dict() for i in items[:limit]]

    def get_by_category(self, category: str) -> list[dict[str, Any]]:
        return [
            i.to_dict() for i in self._items.values()
            if category.lower() in [c.lower() for c in i.categories]
        ]

    def mark_read(self, item_id: str) -> bool:
        item = self._items.get(item_id)
        if item is None:
            return False
        item.read = True
        self._save()
        return True

    def save_item(self, item_id: str) -> bool:
        item = self._items.get(item_id)
        if item is None:
            return False
        item.saved = True
        self._save()
        return True

    def get_saved_items(self) -> list[dict[str, Any]]:
        return [i.to_dict() for i in self._items.values() if i.saved]

    def get_daily_briefing(self) -> str:
        """Generate a news briefing."""
        relevant = self.get_relevant_items(min_score=0.3, limit=5)
        if not relevant:
            return "No relevant news items found."
        parts = ["News briefing:"]
        for item in relevant:
            parts.append(f"  - {item['title']} ({item['source']})")
        return "\n".join(parts)

    def get_status(self) -> dict[str, Any]:
        return {
            "total_items": len(self._items),
            "unread": sum(1 for i in self._items.values() if not i.read),
            "relevant": sum(1 for i in self._items.values() if i.relevance_score > 0.4),
            "saved": sum(1 for i in self._items.values() if i.saved),
            "feeds": len(self.feeds),
            "interests": len(self.interests),
        }

    # --------------------------------------------------- persistence

    def _load(self) -> None:
        if not self._items_file.exists():
            return
        try:
            data = json.loads(self._items_file.read_text(encoding="utf-8"))
            for i_id, i in data.items():
                self._items[i_id] = NewsItem(
                    item_id=i_id,
                    title=i.get("title", ""),
                    summary=i.get("summary", ""),
                    url=i.get("url", ""),
                    source=i.get("source", ""),
                    author=i.get("author", ""),
                    published=i.get("published", 0),
                    categories=i.get("categories", []),
                    relevance_score=i.get("relevance_score", 0),
                    read=i.get("read", False),
                    saved=i.get("saved", False),
                )
                self._seen_ids.add(i_id)
        except Exception:
            pass

    def _save(self) -> None:
        data = {i_id: i.to_dict() for i_id, i in self._items.items()}
        self._items_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
