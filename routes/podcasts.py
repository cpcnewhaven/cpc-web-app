from flask import Response
from models import PodcastEpisode
from podcast.feed import generate_rss


@bp.route("/podcast/rss")
def podcast_rss():
    episodes = (
        PodcastEpisode.query
        .filter_by(published=True)
        .order_by(PodcastEpisode.published_at.desc())
        .limit(100)
        .all()
    )

    xml = generate_rss(
        episodes,
        title="CPC New Haven",
        description="CPC New Haven sermons and teaching",
        site_url="https://cpcnewhaven.org",
    )

    return Response(
        xml,
        content_type="application/rss+xml; charset=utf-8"
    )