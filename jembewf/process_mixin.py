from typing import TYPE_CHECKING
from sqlalchemy.orm import declarative_mixin

# import sqlalchemy as sa

if TYPE_CHECKING:
    import jembewf

__all__ = ("ProcessMixin",)


@declarative_mixin
class ProcessMixin:
    """Mixin to be applied to Process SqlAlchemy model

    Process model keep track of all instances of flows (current and completed)
    it global variables and states.

    ProcessMixin should be applied class extended from
    flask_sqlalchemy.SqlAlchemy().Model who defines model in database
    """

    @property
    def flow(self) -> "jembewf.Flow":
        """Flow of the process instance"""
        raise NotImplementedError()
