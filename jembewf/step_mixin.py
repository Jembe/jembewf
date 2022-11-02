from typing import TYPE_CHECKING, Optional, Union
from datetime import datetime
from sqlalchemy_json import NestedMutableJson
from sqlalchemy.orm import declarative_mixin, declared_attr
import sqlalchemy as sa
from .helpers import CanProceed, get_jembewf

if TYPE_CHECKING:
    import jembewf

__all__ = ("StepMixin",)


@declarative_mixin
class StepMixin:
    """Mixin to be applied to Step SqlAlchemy model

    Step model keep track of all instances of states in flows (current and completed)
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

    state_name = sa.Column(sa.String(250), nullable=False)

    is_active = sa.Column(
        sa.Boolean(), nullable=False, default=True, server_default=sa.true()
    )
    is_last_step = sa.Column(
        sa.Boolean(), nullable=False, default=False, server_default=sa.false()
    )

    # step/state variables
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
    def state(self) -> "jembewf.State":
        """Returns State definition of the step"""
        return self.process.flow.states[self.state_name]

    @property
    def callback(self) -> "jembewf.StateCallback":
        """StateCallback of the state instance"""
        return self.state.callback(self)

    @classmethod
    def create(
        cls,
        process: "jembewf.ProcessMixin",
        state: "jembewf.State",
        prev_step: Optional["jembewf.StepMixin"] = None,
        transition_callback: Optional["jembewf.TransitionCallback"] = None,
        **step_vars,
    ) -> "jembewf.StepMixin":
        """Creates step instance in process for the state

        Args:
            process (jembewf.ProcessMixin): Process instance to whome the step will belong
            state (jembewf.State): State instance for wichin we create the step
            from_step (Optional[jembewf.StepMixin]): previous step

        Returns:
            jembewf.StepMixin: _description_
        """
        jwf = get_jembewf()
        step = jwf.step_model()
        step.state_name = state.name
        step.process = process
        step.variables = step_vars
        if prev_step:
            step.prev_step = prev_step
        step.is_last_step = len(state.transitions) == 0

        jwf.db.session.add(step)

        if transition_callback:
            transition_callback.callback(step)

        step.callback.callback()

        if step.is_last_step:
            step.is_active = False
            step.ended_at = datetime.utcnow()
            jwf.db.session.add(step)
        elif step.state.auto_proceed:
            step.proceed()

        return step

    def proceed(
        self,
        transition: Optional["jembewf.Transition"] = None,
        **transition_params
    ) -> Union[bool, "jembewf.CanProceed"]:
        """Proceed process with transition from this step

        Args:
            transition (Optional[&quot;jembewf.Transition&quot;], optional):
                Transition to proceed.
                If transition is None than proceed with every transition on this step.
                Defaults to None.

        Raises:
            ValueError: When transition is not part of this step.

        Returns:
            Union[bool, jembewf.CanProceed]: Returns True if process can proceed or
                CanProceed instanace with concated reasons if process can't proceed.
        """
        # check if this is not last step and is active
        if self.is_last_step or not self.is_active:
            return False

        if transition and transition not in self.state.transitions:
            raise ValueError(
                f"Transition '{transition}' is not transition from state '{self.state}'"
            )
        transitions = [transition] if transition else self.state.transitions

        proceeded = False
        cannot_proceed = CanProceed(False)
        for trans in transitions:
            transition_callback = trans.callback(trans, self, **transition_params)
            if can_proceed := transition_callback.can_proceed():
                self.create(self.process, trans.to_state, self, transition_callback)
                proceeded = True
            else:
                cannot_proceed.append_reason(can_proceed)

        if proceeded:
            self.is_active = False
            self.ended_at = datetime.utcnow()
            jwf = get_jembewf()
            jwf.db.session.add(self)
            self.process.check_is_running()

        return proceeded if proceeded else cannot_proceed

    def can_proceed(
        self, transition: Optional["jembewf.Transition"] = None
    ) -> Union[bool, "jembewf.CanProceed"]:
        """Check if process can proceed

        When 'transition' is provided, check if process can proceed folowing
        that transition.
        When 'transisition' is not provided, check if process can proceed following
        any transition from the this step.

        Args:
            transition (Optional[&quot;jembewf.Transition&quot;], optional):
                Check if process can proceed with this transition.
                If transition is None than check with every transition on this step.
                Defaults to None.

        Raises:
            ValueError: When transition is not part of this step.
        Returns:
            Union[bool, jembewf.CanProceed]: Returns True if process can proceed or
                CanProceed instanace with concated reasons if process can't proceed.
        """
        if transition and transition not in self.state.transitions:
            raise ValueError(
                f"Transition '{transition}' is not transition from state '{self.state}'"
            )
        transitions = [transition] if transition else self.state.transitions

        cannot_proceed = CanProceed(False)
        for trans in transitions:
            transition_callback = trans.callback(trans, self)
            if can_proceed := transition_callback.can_proceed():
                return True
            cannot_proceed.append_reason(can_proceed)
        return cannot_proceed

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
        return f"<Step #{self.id}: '{self.state_name}' from process #{self.process_id}: '{self.process.flow_name}'>"
