from typing import TYPE_CHECKING, Optional
from datetime import datetime
from sqlalchemy_json import NestedMutableJson
from sqlalchemy.orm import declarative_mixin, declared_attr
import sqlalchemy as sa
from .helpers import get_jembewf

if TYPE_CHECKING:
    import jembewf

__all__ = ("StepMixin",)


@declarative_mixin
class StepMixin:
    """Mixin to be applied to Step SqlAlchemy model

    Step model keep track of all instances of tasks in flows (current and completed)
    and it's local variables and states.

    StepMixin should be applied class extended from
    flask_sqlalchemy.SqlAlchemy().Model who defines model in database
    """

    __process_table_name__: str = "jwf_processes"
    __process_class_name__: str = "Process"

    __tablename__ = "jwf_steps"

    id = sa.Column(sa.Integer, primary_key=True)

    # process
    @declared_attr
    def process_id(cls):
        """Foreign key to Process table"""
        return sa.Column(
            sa.Integer,
            sa.ForeignKey(f"{cls.get_process_table_name()}.id"),
            nullable=False,
        )

    @declared_attr
    def process(cls):
        """Defines process relationship"""
        return sa.orm.relationship(
            cls.get_process_class_name(),
            foreign_keys=[cls.process_id],
            back_populates="steps",
        )

    task_name = sa.Column(sa.String(250), nullable=False)

    is_active = sa.Column(
        sa.Boolean(), nullable=False, default=True, server_default=sa.true()
    )
    is_last_step = sa.Column(
        sa.Boolean(), nullable=False, default=False, server_default=sa.false()
    )

    # step/task variables
    variables = sa.Column(NestedMutableJson)

    started_at = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=False)
    ended_at = sa.Column(sa.DateTime)

    # prev_step, next_step

    @declared_attr
    def prev_step_id(cls):
        return sa.Column(
            sa.Integer,
            sa.ForeignKey(f"{cls.__tablename__}.id"),
        )

    @declared_attr
    def prev_step(cls):
        return sa.orm.relationship(
            f"{cls.__name__}", remote_side=[cls.id], foreign_keys=[cls.prev_step_id]
        )

    @property
    def task(self) -> "jembewf.Task":
        """Returns Task definition of the step"""
        return self.process.flow.tasks[self.task_name]

    @property
    def callback(self) -> "jembewf.TaskCallback":
        """TaskCallback of the task instance"""
        return self.task.callback(self)

    @classmethod
    def create(
        cls,
        process: "jembewf.ProcessMixin",
        task: "jembewf.Task",
        prev_step: Optional["jembewf.StepMixin"] = None,
        transition_callback: Optional["jembewf.TransitionCallback"] = None,
        **step_vars,
    ) -> "jembewf.StepMixin":
        """Creates step instance in process for the task

        Args:
            process (jembewf.ProcessMixin): Process instance to whome the step will belong
            task (jembewf.Task): Task instance for wichin we create the step
            from_step (Optional[jembewf.StepMixin]): previous step

        Returns:
            jembewf.StepMixin: _description_
        """
        jwf = get_jembewf()
        step = jwf.step_model()
        step.task_name = task.name
        step.process = process
        step.variables = step_vars
        if prev_step:
            step.prev_step = prev_step
        step.is_last_step = len(task.transitions) == 0

        jwf.db.session.add(step)
        jwf.db.session.commit()

        if transition_callback:
            transition_callback.callback(step)

        step.callback.callback()

        if step.is_last_step:
            step.is_active = False
            step.ended_at = datetime.utcnow()
            jwf.db.session.add(step)
            jwf.db.session.commit()
        elif step.task.auto_proceed:
            step.proceed()

        return step

    def proceed(self, transition: Optional["jembewf.Transition"] = None) -> bool:
        """Proceed process with transition from this step

        Args:
            transition (Optional[&quot;jembewf.Transition&quot;], optional):
                Transition to proceed.
                If transition is None than proceed with every transition on this step.
                Defaults to None.

        TODO return reason why transition cann't proceed

        Raises:
            ValueError: When transition is not part of this step.
        Returns:
            bool: True when process proceed, False if its not

        """
        # check if this is not last step and is active
        if self.is_last_step or not self.is_active:
            return False

        proceeded = False

        if transition and transition not in self.task.transitions:
            raise ValueError(
                f"Transition '{transition}' is not transition from task '{self.task}'"
            )
        transitions = [transition] if transition else self.task.transitions

        for trans in transitions:
            transition_callback = trans.callback(trans, self)
            if transition_callback.can_proceed():
                self.create(self.process, trans.to_task, self, transition_callback)
                proceeded = True

        if proceeded:
            self.is_active = False
            self.ended_at = datetime.utcnow()
            jwf = get_jembewf()
            jwf.db.session.add(self)
            jwf.db.session.commit()
            self.process.check_is_running()

        return proceeded

    def can_proceed(self, transition: Optional["jembewf.Transition"] = None) -> bool:
        """Check if process can proceed

        Args:
            transition (Optional[&quot;jembewf.Transition&quot;], optional):
                Check if process can proceed with this transition.
                If transition is None than check with every transition on this step.
                Defaults to None.

        TODO return reason why transition cann't proceed

        Raises:
            ValueError: When transition is not part of this step.
        Returns:
            bool: True when process can proceed, False if it cannot
        """
        if transition and transition not in self.task.transitions:
            raise ValueError(
                f"Transition '{transition}' is not transition from task '{self.task}'"
            )
        transitions = [transition] if transition else self.task.transitions

        for trans in transitions:
            transition_callback = trans.callback(trans, self)
            if transition_callback.can_proceed():
                return True
        return False

    @classmethod
    def get_process_table_name(cls) -> str:
        """Returns name of Process table defined in cls.__process_table_name__

        It's used to create relationship between steps and processes.
        """
        try:
            return cls.__process_table_name__
        except AttributeError as err:
            raise AttributeError(
                f"Attribute __process_table_name__ for '{cls.__name__}' is not defined"
            ) from err

    @classmethod
    def get_process_class_name(cls) -> str:
        """Returns name of Process class defined in cls.__process_class_name__

        It's used to create relationship between steps and processes.
        """
        try:
            return cls.__process_class_name__
        except AttributeError as err:
            raise AttributeError(
                f"Attribute __process_class_name__ for '{cls.__name__}' is not defined"
            ) from err

    def __repr__(self):
        return f"<Step #{self.id}: '{self.task_name}' from process #{self.process_id}: '{self.process.flow_name}'>"
