from typing import TYPE_CHECKING
from flask import current_app

if TYPE_CHECKING:
    import jembewf

__all__ = ("get_jembewf",)


def get_jembewf() -> "jembewf.JembeWF":
    """Returns instance of JembeWf for current Flask application"""
    jembewf_instance = current_app.extensions.get("jembewf", None)
    if jembewf_instance is None:
        raise Exception("JembeWF extension is not initialised")
    return jembewf_instance
