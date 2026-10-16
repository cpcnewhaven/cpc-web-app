"""Planning Center Services and Google Workspace clients for worship slides."""

import os
from urllib.parse import urlencode

import requests

PCO_API = "https://api.planningcenteronline.com/services/v2"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


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
        "scope": "https://www.googleapis.com/auth/drive.file https://www.googleapis.com/auth/documents",
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
    if token.get("access_token") and token.get("expires_at", 0) > __import__("time").time() + 60:
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
    token["expires_at"] = __import__("time").time() + fresh.get("expires_in", 3600)
    return token


def google_request(token, method, url, **kwargs):
    token = google_access_token(token)
    response = requests.request(method, url, headers={
        "Authorization": "Bearer " + token["access_token"],
        "Content-Type": "application/json",
    }, timeout=30, **kwargs)
    if not response.ok:
        raise IntegrationError("Google Workspace returned an error while creating the file.")
    return response.json() if response.content else {}


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
        items.append({
            "title": title,
            "content": content,
            "kind": "song" if song_ref.get("id") else "item",
            "sequence": attrs.get("sequence", 0),
        })
    return sorted(items, key=lambda item: item["sequence"] or 0)


def create_google_presentation(token, title, items):
    presentation = google_request(token, "POST", "https://slides.googleapis.com/v1/presentations", json={"title": title})
    presentation_id = presentation["presentationId"]
    deck = google_request(token, "GET", f"https://slides.googleapis.com/v1/presentations/{presentation_id}")
    # Keep each projected slide readable: split song verses and readings into short blocks.
    slides = []
    for item in items:
        lines = [line.strip() for line in item["content"].splitlines()]
        blocks, block = [], []
        for line in lines:
            if not line:
                if block:
                    blocks.append("\n".join(block)); block = []
                continue
            block.append(line)
            if len(block) >= 5:
                blocks.append("\n".join(block)); block = []
        if block:
            blocks.append("\n".join(block))
        if not blocks:
            blocks = [""]
        slides.extend({"title": item["title"], "content": text} for text in blocks)
    create_requests = []
    initial_slides = deck.get("slides", [])
    if initial_slides:
        create_requests.append({"deleteObject": {"objectId": initial_slides[0]["objectId"]}})
    for index, item in enumerate(slides):
        create_requests.append({"createSlide": {"objectId": f"cpc_slide_{index}", "slideLayoutReference": {"predefinedLayout": "TITLE_AND_BODY"}}})
    if create_requests:
        google_request(token, "POST", f"https://slides.googleapis.com/v1/presentations/{presentation_id}:batchUpdate", json={"requests": create_requests})
    deck = google_request(token, "GET", f"https://slides.googleapis.com/v1/presentations/{presentation_id}")
    update_requests = []
    for index, item in enumerate(slides):
        slide = next(s for s in deck.get("slides", []) if s["objectId"] == f"cpc_slide_{index}")
        for element in slide.get("pageElements", []):
            placeholder = element.get("shape", {}).get("placeholder", {}).get("type")
            if placeholder == "TITLE":
                update_requests.extend([
                    {"insertText": {"objectId": element["objectId"], "text": item["title"], "insertionIndex": 0}},
                    {"updateTextStyle": {"objectId": element["objectId"], "style": {"fontSize": {"magnitude": 30, "unit": "PT"}, "bold": True, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "textRange": {"type": "ALL"}, "fields": "fontSize,bold,foregroundColor"}},
                ])
            elif placeholder in ("BODY", "SUBTITLE"):
                update_requests.extend([
                    {"insertText": {"objectId": element["objectId"], "text": item["content"], "insertionIndex": 0}},
                    {"updateTextStyle": {"objectId": element["objectId"], "style": {"fontSize": {"magnitude": 25, "unit": "PT"}, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "textRange": {"type": "ALL"}, "fields": "fontSize,foregroundColor"}},
                ])
        update_requests.append({"updatePageProperties": {"objectId": slide["objectId"], "pageProperties": {"pageBackgroundFill": {"solidFill": {"color": {"rgbColor": {"red": 0.035, "green": 0.075, "blue": 0.13}}, "alpha": 1}}}, "fields": "pageBackgroundFill"}})
    if update_requests:
        google_request(token, "POST", f"https://slides.googleapis.com/v1/presentations/{presentation_id}:batchUpdate", json={"requests": update_requests})
    return {"id": presentation_id, "url": f"https://docs.google.com/presentation/d/{presentation_id}/edit"}


def create_google_doc(token, title, items):
    doc = google_request(token, "POST", "https://docs.googleapis.com/v1/documents", json={"title": title})
    content = "\n".join(f"{item['title']}\n{item['content']}\n" for item in items)
    if content:
        google_request(token, "POST", f"https://docs.googleapis.com/v1/documents/{doc['documentId']}:batchUpdate", json={
            "requests": [{"insertText": {"location": {"index": 1}, "text": content}}]
        })
    return {"id": doc["documentId"], "url": f"https://docs.google.com/document/d/{doc['documentId']}/edit"}
