"""Planning Center Services and Google Workspace clients for worship slides."""

import logging
import os
import time
from urllib.parse import urlencode

import requests

from .bulletin_parser import (
    DEFAULT_BULLETIN_DOC_ID,
    DEFAULT_SLIDES_TEMPLATE_ID,
    _infer_category,
    chunk_text_into_slides,
    extract_google_id,
    extract_text_from_google_doc,
    parse_bulletin_text,
)

logger = logging.getLogger(__name__)

PCO_API = "https://api.planningcenteronline.com/services/v2"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

GOOGLE_SCOPES = (
    "https://www.googleapis.com/auth/drive "
    "https://www.googleapis.com/auth/documents "
    "https://www.googleapis.com/auth/presentations"
)


class IntegrationError(RuntimeError):
    pass


def google_configured():
    return bool(os.getenv("SLIDES_GOOGLE_CLIENT_ID") and os.getenv("SLIDES_GOOGLE_CLIENT_SECRET"))


def google_authorize_url(state, redirect_uri):
    if not google_configured():
        raise IntegrationError("Set SLIDES_GOOGLE_CLIENT_ID and SLIDES_GOOGLE_CLIENT_SECRET first.")
    params = {
        "client_id": os.environ["SLIDES_GOOGLE_CLIENT_ID"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": GOOGLE_SCOPES,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)


def exchange_google_code(code, redirect_uri):
    response = requests.post(GOOGLE_TOKEN_URL, data={
        "code": code,
        "client_id": os.environ["SLIDES_GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["SLIDES_GOOGLE_CLIENT_SECRET"],
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }, timeout=20)
    if not response.ok:
        raise IntegrationError("Google authorization could not be completed.")
    return response.json()


def google_access_token(token):
    if token.get("access_token") and token.get("expires_at", 0) > time.time() + 60:
        return token
    refresh_token = token.get("refresh_token")
    if not refresh_token:
        raise IntegrationError("Google connection expired. Reconnect Google Drive.")
    response = requests.post(GOOGLE_TOKEN_URL, data={
        "client_id": os.environ.get("SLIDES_GOOGLE_CLIENT_ID", ""),
        "client_secret": os.environ.get("SLIDES_GOOGLE_CLIENT_SECRET", ""),
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }, timeout=20)
    if not response.ok:
        raise IntegrationError("Google connection expired. Reconnect Google Drive.")
    fresh = response.json()
    token.update(fresh)
    token["refresh_token"] = refresh_token
    token["expires_at"] = time.time() + fresh.get("expires_in", 3600)
    return token


def google_request(token, method, url, **kwargs):
    token = google_access_token(token)
    response = requests.request(method, url, headers={
        "Authorization": "Bearer " + token["access_token"],
        "Content-Type": "application/json",
    }, timeout=35, **kwargs)
    if not response.ok:
        err_msg = "Google Workspace returned an error while processing your request."
        try:
            err_json = response.json()
            err_msg = err_json.get("error", {}).get("message") or err_msg
        except Exception:
            pass
        logger.warning("Google API error (%s %s): %s", method, url, err_msg)
        raise IntegrationError(f"Google Workspace error: {err_msg}")
    return response.json() if response.content else {}


def copy_google_drive_file(token, file_id, new_title):
    """Make a copy of a Google Drive file (such as a standardized slides template)."""
    return google_request(
        token,
        "POST",
        f"https://www.googleapis.com/drive/v3/files/{file_id}/copy",
        json={"name": new_title},
    )


def get_google_doc(token, doc_id_or_url):
    """Fetch and parse a Google Doc bulletin by ID or URL."""
    doc_id = extract_google_id(doc_id_or_url)
    if not doc_id:
        raise IntegrationError("Please provide a valid Google Doc URL or ID.")

    doc_data = google_request(token, "GET", f"https://docs.googleapis.com/v1/documents/{doc_id}")
    doc_title = doc_data.get("title") or "Worship Bulletin"
    raw_text = extract_text_from_google_doc(doc_data)
    items = parse_bulletin_text(raw_text)

    return {
        "id": doc_id,
        "title": doc_title,
        "text": raw_text,
        "items": items,
        "url": f"https://docs.google.com/document/d/{doc_id}/edit",
    }


def pco_request(token, path, params=None):
    response = requests.get(PCO_API + path, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/json",
    }, params=params, timeout=20)
    if not response.ok:
        if response.status_code == 401:
            raise IntegrationError("Planning Center connection expired. Reconnect Planning Center Services.")
        raise IntegrationError("Planning Center Services could not load that information.")
    return response.json()


def list_service_types(token):
    return pco_request(token, "/service_types", {"per_page": 100}).get("data", [])


def list_plans(token, service_type_id):
    return pco_request(token, f"/service_types/{service_type_id}/plans", {
        "per_page": 30,
        "order": "-sort_date",
    }).get("data", [])


def get_plan_items(token, service_type_id, plan_id):
    result = pco_request(token, f"/service_types/{service_type_id}/plans/{plan_id}/items", {
        "per_page": 100,
        "include": "song,arrangement",
    })
    included = {(item.get("type"), item["id"]): item.get("attributes", {}) for item in result.get("included", [])}
    items = []
    for item in result.get("data", []):
        attrs = item.get("attributes", {})
        relationships = item.get("relationships", {})
        song_ref = relationships.get("song", {}).get("data") or {}
        arrangement_ref = relationships.get("arrangement", {}).get("data") or {}
        song_attrs = included.get(("Song", song_ref.get("id")), {})
        arrangement_attrs = included.get(("Arrangement", arrangement_ref.get("id")), {})
        title = attrs.get("title") or song_attrs.get("title") or attrs.get("description") or "Service item"
        content = arrangement_attrs.get("lyrics") or attrs.get("description") or ""
        is_song = bool(song_ref.get("id") or attrs.get("item_type") == "song")
        category = "song" if is_song else _infer_category(title)
        slides = chunk_text_into_slides(title, content, category)
        items.append({
            "title": title,
            "content": content,
            "kind": "song" if is_song else "item",
            "category": category,
            "sequence": attrs.get("sequence", 0),
            "slides": slides,
            "slide_count": len(slides),
        })
    return sorted(items, key=lambda item: item["sequence"] or 0)


def _flatten_items_to_slides(items):
    """Expand service items into individual slides."""
    slides = []
    for item in items:
        # If pre-chunked slides exist, use them
        pre_slides = item.get("slides")
        if isinstance(pre_slides, list) and pre_slides:
            for s in pre_slides:
                slides.append({
                    "title": s.get("title") or item.get("title", ""),
                    "content": s.get("content", ""),
                })
            continue

        # Otherwise chunk content into blocks of up to 5 lines
        lines = [line.strip() for line in (item.get("content") or "").splitlines()]
        blocks, block = [], []
        for line in lines:
            if not line:
                if block:
                    blocks.append("\n".join(block))
                    block = []
                continue
            block.append(line)
            if len(block) >= 5:
                blocks.append("\n".join(block))
                block = []
        if block:
            blocks.append("\n".join(block))
        if not blocks:
            blocks = [""]
        slides.extend({"title": item.get("title", ""), "content": text} for text in blocks)
    return slides


def create_google_presentation(token, title, items, template_id=None):
    """Create a Google Slides presentation from a standardized template or fresh branded deck."""
    clean_template_id = extract_google_id(template_id or DEFAULT_SLIDES_TEMPLATE_ID)

    # Attempt to duplicate the standardized template if available
    if clean_template_id:
        try:
            return create_presentation_from_template(token, title, items, clean_template_id)
        except Exception as exc:
            logger.warning(
                "Could not copy template %s (%s). Falling back to direct presentation generation.",
                clean_template_id,
                exc,
            )

    return _create_fresh_branded_presentation(token, title, items)


def create_presentation_from_template(token, title, items, template_id):
    """Clone the standardized Google Slides template and populate it with service slides."""
    copied = copy_google_drive_file(token, template_id, title)
    presentation_id = copied["id"]

    slides_data = _flatten_items_to_slides(items)
    deck = google_request(token, "GET", f"https://slides.googleapis.com/v1/presentations/{presentation_id}")

    template_slides = deck.get("slides", [])
    if not template_slides:
        # Cloned presentation has no slides; fall back to standard slide creation
        return _populate_fresh_slides(token, presentation_id, slides_data)

    # Pick the best sample slide from the template to duplicate
    # Look for a slide that has both title and body text boxes, or fallback to the last slide
    source_slide_id = template_slides[-1]["objectId"]
    for s in template_slides:
        types = [e.get("shape", {}).get("placeholder", {}).get("type") for e in s.get("pageElements", [])]
        if "BODY" in types or "SUBTITLE" in types:
            source_slide_id = s["objectId"]
            break

    # Duplicate the source slide for each slide chunk
    duplicate_requests = []
    for idx, _ in enumerate(slides_data):
        duplicate_requests.append({
            "duplicateObject": {
                "objectId": source_slide_id,
                "objectIds": {source_slide_id: f"cpc_gen_slide_{idx}"},
            }
        })

    if duplicate_requests:
        google_request(
            token,
            "POST",
            f"https://slides.googleapis.com/v1/presentations/{presentation_id}:batchUpdate",
            json={"requests": duplicate_requests},
        )

    # Re-fetch deck to get elements of newly created slides
    deck = google_request(token, "GET", f"https://slides.googleapis.com/v1/presentations/{presentation_id}")
    update_requests = []

    for idx, slide_item in enumerate(slides_data):
        gen_id = f"cpc_gen_slide_{idx}"
        slide_obj = next((s for s in deck.get("slides", []) if s["objectId"] == gen_id), None)
        if not slide_obj:
            continue

        # Replace template placeholder tags {{title}}, {{content}}
        update_requests.extend([
            {
                "replaceAllText": {
                    "containsText": {"matchCase": False, "text": "{{title}}"},
                    "replaceText": slide_item["title"],
                    "pageObjectIds": [gen_id],
                }
            },
            {
                "replaceAllText": {
                    "containsText": {"matchCase": False, "text": "{{content}}"},
                    "replaceText": slide_item["content"],
                    "pageObjectIds": [gen_id],
                }
            },
        ])

        # Also replace text in explicit TITLE and BODY / SUBTITLE shapes
        for element in slide_obj.get("pageElements", []):
            placeholder = element.get("shape", {}).get("placeholder", {}).get("type")
            shape_id = element.get("objectId")
            if not shape_id:
                continue

            if placeholder == "TITLE":
                update_requests.extend([
                    {"deleteText": {"objectId": shape_id, "textRange": {"type": "ALL"}}},
                    {"insertText": {"objectId": shape_id, "text": slide_item["title"], "insertionIndex": 0}},
                ])
            elif placeholder in ("BODY", "SUBTITLE"):
                update_requests.extend([
                    {"deleteText": {"objectId": shape_id, "textRange": {"type": "ALL"}}},
                    {"insertText": {"objectId": shape_id, "text": slide_item["content"], "insertionIndex": 0}},
                ])

    # Delete the original placeholder slides from the template so only generated service slides remain
    for orig_slide in template_slides:
        update_requests.append({"deleteObject": {"objectId": orig_slide["objectId"]}})

    if update_requests:
        google_request(
            token,
            "POST",
            f"https://slides.googleapis.com/v1/presentations/{presentation_id}:batchUpdate",
            json={"requests": update_requests},
        )

    return {
        "id": presentation_id,
        "url": f"https://docs.google.com/presentation/d/{presentation_id}/edit",
        "template_used": True,
    }


def _create_fresh_branded_presentation(token, title, items):
    """Create a presentation from scratch using CPC New Haven's dark blue theme."""
    presentation = google_request(token, "POST", "https://slides.googleapis.com/v1/presentations", json={"title": title})
    presentation_id = presentation["presentationId"]
    slides_data = _flatten_items_to_slides(items)
    res = _populate_fresh_slides(token, presentation_id, slides_data)
    res["template_used"] = False
    return res


def _populate_fresh_slides(token, presentation_id, slides):
    deck = google_request(token, "GET", f"https://slides.googleapis.com/v1/presentations/{presentation_id}")
    create_requests = []
    initial_slides = deck.get("slides", [])
    if initial_slides:
        create_requests.append({"deleteObject": {"objectId": initial_slides[0]["objectId"]}})

    for index, _ in enumerate(slides):
        create_requests.append({
            "createSlide": {
                "objectId": f"cpc_slide_{index}",
                "slideLayoutReference": {"predefinedLayout": "TITLE_AND_BODY"},
            }
        })

    if create_requests:
        google_request(
            token,
            "POST",
            f"https://slides.googleapis.com/v1/presentations/{presentation_id}:batchUpdate",
            json={"requests": create_requests},
        )

    deck = google_request(token, "GET", f"https://slides.googleapis.com/v1/presentations/{presentation_id}")
    update_requests = []

    for index, item in enumerate(slides):
        slide = next((s for s in deck.get("slides", []) if s["objectId"] == f"cpc_slide_{index}"), None)
        if not slide:
            continue
        for element in slide.get("pageElements", []):
            placeholder = element.get("shape", {}).get("placeholder", {}).get("type")
            if placeholder == "TITLE":
                update_requests.extend([
                    {"insertText": {"objectId": element["objectId"], "text": item["title"], "insertionIndex": 0}},
                    {
                        "updateTextStyle": {
                            "objectId": element["objectId"],
                            "style": {
                                "fontSize": {"magnitude": 30, "unit": "PT"},
                                "bold": True,
                                "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}},
                            },
                            "textRange": {"type": "ALL"},
                            "fields": "fontSize,bold,foregroundColor",
                        }
                    },
                ])
            elif placeholder in ("BODY", "SUBTITLE"):
                update_requests.extend([
                    {"insertText": {"objectId": element["objectId"], "text": item["content"], "insertionIndex": 0}},
                    {
                        "updateTextStyle": {
                            "objectId": element["objectId"],
                            "style": {
                                "fontSize": {"magnitude": 25, "unit": "PT"},
                                "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}},
                            },
                            "textRange": {"type": "ALL"},
                            "fields": "fontSize,foregroundColor",
                        }
                    },
                ])
        update_requests.append({
            "updatePageProperties": {
                "objectId": slide["objectId"],
                "pageProperties": {
                    "pageBackgroundFill": {
                        "solidFill": {
                            "color": {"rgbColor": {"red": 0.035, "green": 0.075, "blue": 0.13}},
                            "alpha": 1,
                        }
                    }
                },
                "fields": "pageBackgroundFill",
            }
        })

    if update_requests:
        google_request(
            token,
            "POST",
            f"https://slides.googleapis.com/v1/presentations/{presentation_id}:batchUpdate",
            json={"requests": update_requests},
        )

    return {"id": presentation_id, "url": f"https://docs.google.com/presentation/d/{presentation_id}/edit"}


def create_google_doc(token, title, items):
    doc = google_request(token, "POST", "https://docs.googleapis.com/v1/documents", json={"title": title})
    content = "\n".join(f"{item['title']}\n{item['content']}\n" for item in items)
    if content:
        google_request(token, "POST", f"https://docs.googleapis.com/v1/documents/{doc['documentId']}:batchUpdate", json={
            "requests": [{"insertText": {"location": {"index": 1}, "text": content}}]
        })
    return {"id": doc["documentId"], "url": f"https://docs.google.com/document/d/{doc['documentId']}/edit"}
