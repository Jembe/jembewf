from typing import TYPE_CHECKING, Type, Dict, Optional, List, Union

if TYPE_CHECKING:
    import jembewf

__all__ = ("Flow", "FlowCallback")


class FlowCallback:
    """Provides business logic for starting the flow to which is attached to.

    Extend this class and override methods to provide custom business logic
    """

    def __init__(self, process: "jembewf.ProcessMixin"):
        self.process = process

        self.flow = process.flow

    def can_start(self) -> Union[bool, "jembewf.CanProceed"]:
        """Check if a flow can be started. Default returns True

        Returns:
            Union[bool, jembewf.CanProceed]: True if flow can start.
                You can attach reason  why flow cannt start
                by returing instance of jembewf.CanProceed. Default returns True.
        """
        return True

    def callback(self):
        """Called right after process is created and before startit transitions"""


class Flow:
    """Defines and configures Flow"""

    def __init__(
        self,
        name: str,
        callback: Optional[Type["jembewf.FlowCallback"]] = None,
        **config,
    ) -> None:
        self.name = name
        self.callback: Type[FlowCallback] = callback if callback else FlowCallback
        self.config = config

        # list of all states that belongs to this workflow
        self.states: Dict[str, "jembewf.State"] = {}
        self.starts_with_states: List[str] = []
        self.ends_with_states: List[str] = []

        self.validated = False

    def start_with(self, *state_names: str) -> "jembewf.Flow":
        """Define state names that will be executed when flow starts

        Flow must call start_with in order to have valid and complet definition.
        """
        # at least one state_name
        if len(state_names) == 0:
            raise Exception(
                f"At least one state_name must be provided to flow '{self.name}'."
            )

        # state with provided names exist
        for state_name in state_names:
            if state_name not in self.states:
                raise Exception(
                    f"State with name '{state_name}' doesn't exist in flow '{self.name}'."
                )
        self.starts_with_states = list(state_names)

        # Associate from_state, to_state, and flow inside transitions
        # Can't be done earlier because we need to define have
        # all states defined to associate to_state
        for state in self.states.values():
            for transition in state.transitions:
                transition.attach_to_from_state(state)

        self._validate_flow()
        return self

    def add(self, *states: "jembewf.State") -> "jembewf.Flow":
        """Add States to flow

        Returns:
            jembewf.Flow: returns self
        """
        for state in states:
            if state.name in self.states:
                raise Exception(
                    f"State '{state.name}' already exist in flow '{self.name}'."
                )

            state.attach_to_flow(self)
            self.states[state.name] = state
            if len(state.transitions) == 0:
                self.ends_with_states.append(state.name)
        return self

    def _validate_flow(self):
        if len(self.states) == 0:
            Exception(f"Flow '{self.name} have no states.")

        if len(self.starts_with_states) == 0:
            Exception(
                f"Flow '{self.name} have no start states defined. "
                "Use Flow.start_with to define start states."
            )

        if len(self.ends_with_states) == 0:
            Exception(
                f"Flow '{self.name} have no endstates. States are making infinite loop"
            )

        # check if all transitions  lead to to the existing state_name
        for state in self.states.values():
            for transition in state.transitions:
                if transition.to_state_name not in self.states:
                    raise Exception(
                        f"Transition from state '{state.name}' "
                        f"in flow '{self.name}' leads to non existing "
                        f"state '{transition.to_state_name}'."
                    )
        self.validated = True
