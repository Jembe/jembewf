from typing import TYPE_CHECKING, Dict, Optional, Type
import json
from .flow import Flow, FlowCallback
from .task import Task, TaskCallback
from .transition import Transition, TransitionCallback
from .process_mixin import ProcessMixin, CantStartProcess
from .step_mixin import StepMixin
from .helpers import get_jembewf


if TYPE_CHECKING:
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    import jembewf


__all__ = (
    "get_jembewf",
    "JembeWF",
    "Flow",
    "FlowCallback",
    "Task",
    "TaskCallback",
    "Transition",
    "TransitionCallback",
    "ProcessMixin",
    "StepMixin",
    "CantStartProcess",
)


class JembeWF:
    """Jembe Workflow Management extension for Flask framework"""

    def __init__(
        self,
        app: Optional["Flask"] = None,
        db: Optional["SQLAlchemy"] = None,
        process_model: Optional[Type["jembewf.ProcessMixin"]] = None,
        step_model: Optional[Type["jembewf.StepMixin"]] = None,
    ) -> None:

        self.flows: Dict[str, "jembewf.Flow"] = {}
        self.initialised = False

        self.db: "SQLAlchemy"
        if db is not None:
            self.db = db

        self.process_model: Type["jembewf.ProcessMixin"]
        if process_model is not None:
            self.process_model = process_model

        self.step_model: Type["jembewf.StepMixin"]
        if step_model is not None:
            self.step_model = step_model

        if app is not None:
            if process_model is None or step_model is None or db is None:
                raise Exception(
                    "When you provide app parameter then "
                    "db, process_model and step_model must also be provided in other to initialise JembeWf."
                )
            self.init_app(app, self.db, self.process_model, self.step_model)

    def init_app(
        self,
        app: "Flask",
        db: Optional["SQLAlchemy"] = None,
        process_model: Optional[Type["jembewf.ProcessMixin"]] = None,
        step_model: Optional[Type["jembewf.StepMixin"]] = None,
    ) -> None:
        """Initialize JembeWF Flask extension

        Args:
            app (Flask): Flask instance
        """
        if "jembewf" in app.extensions:
            raise Exception("JembeWF is already registred at Flask app")
        # check if db is provided
        if db is None and not hasattr(self, "db"):
            raise Exception("JembeWF 'db' must be provided in __init__ or in init_app")
        if db is not None:
            self.db = db

        # check if process_model is provided
        if process_model is None and not hasattr(self, "process_model"):
            raise Exception(
                "JembeWF 'process_model' must be provided in __init__ or in init_app"
            )
        if process_model is not None:
            self.process_model = process_model

        # check if step_model is provided
        if step_model is None and not hasattr(self, "step_model"):
            raise Exception(
                "JembeWF 'step_model' must be provided in __init__ or in init_app"
            )
        if step_model is not None:
            self.step_model = step_model

        # initialise extension
        app.extensions["jembewf"] = self
        self.initialised = True

    def add(self, *flows: "jembewf.Flow") -> "jembewf.JembeWF":
        """Add/Register Flow definition"""
        if self.initialised:
            raise Exception(
                "Can't add flows to JembeWF because it is already initialised."
            )

        for flow in flows:
            if flow.name in self.flows:
                raise Exception(
                    f"Flow with same name '{flow.name}' is already registred."
                )
            self.flows[flow.name] = flow
        return self

    def start(self, flow_name: str, **process_vars) -> "jembewf.ProcessMixin":
        """Start Process instance from Flow definition

        Returns Process instance that has been started.
        """
        return self.process_model.create(flow_name, **process_vars)

    def can_start(self, flow_name: str, **process_vars) -> bool:
        """Check if process from flow definition can be started"""
        return self.process_model.can_start(flow_name, **process_vars)
