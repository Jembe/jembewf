from typing import TYPE_CHECKING, List
from datetime import datetime
from sqlalchemy_json import NestedMutableJson
from sqlalchemy.orm import declarative_mixin, declared_attr, object_session
import sqlalchemy as sa
from .helpers import get_jembewf


if TYPE_CHECKING:
    import jembewf

__all__ = ("ProcessMixin", "CantStartProcess")


class CantStartProcess(Exception):
    """Exception raised when process can't be started"""


@declarative_mixin
class ProcessMixin:
    """Mixin to be applied to Process SqlAlchemy model

    Process model keep track of all instances of flows (current and completed)
    it global variables and states.

    ProcessMixin should be applied class extended from
    flask_sqlalchemy.SqlAlchemy().Model who defines model in database
    """

    __tablename__ = "jwf_processes"

    __step_table_name__: str = "jwf_steps"
    __step_class_name__: str = "Step"

    id = sa.Column(sa.Integer, primary_key=True)

    flow_name = sa.Column(sa.String(250), nullable=False)

    is_running = sa.Column(
        sa.Boolean(), nullable=False, default=True, server_default=sa.true()
    )

    # process variables
    variables = sa.Column(NestedMutableJson)

    started_at = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=False)
    ended_at = sa.Column(sa.DateTime)

    @declared_attr
    def steps(cls):
        return sa.orm.relationship(
            cls.get_step_class_name(),
            foreign_keys=f"{cls.get_step_class_name()}.process_id",
            back_populates="process",
            order_by=f"{cls.get_step_class_name()}.id",
        )

    def current_steps(self) -> List["jembewf.StepMisin"]:
        """Returns current active process steps"""
        session = object_session(self)
        step = get_jembewf().step_model
        return list(session.query(step).filter(step.is_active == True).all())

    def last_steps(self) -> List["jembewf.StepMisin"]:
        """Returns last steps of the process"""
        session = object_session(self)
        step = get_jembewf().step_model
        return list(session.query(step).filter(step.is_last_step == True).all())

    @property
    def flow(self) -> "jembewf.Flow":
        """Flow of the process instance"""
        return get_jembewf().flows[self.flow_name]

    @property
    def callback(self) -> "jembewf.FlowCallback":
        """FlowCallback of the process instance"""
        return self.flow.callback(self)

    @classmethod
    def can_start(cls, flow_name: str, **process_vars) -> bool:
        """Checks if process can be started

        Args:
            flow_name (str): name of the flow for witch we are doing check
            process_vars: global process variables

        Raises:
            ValueError: Can't start flow because it does not exist!

        Returns:
            bool: True if process can be started
        """
        process = cls._create_process(flow_name, **process_vars)
        return process.callback.can_start()

    @classmethod
    def create(cls, flow_name: str, **process_vars) -> "jembewf.ProcessMixin":
        """Creates process instance for flow named flow_name

        Args:
            flow_name (str): name of the flow for witch we are creating the process
            process_vars: global process variables

        Raises:
            ValueError: Can't create process because flow does not exist!

        Returns:
            jembewf.ProcessMixin: Instance of the process model
        """
        jwf = get_jembewf()
        process = cls._create_process(flow_name, **process_vars)
        if process.callback.can_start():
            # save process to db
            jwf.db.session.add(process)
            jwf.db.session.commit()

            process.callback.callback()

            # create steps for starting tasks
            for task_name in process.flow.starts_with_tasks:
                task = process.flow.tasks[task_name]
                jwf.step_model.create(process, task)
        else:
            raise CantStartProcess(
                f"Can't start process '{flow_name}' with process vars: {process_vars}"
            )
        return process

    def proceed(self) -> bool:
        """Proceed with process execution

        Check if any of active steps can transit to the next tasks, if so
        do the transition.

        Returns True if process proceed to new steps
        """
        proceded = False
        for step in self.current_steps():
            if not step.is_last_step:
                proceded = proceded or step.proceed()
        return proceded

    def check_is_running(self):
        """Check if process is still running and update is_running if necessary"""
        session = object_session(self)
        step = get_jembewf().step_model
        is_running = session.query(
            session.query(step).filter(step.is_active == True).exists()
        ).scalar()
        if self.is_running != is_running:
            self.is_running = is_running
            session.add(self)
            session.commit()
        return is_running

    @classmethod
    def _create_process(cls, flow_name: str, **process_vars) -> "jembewf.ProcessMixin":
        jwf = get_jembewf()
        try:
            flow = jwf.flows[flow_name]
        except KeyError as err:
            raise ValueError(
                f"Can't start flow '{flow_name}' because it does not exist!"
            ) from err

        process = jwf.process_model()
        process.flow_name = flow.name
        process.variables = process_vars

        return process

    @classmethod
    def get_step_table_name(cls) -> str:
        """Returns name of Process table defined in cls.__step_table_name__

        It's used to create relationship between steps and steps.
        """
        try:
            return cls.__step_table_name__
        except AttributeError as err:
            raise AttributeError(
                f"Attribute __step_table_name__ for '{cls.__name__}' is not defined"
            ) from err

    @classmethod
    def get_step_class_name(cls) -> str:
        """Returns name of Process class defined in cls.__step_class_name__

        It's used to create relationship between steps and steps.
        """
        try:
            return cls.__step_class_name__
        except AttributeError as err:
            raise AttributeError(
                f"Attribute __step_class_name__ for '{cls.__name__}' is not defined"
            ) from err

    def __repr__(self):
        return f"<Process #{self.id}: '{self.flow_name}'>"
