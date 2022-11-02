from typing import TYPE_CHECKING, Optional, Union
from dataclasses import dataclass
from flask import current_app

if TYPE_CHECKING:
    import jembewf

__all__ = (
    "CanProceed",
    "get_jembewf",
)


@dataclass
class CanProceed:
    """Returnable from can_proceed method transition callback containg reason why transition can't proceed

    Can be used as regular bool since it behaves as truly or falsly
    """

    result: bool
    reason: Optional[str] = None

    def __post_init__(self):
        """Reason should be none when transition can proceed"""
        if self.result is True:
            self.reason = None

    def __bool__(self) -> bool:
        """Can be used as regular bool in expressions"""
        return self.result

    def append_reason(self, can_proceed: Union[bool, "jembewf.CanProceed"]):
        """Append reasion why it can not proceed

        raises:
            ValueError: if self.result is not False or can_proceed is True"""
        if self.result or can_proceed:
            raise ValueError(
                "Reasons can be append only if both transition can not proceed."
            )
        if self.reason is None:
            self.reason = ""
        if isinstance(can_proceed, CanProceed) and isinstance(can_proceed.reason, str):
            self.reason += can_proceed.reason

    def add_reason(self, reason: str, result: bool = False):
        """Adds reason to result"""
        if self.reason is not None:
            self.reason += "\n" + reason
        else:
            self.reason = reason
        self.result = self.result and result


def get_jembewf() -> "jembewf.JembeWF":
    """Returns instance of JembeWf for current Flask application"""
    jembewf_instance = current_app.extensions.get("jembewf", None)
    if jembewf_instance is None:
        raise Exception("JembeWF extension is not initialised")
    return jembewf_instance
