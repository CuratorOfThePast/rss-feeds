from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def create_example_config(path: Path) -> None:
    config = {
        "feeds": {
            "meine_neuer_feed": {
                "script": "generic_feed.py",
                "type": "requests",
                "blog_url": "https://example.org/aktuelles/",
                "title": "Mein neuer Feed",
                "description": "Beschreibung des Feeds",
                "local_file_name": "example.html",
                "selectors": {
                    "article_selector": "article.post",
                    "title_selector": "h2 a",
                    "link_selector": "h2 a",
                    "description_selector": "p",
                    "date_selector": "time",
                    "date_attr": "datetime",
                    "date_format": "%Y-%m-%d",
                    "base_url": "https://example.org",
                },
            }
        }
    }
    path.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8")


def add_feed(feed_id: str, config_path: Path) -> None:
    if config_path.exists():
        with open(config_path, encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    else:
        data = {}

    feeds = data.setdefault("feeds", {})
    if feed_id in feeds:
        raise SystemExit(f"Feed '{feed_id}' exists already")

    feed_entry = {
        "script": "generic_feed.py",
        "type": "requests",
        "blog_url": "https://example.org/aktuelles/",
        "title": feed_id.replace("_", " ").title(),
        "description": "Beschreibung des Feeds",
        "selectors": {
            "article_selector": "article.post",
            "title_selector": "h2 a",
            "link_selector": "h2 a",
            "description_selector": "p",
            "date_selector": "time",
            "date_attr": "datetime",
            "date_format": "%Y-%m-%d",
            "base_url": "https://example.org",
        },
    }
    feeds[feed_id] = feed_entry
    config_path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"Added '{feed_id}' to {config_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Add a new feed configuration for the generic generator")
    parser.add_argument("feed_id", nargs="?", help="Identifier for the new feed")
    parser.add_argument("--config", default=str(ROOT / "feeds.yaml"), help="Path to the feeds.yaml file")
    parser.add_argument("--example", action="store_true", help="Create an example config file")
    args = parser.parse_args()

    if args.example:
        create_example_config(Path(args.config))
        print(f"Example config written to {args.config}")
        return

    if not args.feed_id:
        parser.error("feed_id is required unless --example is used")

    add_feed(args.feed_id, Path(args.config))


if __name__ == "__main__":
    main()
