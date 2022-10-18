from typing import TYPE_CHECKING, Optional, Type, List

if TYPE_CHECKING:
    import jembewf

__all__ = ("State", "StateCallback")


class StateCallback:
    """Provides business logic for the State to which is attached to.

    Extend this class and override methods to provide custom business logic.
    """

    def __init__(self, step: "jembewf.StepMixin"):
        self.step = step
        self.process = step.process

        self.state = step.state
        self.flow = self.state.flow

    def callback(self):
        """Called on arrive to the state"""


class State:
    """Defines and configures State"""

    def __init__(
        self,
        name: str,
        callback: Optional[Type["jembewf.StateCallback"]] = None,
        **config,
    ) -> None:
        self.name = name
        self.callback: Type[StateCallback] = (
            callback if callback is not None else StateCallback
        )
        self.config = config
        self.auto_proceed = False

        # list of all transitions that belogns to this state
        self.transitions: List["jembewf.Transition"] = []

        self.flow: "jembewf.Flow"

        self.validate = False

    def add(self, *transitions: "jembewf.Transition") -> "jembewf.State":
        """Adds transition to the state"""
        self.transitions.extend(transitions)
        return self

    def auto(self) -> "jembewf.State":
        """State will proceed automaticaly to its transition when Step is created"""
        self.auto_proceed = True
        return self

    def attach_to_flow(self, flow: "jembewf.Flow"):
        """Attach state to the Flow"""
        self.flow = flow
        self._validate()

    def _validate(self):
        if not hasattr(self, "flow"):
            raise Exception(f"State '{self.name}' is not attached to the flow")
        self.validate = True

    def get_transition(self, transition_name: str) -> "jembewf.Transition":
        """Get current state transition by transition name"""
        try:
            return next(
                trans for trans in self.transitions if trans.name == transition_name
            )
        except StopIteration:
            raise ValueError(
                f"Transition {transition_name} does not exist in state '{self.name}'!"
            ) from StopIteration

    def has_transition(self, transition_name: str) -> bool:
        """Check if transition exsist"""
        try:
            next(trans for trans in self.transitions if trans.name == transition_name)
            return True
        except StopIteration:
            return False
