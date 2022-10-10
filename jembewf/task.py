from typing import TYPE_CHECKING, Optional, Type, List

if TYPE_CHECKING:
    import jembewf

__all__ = ("Task", "TaskCallback")


class TaskCallback:
    """Provides business logic for the Task to which is attached to.

    Extend this class and override methods to provide custom business logic.
    """

    def __init__(self, step: "jembewf.StepMixin"):
        self.step = step
        self.process = step.process

        self.task = step.task
        self.flow = self.task.flow

    def callback(self):
        """Called on arrive to the task"""


class Task:
    """Defines and configures Task"""

    def __init__(
        self,
        name: str,
        callback: Optional[Type["jembewf.TaskCallback"]] = None,
        **config,
    ) -> None:
        self.name = name
        self.callback: Type[TaskCallback] = (
            callback if callback is not None else TaskCallback
        )
        self.config = config
        self.auto_proceed = False

        # list of all transitions that belogns to this task
        self.transitions: List["jembewf.Transition"] = []

        self.flow: "jembewf.Flow"

        self.validate = False

    def add(self, *transitions: "jembewf.Transition") -> "jembewf.Task":
        """Adds transition to the task"""
        self.transitions.extend(transitions)
        return self

    def auto(self) -> "jembewf.Task":
        """Task will proceed automaticaly to its transition when Step is created"""
        self.auto_proceed = True
        return self

    def attach_to_flow(self, flow: "jembewf.Flow"):
        """Attach task to the Flow"""
        self.flow = flow
        self._validate()

    def _validate(self):
        if not hasattr(self, "flow"):
            raise Exception(f"Task '{self.name}' is not attached to the flow")
        self.validate = True
