from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLE = (ROOT / "static" / "css" / "style.css").read_text()
COMMUNITY = (ROOT / "templates" / "community.html").read_text()
ARCHIVE = (ROOT / "templates" / "archive.html").read_text()


def test_shared_light_theme_fallback_covers_legacy_content_cards():
    """Light mode must override the older dark-theme card text assumptions."""
    required_selectors = (
        "body.theme-white .search-page .result-card",
        "body.theme-white .announcements-page .announcement-card",
        "body.theme-white .give-page .giving-option",
        "body.theme-white .gallery-page .sermon-controls",
        "body.theme-white .pastor-teaching-page .series-card-pastor",
        "body.theme-white .pastors-book-page .book-info-card",
    )
    for selector in required_selectors:
        assert selector in STYLE


def test_community_and_archive_use_theme_aware_text_tokens():
    """The two pages that exposed the bug should not hard-code white card text."""
    assert ".group-card h3" in COMMUNITY
    assert "color: var(--page-text);" in COMMUNITY
    assert "color: var(--page-muted);" in COMMUNITY
    assert "--archive-muted" in ARCHIVE
    assert "--archive-divider" in ARCHIVE


def test_community_hero_has_one_readable_treatment_in_both_themes():
    """The page title should not switch to a pale, low-contrast light variant."""
    assert ".community-hero h1" in COMMUNITY
    assert "color: #fff;" in COMMUNITY
    assert "body.theme-white .community-hero" not in COMMUNITY
