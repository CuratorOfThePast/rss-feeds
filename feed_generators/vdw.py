from contextlib import suppress
from datetime import datetime

import pytz
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

from utils import fetch_page, get_project_root, save_rss_feed, setup_feed_links, setup_logging

logger = setup_logging()

FEED_NAME = "wirtschaftsarchive"
BLOG_URL = "https://www.wirtschaftsarchive.de/aktuelles/mitteilungen/"
LOCAL_FILE_NAME = "wirtschaftsarchive_mitteilungen.htm"


def fetch_blog_content(url=BLOG_URL):
    project_root = get_project_root()
    local_files = [project_root / LOCAL_FILE_NAME, project_root / "wirtschaftsarchive.htm"]

    for local_path in local_files:
        if local_path.exists():
            logger.info(f"Reading from local file for development: {local_path}")
            with open(local_path, encoding="utf-8") as f:
                return f.read()

    try:
        logger.info(f"Fetching blog content from URL: {url}")
        return fetch_page(url)
    except Exception as e:
        logger.error(f"Error fetching blog content: {e!s}")
        raise


def parse_blog_html(html_content):
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        blog_posts = []

        articles = soup.select("article")
        if not articles:
            articles = soup.select(".news-item, .list-item, .item")

        for article in articles:
            title_elem = article.select_one("h2") or article.select_one("h3") or article.select_one("a.title")
            if not title_elem:
                continue
            title = title_elem.text.strip()

            date_elem = article.select_one("time")
            date_obj = datetime.now(pytz.UTC)

            if date_elem and date_elem.get("datetime"):
                with suppress(ValueError):
                    date_obj = datetime.strptime(date_elem["datetime"].split("T")[0], "%Y-%m-%d")
            elif date_elem:
                with suppress(ValueError):
                    date_obj = datetime.strptime(date_elem.text.strip(), "%d.%m.%Y")

            desc_elem = article.select_one("p")
            description = desc_elem.text.strip() if desc_elem else title

            link_elem = article.select_one("a[href]")
            if not link_elem or not link_elem.get("href"):
                continue

            link = link_elem["href"]
            if link.startswith("/"):
                link = f"https://www.wirtschaftsarchive.de{link}"

            blog_posts.append(
                {
                    "title": title,
                    "date": date_obj,
                    "description": description,
                    "link": link,
                }
            )

        return blog_posts
    except Exception as e:
        logger.error(f"Error parsing HTML content: {e!s}")
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
        logger.error(f"Error generating RSS feed: {e!s}")
        raise


def main():
    try:
        html_content = fetch_blog_content()
        blog_posts = parse_blog_html(html_content)
        if not blog_posts:
            return False
        feed = generate_rss_feed(blog_posts)
        save_rss_feed(feed, FEED_NAME)
        return True
    except Exception as e:
        logger.error(f"Failed to generate RSS feed: {e!s}")
        return False


if __name__ == "__main__":
    main()
