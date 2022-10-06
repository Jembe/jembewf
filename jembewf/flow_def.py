__all__ = ("FlowDef",)


class FlowDef:
    """Process Flow Definition Base class"""
    def __init__(self, name:str) -> None:
        self.name = name
