"""Small Planning Center Calendar API client for the single-church integration."""
import os
import requests


BASE_URL = "https://api.planningcenteronline.com"


class PlanningCenterError(RuntimeError):
    pass


def _auth():
    client_id = __import__("os").getenv("PLANNING_CENTER_CLIENT_ID")
    token = __import__("os").getenv("PLANNING_CENTER_PERSONAL_ACCESS_TOKEN")
    if not client_id or not token:
        raise PlanningCenterError("Planning Center credentials are not configured")
    return (client_id, token)


def oauth_authorize_url(state, redirect_uri):
    from urllib.parse import urlencode
    return "https://api.planningcenteronline.com/oauth/authorize?" + urlencode({
        "client_id": os.getenv("PLANNING_CENTER_CLIENT_ID", ""),
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": os.getenv("PLANNING_CENTER_OAUTH_SCOPES", "calendar"),
        "state": state,
    })


def exchange_code(code, redirect_uri):
    response = requests.post("https://api.planningcenteronline.com/oauth/token", data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": os.getenv("PLANNING_CENTER_CLIENT_ID", ""),
        "client_secret": os.getenv("PLANNING_CENTER_CLIENT_SECRET", ""),
    }, timeout=15)
    if not response.ok:
        raise PlanningCenterError(f"Planning Center OAuth failed: {response.status_code}")
    return response.json()


def _oauth_auth(token):
    return {"Authorization": f"Bearer {token}"}


def upcoming_events_with_token(token, calendar_id=None, per_page=100):
    params = {"per_page": min(per_page, 100)}
    path = f"/calendar/v2/calendars/{calendar_id}/events" if calendar_id else "/calendar/v2/events"
    response = requests.get(BASE_URL + path, headers={"Accept": "application/json", **_oauth_auth(token)}, params=params, timeout=15)
    if not response.ok:
        raise PlanningCenterError(f"Planning Center returned {response.status_code}")
    return response.json().get("data", [])


def _get(path, params=None):
    response = requests.get(
        BASE_URL + path,
        auth=_auth(),
        params=params,
        headers={"Accept": "application/json", "User-Agent": "CPC-Web-App"},
        timeout=15,
    )
    if not response.ok:
        raise PlanningCenterError(f"Planning Center returned {response.status_code}: {response.text[:300]}")
    return response.json()


def event(event_id):
    return _get(f"/calendar/v2/events/{event_id}").get("data", {})


def upcoming_events(calendar_id=None, per_page=100):
    params = {"per_page": min(per_page, 100)}
    if calendar_id:
        return _get(f"/calendar/v2/calendars/{calendar_id}/events", params=params).get("data", [])
    return _get("/calendar/v2/events", params=params).get("data", [])


def event_instances(event_id):
    return _get(f"/calendar/v2/events/{event_id}/event_instances", params={"per_page": 100}).get("data", [])
