#!/usr/bin/env python3
"""Import Beyond the Sunday Sermon from the public CPC RSS feed into the DB."""

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import app, sync_beyond_episodes


def main():
    with app.app_context():
        result = sync_beyond_episodes()
    logging.info("Beyond podcast sync: %s", result)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
