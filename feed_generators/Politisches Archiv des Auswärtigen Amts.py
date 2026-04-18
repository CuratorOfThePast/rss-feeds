from datetime import datetime
from pathlib import Path

import pytz
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

from utils import fetch_page, save_rss_feed, setup_feed_links, setup_logging, get_project_root

logger = setup_logging()

FEED_NAME = "auswaertiges_amt_archiv"
BLOG_URL = "https://archiv.diplo.de/arc-de/aktuelles/"
# For development/testing, look for this file in the project root
LOCAL_FILE_NAME = "Nachrichten aus dem Archiv - Auswärtiges Amt.htm"


def fetch_blog_content(url=BLOG_URL):
    """Fetch blog content from local file if it exists, otherwise from the given URL."""
    project_root = get_project_root()
    # Support both original name and simplified name if moved
    local_files = [
        project_root / LOCAL_FILE_NAME,
        project_root / "Nachrichten aus dem Archiv - Auswärtiges Amt.htm",
    ]
    
    for local_path in local_files:
        if local_path.exists():
            logger.info(f"Reading from local file for development: {local_path}")
            with open(local_path, "r", encoding="utf-8") as f:
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

        # Find all blog post teasers
        # Based on the structure: <div class="c-teaser--default is-headline-text-image">
        teasers = soup.select('div.c-teaser--default.is-headline-text-image')
        
        for teaser in teasers:
            # Extract title
            # <h3 class="teaser__headline"> <span class="teaser__headline-content"> <span>Title</span> </span>
            title_elem = teaser.select_one("h3.teaser__headline span.teaser__headline-content span")
            if not title_elem:
                logger.warning("Skipping post: no title found")
                continue
            title = title_elem.text.strip()

            # Extract link
            # <a class="teaser__link" href="...">
            link_elem = teaser.select_one("a.teaser__link")
            if not link_elem or not link_elem.get("href"):
                logger.warning(f"Skipping post '{title}': no link found")
                continue
            link = link_elem["href"]
            if link.startswith("/"):
                link = f"https://archiv.diplo.de{link}"

            # Extract description
            # <p class="teaser__text">Description</p>
            desc_elem = teaser.select_one("p.teaser__text")
            description = desc_elem.text.strip() if desc_elem else title

            # Extract date from the detail page
            try:
                detail_html = fetch_page(link)
                detail_soup = BeautifulSoup(detail_html, "html.parser")
                # Look for date pattern like "17.04.2026 - Pressemitteilung"
                date_texts = detail_soup.find_all(string=lambda text: text and " - " in text and any(char.isdigit() for char in text))
                date_str = None
                for text in date_texts:
                    # Extract date from format "dd.mm.yyyy - ..."
                    import re
                    match = re.search(r'(\d{1,2}\.\d{1,2}\.\d{4})', text)
                    if match:
                        date_str = match.group(1)
                        break
                
                if not date_str:
                    logger.warning(f"Skipping post '{title}': no date found on detail page")
                    continue
                
                try:
                    date_obj = datetime.strptime(date_str, "%d.%m.%Y")
                except ValueError:
                    logger.warning(f"Skipping post '{title}': could not parse date '{date_str}'")
                    continue
                    
            except Exception as e:
                logger.warning(f"Skipping post '{title}': error fetching detail page: {e}")
                continue

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
        fg.title("Politisches Archiv des Auswärtigen Amts - Aktuelles")
        fg.description("Nachrichten und Pressemitteilungen aus dem Politischen Archiv des Auswärtigen Amts.")
        setup_feed_links(fg, BLOG_URL, feed_name)
        fg.language("de")

        # Set feed metadata
        fg.author({"name": "Auswärtiges Amt"})
        fg.logo("https://archiv.diplo.de/resource/crblob/772/47f731c5aa09d415e52ad2d35c55a7be/aamt-logo-sp-data.svg")
        fg.subtitle("Neueste Nachrichten aus dem Politischen Archiv des Auswärtigen Amts")

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