from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import urljoin

import pytz
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

from feed_generators.utils import fetch_page, get_project_root, save_rss_feed, setup_feed_links, setup_logging

logger = setup_logging()


def fetch_blog_content(url: str, local_file_name: str | None = None) -> str:
    """Fetch page content from a local file for development or from the URL."""
    project_root = get_project_root()
    local_candidates = []
    if local_file_name:
        local_candidates.append(project_root / local_file_name)
    local_candidates.extend([project_root / "index.html", project_root / "page.html"])

    for local_path in local_candidates:
        if local_path.exists():
            logger.info("Reading from local file for development: %s", local_path)
            with open(local_path, encoding="utf-8") as f:
                return f.read()

    try:
        logger.info("Fetching blog content from URL: %s", url)
        return fetch_page(url)
    except Exception as exc:
        logger.error("Error fetching blog content: %s", exc)
        raise


def parse_blog_html(html_content: str, selectors: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse blog posts from HTML using configurable CSS selectors."""
    soup = BeautifulSoup(html_content, "html.parser")
    posts: list[dict[str, Any]] = []

    articles = soup.select(selectors["article_selector"])
    for article in articles:
        title_elem = article.select_one(selectors["title_selector"])
        if not title_elem:
            continue
        title = title_elem.get_text(" ", strip=True)

        link_elem = article.select_one(selectors["link_selector"])
        if not link_elem:
            continue
        link_value = link_elem.get("href") or ""
        if link_value.startswith("/"):
            base_url = selectors.get("base_url", "")
            link_value = urljoin(base_url, link_value)
        elif link_value and not link_value.startswith(("http://", "https://")):
            link_value = urljoin(selectors.get("base_url", ""), link_value)

        description_elem = article.select_one(selectors.get("description_selector", "p"))
        description = description_elem.get_text(" ", strip=True) if description_elem else title

        date_elem = article.select_one(selectors.get("date_selector", "time"))
        date_obj = None
        if date_elem:
            date_value = date_elem.get(selectors.get("date_attr", "datetime")) or date_elem.get_text(" ", strip=True)
            if date_value:
                date_format = selectors.get("date_format")
                if date_format:
                    try:
                        date_obj = datetime.strptime(date_value, date_format)
                    except ValueError:
                        date_obj = None
                if date_obj is None:
                    try:
                        date_obj = datetime.fromisoformat(date_value.split("T")[0])
                    except ValueError:
                        date_obj = None

        if date_obj is None:
            date_obj = datetime.now(pytz.UTC)
        else:
            date_obj = date_obj.replace(tzinfo=pytz.UTC)

        posts.append(
            {
                "title": title,
                "date": date_obj,
                "description": description,
                "link": link_value,
            }
        )

    return posts


def generate_rss_feed(blog_posts: list[dict[str, Any]], feed_name: str, title: str, description: str, blog_url: str) -> FeedGenerator:
    """Generate a feed from a list of parsed posts."""
    fg = FeedGenerator()
    fg.title(title)
    fg.description(description)
    setup_feed_links(fg, blog_url, feed_name)
    fg.language("de")
    fg.author({"name": title})

    for post in blog_posts:
        fe = fg.add_entry()
        fe.title(post["title"])
        fe.description(post["description"])
        fe.link(href=post["link"])
        fe.published(post["date"])
        fe.id(post["link"])

    return fg


def generate_feed_from_config(config: dict[str, Any]) -> bool:
    """Generate one feed from a config dictionary."""
    html_content = fetch_blog_content(config["blog_url"], config.get("local_file_name"))
    blog_posts = parse_blog_html(html_content, config["selectors"])
    if not blog_posts:
        logger.warning("No posts found for %s", config["feed_name"])
        return False

    feed = generate_rss_feed(
        blog_posts,
        config["feed_name"],
        config["title"],
        config["description"],
        config["blog_url"],
    )
    save_rss_feed(feed, config["feed_name"])
    return True
