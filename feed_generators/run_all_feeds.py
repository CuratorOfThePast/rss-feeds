from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from feed_generators.models import load_feed_registry
from feed_generators.utils import setup_logging

logger = setup_logging()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate one or all RSS feeds")
    parser.add_argument("--feed", help="Generate a single feed by registry name")
    args = parser.parse_args()

    registry = load_feed_registry()
    selected_names = [args.feed] if args.feed else list(registry)

    for feed_name in selected_names:
        config = registry[feed_name]
        if not config.enabled:
            logger.info("Skipping disabled feed %s", feed_name)
            continue

        if config.script == "generic_feed.py":
            from feed_generators.generic_feed import generate_feed_from_config

            generate_feed_from_config(
                {
                    "feed_name": feed_name,
                    "blog_url": config.blog_url,
                    "title": config.title or feed_name.replace("_", " ").title(),
                    "description": config.description or "RSS feed generated from a configurable source",
                    "local_file_name": config.local_file_name,
                    "selectors": config.selectors or {},
                }
            )
            continue

        module = importlib.import_module(f"feed_generators.{Path(config.script).stem}")
        if hasattr(module, "main"):
            logger.info("Generating feed %s via %s", feed_name, config.script)
            module.main(config.blog_url, feed_name)
        else:
            logger.warning("No main() found in %s", config.script)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
