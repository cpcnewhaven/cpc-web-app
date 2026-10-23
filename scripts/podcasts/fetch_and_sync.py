#!/usr/bin/env python3
"""Import Beyond the Sunday Sermon from the public CPC RSS feed into the DB."""

import logging
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import app, sync_beyond_episodes


def main():
    try:
        feed_url = app.config["PODCAST_FEEDS"].get("beyond")
        if not feed_url:
            raise RuntimeError("BEYOND_PODCAST_RSS_URL is not configured")

        with app.app_context():
            result = sync_beyond_episodes()
        logging.info("Beyond podcast sync succeeded: %s", result)
    except Exception:
        logging.error("Beyond podcast sync failed:\n%s", traceback.format_exc())
        raise


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
