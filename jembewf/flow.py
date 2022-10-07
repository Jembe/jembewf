from typing import TYPE_CHECKING, Type, Dict, Optional, List

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

    def can_start(self) -> bool:
        """Check if a flow can be started. Default returns True"""
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

        # list of all tasks that belongs to this workflow
        self.tasks: Dict[str, "jembewf.Task"] = {}
        self.starts_with_tasks: List[str] = []
        self.ends_with_tasks: List[str] = []

        self.validated = False

    def start_with(self, *task_names: str) -> "jembewf.Flow":
        """Define task names that will be executed when flow starts

        Flow must call start_with in order to have valid and complet definition.
        """
        # at least one task_name
        if len(task_names) == 0:
            raise Exception(
                f"At least one task_name must be provided to flow '{self.name}'."
            )

        # task with provided names exist
        for task_name in task_names:
            if task_name not in self.tasks:
                raise Exception(
                    f"Task with name '{task_name}' doesn't exist in flow '{self.name}'."
                )
        self.starts_with_tasks = list(task_names)


        # Associate from_task, to_task, and flow inside transitions
        # Can't be done earlier because we need to define have
        # all tasks defined to associate to_task 
        for task in self.tasks.values():
            for transition in task.transitions:
                transition.attach_to_from_task(task)

        self._validate_flow()
        return self

    def add(self, *tasks: "jembewf.Task") -> "jembewf.Flow":
        """Add Tasks to flow

        Returns:
            jembewf.Flow: returns self
        """
        for task in tasks:
            if task.name in self.tasks:
                raise Exception(
                    f"Task '{task.name}' already exist in flow '{self.name}'."
                )

            task.attach_to_flow(self)
            self.tasks[task.name] = task
            if len(task.transitions) == 0:
                self.ends_with_tasks.append(task.name)
        return self

    def _validate_flow(self):
        if len(self.tasks) == 0:
            Exception(f"Flow '{self.name} have no tasks.")

        if len(self.starts_with_tasks) == 0:
            Exception(
                f"Flow '{self.name} have no start tasks defined. "
                "Use Flow.start_with to define start tasks."
            )

        if len(self.ends_with_tasks) == 0:
            Exception(
                f"Flow '{self.name} have no endtasks. Tasks are making infinite loop"
            )

        # check if all transitions  lead to to the existing task_name
        for task in self.tasks.values():
            for transition in task.transitions:
                if transition.to_task_name not in self.tasks:
                    raise Exception(
                        f"Transition from task '{task.name}' "
                        f"in flow '{self.name}' leads to non existing "
                        f"task '{transition.to_task_name}'."
                    )
        self.validated = True
