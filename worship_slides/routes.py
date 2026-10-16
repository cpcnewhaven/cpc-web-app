"""Private routes for the worship slides workspace."""

import hmac
import json
import os
import time
import uuid
from functools import wraps

from flask import abort, current_app, jsonify, redirect, render_template, request, session, url_for

from . import worship_slides_bp
from .integrations import (
    IntegrationError,
    create_google_doc,
    create_google_presentation,
    exchange_google_code,
    google_access_token,
    google_authorize_url,
    google_configured,
    list_plans,
    list_service_types,
    get_plan_items,
)

PCO_TOKEN_KEY = "worship_slides_pco_tokens"
GOOGLE_TOKEN_KEY = "worship_slides_google_tokens"


def staff_only(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def _get_token(key):
    from app import SiteContent
    row = SiteContent.query.filter_by(key=key).first()
    return json.loads(row.value) if row and row.value else None


def _save_token(key, token):
    from app import SiteContent, db
    row = SiteContent.query.filter_by(key=key).first()
    if row:
        row.value = json.dumps(token)
    else:
        db.session.add(SiteContent(key=key, value=json.dumps(token)))
    db.session.commit()


def _delete_token(key):
    from app import SiteContent, db
    SiteContent.query.filter_by(key=key).delete()
    db.session.commit()


def _csrf_ok():
    supplied = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token", "")
    return bool(session.get("slides_csrf")) and hmac.compare_digest(supplied, session["slides_csrf"])


def _pco_access_token():
    token = _get_token(PCO_TOKEN_KEY)
    if not token:
        raise IntegrationError("Connect Planning Center Services to browse worship plans.")
    expires_at = token.get("expires_at", 0)
    if expires_at and expires_at <= time.time() + 60:
        refresh = token.get("refresh_token")
        if not refresh:
            raise IntegrationError("Planning Center connection expired. Reconnect Planning Center Services.")
        import requests
        response = requests.post("https://api.planningcenteronline.com/oauth/token", data={
            "grant_type": "refresh_token",
            "refresh_token": refresh,
            "client_id": os.getenv("PLANNING_CENTER_CLIENT_ID", ""),
            "client_secret": os.getenv("PLANNING_CENTER_CLIENT_SECRET", ""),
        }, timeout=20)
        if not response.ok:
            raise IntegrationError("Planning Center connection expired. Reconnect Planning Center Services.")
        updated = response.json()
        updated.setdefault("refresh_token", refresh)
        updated["expires_at"] = time.time() + updated.get("expires_in", 3600)
        token.update(updated)
        _save_token(PCO_TOKEN_KEY, token)
    return token["access_token"]


@worship_slides_bp.route("/")
@staff_only
def workspace():
    if "slides_csrf" not in session:
        session["slides_csrf"] = uuid.uuid4().hex
    return render_template(
        "slides_workspace.html",
        csrf_token=session["slides_csrf"],
        pco_connected=bool(_get_token(PCO_TOKEN_KEY)),
        google_connected=bool(_get_token(GOOGLE_TOKEN_KEY)),
        google_configured=google_configured(),
    )


@worship_slides_bp.route("/connect/planning-center")
@staff_only
def connect_planning_center():
    if not os.getenv("PLANNING_CENTER_CLIENT_ID") or not os.getenv("PLANNING_CENTER_CLIENT_SECRET"):
        return redirect(url_for("worship_slides.workspace", setup="planning-center"))
    state = uuid.uuid4().hex
    session["slides_pco_oauth_state"] = state
    from urllib.parse import urlencode
    query = urlencode({
        "client_id": os.environ["PLANNING_CENTER_CLIENT_ID"],
        "redirect_uri": url_for("worship_slides.planning_center_callback", _external=True),
        "response_type": "code",
        "scope": "services",
        "state": state,
    })
    return redirect("https://api.planningcenteronline.com/oauth/authorize?" + query)


@worship_slides_bp.route("/connect/planning-center/callback")
@staff_only
def planning_center_callback():
    expected = session.pop("slides_pco_oauth_state", "")
    if request.args.get("error"):
        return redirect(url_for("worship_slides.workspace", setup="planning-center"))
    if not request.args.get("code") or not hmac.compare_digest(request.args.get("state", ""), expected):
        abort(400)
    import requests
    response = requests.post("https://api.planningcenteronline.com/oauth/token", data={
        "grant_type": "authorization_code",
        "code": request.args["code"],
        "redirect_uri": url_for("worship_slides.planning_center_callback", _external=True),
        "client_id": os.getenv("PLANNING_CENTER_CLIENT_ID", ""),
        "client_secret": os.getenv("PLANNING_CENTER_CLIENT_SECRET", ""),
    }, timeout=20)
    if not response.ok:
        current_app.logger.warning("Planning Center worship OAuth failed: %s", response.status_code)
        return redirect(url_for("worship_slides.workspace", setup="planning-center"))
    token = response.json()
    token["expires_at"] = time.time() + token.get("expires_in", 3600)
    _save_token(PCO_TOKEN_KEY, token)
    return redirect(url_for("worship_slides.workspace", connected="planning-center"))


@worship_slides_bp.route("/connect/google")
@staff_only
def connect_google():
    try:
        state = uuid.uuid4().hex
        session["slides_google_oauth_state"] = state
        target = google_authorize_url(state, url_for("worship_slides.google_callback", _external=True))
        return redirect(target)
    except IntegrationError:
        return redirect(url_for("worship_slides.workspace", setup="google"))


@worship_slides_bp.route("/connect/google/callback")
@staff_only
def google_callback():
    expected = session.pop("slides_google_oauth_state", "")
    if request.args.get("error"):
        return redirect(url_for("worship_slides.workspace", setup="google"))
    if not request.args.get("code") or not hmac.compare_digest(request.args.get("state", ""), expected):
        abort(400)
    try:
        token = exchange_google_code(request.args["code"], url_for("worship_slides.google_callback", _external=True))
        token["expires_at"] = time.time() + token.get("expires_in", 3600)
        old_token = _get_token(GOOGLE_TOKEN_KEY)
        if old_token and not token.get("refresh_token"):
            token["refresh_token"] = old_token.get("refresh_token")
        _save_token(GOOGLE_TOKEN_KEY, token)
    except IntegrationError:
        return redirect(url_for("worship_slides.workspace", setup="google"))
    return redirect(url_for("worship_slides.workspace", connected="google"))


@worship_slides_bp.route("/disconnect/<provider>", methods=["POST"])
@staff_only
def disconnect(provider):
    if not _csrf_ok():
        abort(400)
    key = {"planning-center": PCO_TOKEN_KEY, "google": GOOGLE_TOKEN_KEY}.get(provider)
    if not key:
        abort(404)
    _delete_token(key)
    return redirect(url_for("worship_slides.workspace"))


@worship_slides_bp.route("/api/service-types")
@staff_only
def api_service_types():
    try:
        entries = list_service_types(_pco_access_token())
        return jsonify([{"id": row["id"], "name": row.get("attributes", {}).get("name", "Service type")} for row in entries])
    except IntegrationError as exc:
        return jsonify({"error": str(exc)}), 400


@worship_slides_bp.route("/api/plans/<service_type_id>")
@staff_only
def api_plans(service_type_id):
    try:
        plans = list_plans(_pco_access_token(), service_type_id)
        return jsonify([{
            "id": plan["id"],
            "title": plan.get("attributes", {}).get("title") or "Untitled plan",
            "date": plan.get("attributes", {}).get("sort_date"),
        } for plan in plans])
    except IntegrationError as exc:
        return jsonify({"error": str(exc)}), 400


@worship_slides_bp.route("/api/plan/<service_type_id>/<plan_id>")
@staff_only
def api_plan(service_type_id, plan_id):
    try:
        return jsonify(get_plan_items(_pco_access_token(), service_type_id, plan_id))
    except IntegrationError as exc:
        return jsonify({"error": str(exc)}), 400


@worship_slides_bp.route("/api/create", methods=["POST"])
@staff_only
def api_create():
    if not _csrf_ok():
        abort(400)
    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "").strip()[:160]
    items = payload.get("items")
    outputs = payload.get("outputs")
    if not title or not isinstance(items, list) or not items or len(items) > 100:
        return jsonify({"error": "Add a title and at least one service item."}), 400
    safe_items = []
    for item in items:
        if not isinstance(item, dict):
            continue
        safe_items.append({"title": str(item.get("title", ""))[:300], "content": str(item.get("content", ""))[:10000]})
    if not safe_items:
        return jsonify({"error": "There are no usable service items to publish."}), 400
    if not isinstance(outputs, list) or not outputs or any(x not in ("slides", "doc") for x in outputs):
        return jsonify({"error": "Choose Google Slides, Google Docs, or both."}), 400
    token = _get_token(GOOGLE_TOKEN_KEY)
    if not token:
        return jsonify({"error": "Connect Google Drive before creating files."}), 400
    created = {}
    try:
        token = google_access_token(token)
        for output in outputs:
            created[output] = (
                create_google_presentation(token, title, safe_items)
                if output == "slides" else create_google_doc(token, title, safe_items)
            )
        _save_token(GOOGLE_TOKEN_KEY, token)
    except IntegrationError as exc:
        _save_token(GOOGLE_TOKEN_KEY, token)
        return jsonify({"error": str(exc), "created": created}), 502
    return jsonify({"created": created})
