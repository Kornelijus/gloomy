class PathAccessError(Exception):
    """Raised when specified path (spec) cannot be accessed and no default is provided."""


class PathAssignError(Exception):
    """Raised when specified path cannot be assigned to."""


class PathDeleteError(Exception):
    """Raised when specified path cannot be deleted from."""
