from typing import TYPE_CHECKING, Dict, Optional
from flask import current_app
from .flow_def import FlowDef


if TYPE_CHECKING:
    from flask import Flask
    import jembewf

__all__ = (
    "get_jembewf",
    "JembeWF",
    "FlowDef",
)


class JembeWF:
    """Jembe Workflow Management extension for Flask framework"""

    def __init__(self, app: Optional["Flask"] = None) -> None:
        self._flow_definitions: Dict[str, "jembewf.FlowDef"] = {}
        if app is not None:
            self.init_app(app)

    def init_app(self, app: "Flask") -> None:
        """Initialize JembeWF Flask extension

        Args:
            app (Flask): Flask instance
        """

        if "jembewf" in app.extensions:
            raise Exception("JembeWF is already registred at Flask app")

        app.extensions["jembewf"] = self

    def add_flow(self, flow_def: "jembewf.FlowDef"):
        """Register Process Flow definition"""
        if flow_def.name in self._flow_definitions:
            raise Exception(
                f"Flow with same name '{flow_def.name}' is already registred."
            )
        self._flow_definitions[flow_def.name] = flow_def

    def flow(self):
        """Decorator that register Process Flow Definition"""

        def decorator(flow_def: "jembewf.FlowDef"):
            self.add_flow(flow_def)
            return flow_def

        return decorator


def get_jembewf() -> "jembewf.JembeWF":
    """Returns instance of JembeWf for current Flask application"""
    jembewf_instance = current_app.extensions.get("jembewf", None)
    if jembewf_instance is None:
        raise Exception("JembeWF extension is not initialised")
    return jembewf_instance
