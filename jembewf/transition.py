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
        self.from_state = transition.from_state
        self.to_state = transition.to_state
        self.flow = transition.flow

        if transition.flow != self.process.flow:
            raise Exception(
                f"Transition flow '{transition.flow.name}'  "
                f"and Process flow '{self.process.flow}' are not equal when "
                f" proceeding from step '{self.from_state.name}' to '{self.to_state.name}'."
            )

    def can_proceed(self) -> bool:
        """Check if a transition is ready proceed to next step/state.

        Default returns True.

        Override this method to implement check to see if all contitions
        for proceeding to next state are meet.

        If you want to autamticaly proceed to next state then override this
        method and return True.
        """
        return True

    def callback(self, to_step: "jembewf.StepMixin"):
        """Called when transiting to the to_state/step"""


class Transition:
    """Defines and configures Transition"""

    def __init__(
        self,
        to_state_name: str,
        callback: Optional[Type["jembewf.TransitionCallback"]] = None,
        **config,
    ) -> None:
        self.to_state_name = to_state_name
        self.callback: Type[TransitionCallback] = (
            callback if callback is not None else TransitionCallback
        )
        self.config = config

        self.flow: "jembewf.Flow"
        self.from_state: "jembewf.State"
        self.to_state: "jembewf.State"
        # Unique transition name automaticly set when attached to state
        self.name: str

        self.validate = False

    def attach_to_from_state(self, state: "jembewf.State"):
        """Attach to the State"""
        self.from_state = state
        self.flow = state.flow
        self.to_state = self.flow.states[self.to_state_name]
        transition_id = state.transitions.index(self)
        self.name = f"{self.from_state.name} -- {transition_id}"
        self._validate()

    def _validate(self):
        if not hasattr(self, "from_state"):
            raise Exception(
                f"Transition '{self.name}' is not attached to the from_state"
            )
        if not hasattr(self, "to_state"):
            raise Exception(
                f"Transition '{self.name}' is not associated with the to_state"
            )
        if not hasattr(self, "flow"):
            raise Exception(f"Transition '{self.name}' is not associated with the flow")
        self.validate = True
