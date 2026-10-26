"""Custom exceptions for the Fly-in project."""


class ParseError(Exception):
    """Raised when the map file is invalid."""

    def __init__(self, line_no: int, message: str) -> None:
        """Build the error message from a line number and a cause."""
        super().__init__(f"line {line_no}: {message}")
