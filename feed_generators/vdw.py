from contextlib import suppress
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import pytz
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

if __package__ in {None, ""}:
    import sys

    sys.path.append(str(Path(__file__).resolve().parent.parent))

from feed_generators.utils import fetch_page, get_project_root, save_rss_feed, setup_feed_links

FEED_NAME = "wirtschaftsarchive"
BLOG_URL = "https://www.wirtschaftsarchive.de/aktuelles/mitteilungen/"
LOCAL_FILE_NAME = "wirtschaftsarchive_mitteilungen.htm"


def fetch_blog_content(url=BLOG_URL):
    project_root = get_project_root()
    local_files = [project_root / LOCAL_FILE_NAME, project_root / "wirtschaftsarchive.htm"]

    for local_path in local_files:
        if local_path.exists():
            print(f"Reading from local file for development: {local_path}")
            with open(local_path, encoding="utf-8") as f:
                return f.read()

    try:
        print(f"Fetching blog content from URL: {url}")
        return fetch_page(url)
    except Exception as e:
        print(f"Error fetching blog content: {e}")
        raise


def parse_blog_html(html_content):
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        blog_posts = []

        # Gezielt nur Artikel der News-Liste erfassen
        articles = soup.select("article.news-teaser")
        if not articles:
            articles = soup.select(".news-list__item, .news-teaser")

        for article in articles:
            # 1. Titel & Kategorie
            headline_elem = article.select_one(".news-teaser__headline") or article.select_one("h3, h2")
            if not headline_elem:
                continue

            title = headline_elem.get_text(strip=True)

            category_elem = article.select_one(".news-teaser__category")
            if category_elem and category_elem.get_text(strip=True):
                category = category_elem.get_text(strip=True)
                title = f"[{category}] {title}"

            # 2. Datum aus <time> lesen
            date_elem = article.select_one("time.news-teaser__datetime") or article.select_one("time")
            date_obj = None

            if date_elem:
                # Versuch A: Aus dem 'datetime'-Attribut (z. B. "2026-07-14")
                if date_elem.get("datetime"):
                    with suppress(ValueError):
                        dt_str = date_elem["datetime"].split("T")[0]
                        date_obj = datetime.strptime(dt_str, "%Y-%m-%d").replace(tzinfo=pytz.UTC)

                # Versuch B: Aus dem HTML-Inhalt (z. B. "14.07.2026")
                if not date_obj:
                    with suppress(ValueError):
                        date_text = date_elem.get_text(strip=True)
                        date_obj = datetime.strptime(date_text, "%d.%m.%Y").replace(tzinfo=pytz.UTC)

            # Standard-Fallback, falls kein Datum geparst werden konnte
            if not date_obj:
                date_obj = datetime.now(pytz.UTC)

            # 3. Beschreibung (Vorschautext)
            desc_elem = article.select_one(".news-teaser__text") or article.select_one("p")
            description = desc_elem.get_text(" ", strip=True) if desc_elem else title

            # 4. Link auslesen
            link_elem = article.select_one("a.news-teaser__link") or article.select_one("a[href]")
            if not link_elem or not link_elem.get("href"):
                continue

            link = urljoin(BLOG_URL, link_elem["href"])

            blog_posts.append(
                {
                    "title": title,
                    "date": date_obj,
                    "description": description,
                    "link": link,
                }
            )

        # Dubletten entfernen & aufsteigend nach Datum sortieren
        unique_posts = {(p["link"], p["title"]): p for p in blog_posts}.values()
        return sorted(list(unique_posts), key=lambda x: x["date"], reverse=False)

    except Exception as e:
        print(f"Error parsing HTML content: {e}")
        raise


def generate_rss_feed(blog_posts, feed_name=FEED_NAME):
    try:
        fg = FeedGenerator()
        fg.title("Wirtschaftsarchive Mitteilungen")
        fg.description("Aktuelle Mitteilungen und Neuigkeiten aus den Wirtschaftsarchiven.")
        setup_feed_links(fg, BLOG_URL, feed_name)
        fg.language("de")
        fg.author({"name": "Wirtschaftsarchive"})

        for post in blog_posts:
            fe = fg.add_entry()
            fe.title(post["title"])
            fe.description(post["description"])
            fe.link(href=post["link"])

            pub_date = post["date"]
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=pytz.UTC)
            fe.published(pub_date)
            fe.id(post["link"])

        return fg
    except Exception as e:
        print(f"Error generating RSS feed: {e}")
        raise


def main():
    try:
        html_content = fetch_blog_content()
        blog_posts = parse_blog_html(html_content)
        if not blog_posts:
            print("Keine Beiträge gefunden.")
            return False
        feed = generate_rss_feed(blog_posts)
        save_rss_feed(feed, FEED_NAME)
        return True
    except Exception as e:
        print(f"Failed to generate RSS feed: {e}")
        return False


if __name__ == "__main__":
    main()
