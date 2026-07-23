from datetime import datetime

import pytz
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

from utils import fetch_page, get_project_root, save_rss_feed, setup_feed_links, setup_logging

logger = setup_logging()

FEED_NAME = "bundesarchiv"
BLOG_URL = "https://www.bundesarchiv.de/aktuelles/"
# For development/testing, look for this file in the project root
LOCAL_FILE_NAME = "Aktuelles aus dem Bundesarchiv - Bundesarchiv.htm"


def fetch_blog_content(url=BLOG_URL):
    """Fetch blog content from local file if it exists, otherwise from the given URL."""
    project_root = get_project_root()
    # Support both original name and simplified name if moved
    local_files = [
        project_root / LOCAL_FILE_NAME,
        project_root / "Aktuelles aus dem Bundesarchiv - Bundesarchiv.htm",
        project_root / "@Aktuelles aus dem Bundesarchiv - Bundesarchiv.htm",
    ]

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
    """Parse the blog HTML content and extract post information."""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        blog_posts = []

        # Find all blog post articles
        # Based on the structure: <article class="item" ...>
        articles = soup.select("article.item")

        for article in articles:
            # Extract title
            # <h3 class="underlined" ...><span>Title</span></h3>
            title_elem = article.select_one("h3.underlined span")
            if not title_elem:
                title_elem = article.select_one("h3")  # Fallback

            if not title_elem:
                logger.warning("Skipping post: no title found")
                continue
            title = title_elem.text.strip()

            # Extract date
            # <time datetime="2026-04-09">
            date_elem = article.select_one("time")
            if not date_elem or not date_elem.get("datetime"):
                logger.warning(f"Skipping post '{title}': no date found")
                continue
            date_str = date_elem["datetime"]
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                # Try parsing the display text if datetime attribute fails
                try:
                    date_obj = datetime.strptime(date_elem.text.strip(), "%d.%m.%Y")
                except ValueError:
                    logger.warning(f"Skipping post '{title}': could not parse date '{date_str}'")
                    continue

            # Extract description
            # <p>Description</p>
            desc_elem = article.select_one("p")
            description = desc_elem.text.strip() if desc_elem else title

            # Extract link
            # <a class="arrow-right" ... href="...">
            link_elem = article.select_one("a.arrow-right")
            if not link_elem or not link_elem.get("href"):
                # Fallback: check if the headline itself is a link or redirects
                link_elem = article.select_one("a[href]")

            if not link_elem or not link_elem.get("href"):
                logger.warning(f"Skipping post '{title}': no link found")
                continue

            link = link_elem["href"]
            if link.startswith("/"):
                link = f"https://www.bundesarchiv.de{link}"

            blog_posts.append(
                {
                    "title": title,
                    "date": date_obj,
                    "description": description,
                    "link": link,
                }
            )

        logger.info(f"Successfully parsed {len(blog_posts)} blog posts")
        return blog_posts

    except Exception as e:
        logger.error(f"Error parsing HTML content: {e!s}")
        raise


def generate_rss_feed(blog_posts, feed_name=FEED_NAME):
    """Generate RSS feed from blog posts."""
    try:
        fg = FeedGenerator()
        fg.title("Bundesarchiv Aktuelles")
        fg.description("Veranstaltungen, Informationen und Pressemitteilungen aus dem Bundesarchiv.")
        setup_feed_links(fg, BLOG_URL, feed_name)
        fg.language("de")

        # Set feed metadata
        fg.author({"name": "Bundesarchiv"})
        fg.logo(
            "https://www.bundesarchiv.de/typo3conf/ext/dreipc_bstu/Resources/Public/Frontend/assets/"
            "media/ci/logo_bundesarchiv.svg"
        )
        fg.subtitle("Neueste Nachrichten aus dem Bundesarchiv")

        # Add entries
        for post in blog_posts:
            fe = fg.add_entry()
            fe.title(post["title"])
            fe.description(post["description"])
            fe.link(href=post["link"])
            fe.published(post["date"].replace(tzinfo=pytz.UTC))
            fe.id(post["link"])

        logger.info("Successfully generated RSS feed")
        return fg

    except Exception as e:
        logger.error(f"Error generating RSS feed: {e!s}")
        raise


def main(blog_url=BLOG_URL, feed_name=FEED_NAME):
    """Main function to generate RSS feed from blog URL."""
    try:
        # Fetch blog content
        html_content = fetch_blog_content(blog_url)

        # Parse blog posts from HTML
        blog_posts = parse_blog_html(html_content)

        if not blog_posts:
            logger.warning("No blog posts found to generate feed.")
            return False

        # Generate RSS feed
        feed = generate_rss_feed(blog_posts, feed_name)

        # Save feed to file
        save_rss_feed(feed, feed_name)

        return True

    except Exception as e:
        logger.error(f"Failed to generate RSS feed: {e!s}")
        return False


if __name__ == "__main__":
    main()
