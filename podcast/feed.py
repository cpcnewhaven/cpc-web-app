from xml.etree.ElementTree import Element, SubElement, tostring
from email.utils import format_datetime


def generate_rss(episodes, title, description, site_url):
    rss = Element(
        "rss",
        {
            "version": "2.0",
            "xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
        },
    )

    channel = SubElement(rss, "channel")

    SubElement(channel, "title").text = title
    SubElement(channel, "description").text = description
    SubElement(channel, "link").text = site_url

    for episode in episodes:
        item = SubElement(channel, "item")

        SubElement(item, "title").text = episode.title
        SubElement(item, "description").text = episode.description

        if episode.published_at:
            SubElement(item, "pubDate").text = format_datetime(
                episode.published_at
            )

        if episode.audio_url:
            SubElement(
                item,
                "enclosure",
                {
                    "url": episode.audio_url,
                    "type": "audio/mpeg",
                },
            )

    return tostring(rss, encoding="utf-8", xml_declaration=True)