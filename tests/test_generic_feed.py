import unittest

from feed_generators.generic_feed import parse_blog_html


class GenericFeedParserTests(unittest.TestCase):
    def test_parse_blog_html_with_css_selectors(self) -> None:
        html = """
        <main>
          <section class="posts">
            <article class="post">
              <h2><a href="/news/erste">Erster Titel</a></h2>
              <p>Erste Kurzbeschreibung</p>
              <time datetime="2026-07-20">20.07.2026</time>
            </article>
            <article class="post">
              <h2><a href="https://example.org/news/zweite">Zweiter Titel</a></h2>
              <p>Zweite Kurzbeschreibung</p>
              <time datetime="2026-07-21">21.07.2026</time>
            </article>
          </section>
        </main>
        """

        selectors = {
            "article_selector": "article.post",
            "title_selector": "h2 a",
            "link_selector": "h2 a",
            "description_selector": "p",
            "date_selector": "time",
            "date_attr": "datetime",
            "date_format": "%Y-%m-%d",
            "base_url": "https://example.org",
        }

        posts = parse_blog_html(html, selectors)

        self.assertEqual(len(posts), 2)
        self.assertEqual(posts[0]["title"], "Erster Titel")
        self.assertEqual(posts[0]["link"], "https://example.org/news/erste")
        self.assertEqual(posts[0]["description"], "Erste Kurzbeschreibung")
        self.assertEqual(posts[0]["date"].date().isoformat(), "2026-07-20")
