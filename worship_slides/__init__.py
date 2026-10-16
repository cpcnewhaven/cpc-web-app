"""Isolated worship planning and Google Workspace publishing feature."""

from flask import Blueprint

worship_slides_bp = Blueprint(
    "worship_slides",
    __name__,
    url_prefix="/slides",
    template_folder="templates",
    static_folder="static",
)

from . import routes  # noqa: E402,F401
