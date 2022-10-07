from typing import TYPE_CHECKING
from sqlalchemy.orm import declarative_mixin
# import sqlalchemy as sa

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

    @property
    def process(self) -> "jembewf.Process":
        """Returns process instance that this step belongs to"""
        # TODO implement with SqlAlchemy relation to ProcessMixin
        raise NotImplementedError()

    @property
    def task(self) -> "jembewf.Task":
        """Returns Task definition of the step"""
        raise NotImplementedError()
