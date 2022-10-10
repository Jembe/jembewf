from typing import TYPE_CHECKING, Optional, Type

if TYPE_CHECKING:
    import jembewf

__all__ = ("Transition", "TransitionCallback")


class TransitionCallback:
    """Provides business logic for the Transition to which is attached to.

    Extend this class and override methods to provide custom business logic.
    """

    def __init__(
        self,
        transition: "jembewf.Transition",
        from_step: "jembewf.StepMixin",
    ):
        self.from_step = from_step
        self.process = from_step.process

        self.transition = transition
        self.from_task = transition.from_task
        self.to_task = transition.to_task
        self.flow = transition.flow

        if transition.flow != self.process.flow:
            raise Exception(
                f"Transition flow '{transition.flow.name}'  "
                f"and Process flow '{self.process.flow}' are not equal when "
                f" proceeding from step '{self.from_task.name}' to '{self.to_task.name}'."
            )

    def can_proceed(self) -> bool:
        """Check if a transition is ready proceed to next step/task.

        Default returns True.

        Override this method to implement check to see if all contitions
        for proceeding to next task are meet.

        If you want to autamticaly proceed to next task then override this
        method and return True.
        """
        return True

    def callback(self, to_step: "jembewf.StepMixin"):
        """Called when transiting to the to_task/step"""


class Transition:
    """Defines and configures Transition"""

    def __init__(
        self,
        to_task_name: str,
        callback: Optional[Type["jembewf.TransitionCallback"]] = None,
        **config,
    ) -> None:
        self.to_task_name = to_task_name
        self.callback: Type[TransitionCallback] = (
            callback if callback is not None else TransitionCallback
        )
        self.config = config

        self.flow: "jembewf.Flow"
        self.from_task: "jembewf.Task"
        self.to_task: "jembewf.Task"

        self.validate = False

    def attach_to_from_task(self, task: "jembewf.Task"):
        """Attach to the Task"""
        self.from_task = task
        self.flow = task.flow
        self.to_task = self.flow.tasks[self.to_task_name]
        self._validate()

    def _validate(self):
        if not hasattr(self, "from_task"):
            raise Exception(
                f"Transition '{self.name}' is not attached to the from_task"
            )
        if not hasattr(self, "to_task"):
            raise Exception(
                f"Transition '{self.name}' is not associated with the to_task"
            )
        if not hasattr(self, "flow"):
            raise Exception(f"Transition '{self.name}' is not associated with the flow")
        self.validate = True
