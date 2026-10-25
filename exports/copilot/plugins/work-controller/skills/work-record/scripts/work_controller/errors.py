"""Domain errors with stable, user-facing messages."""


class ProcessError(Exception):
    """Base error for an expected operational failure."""


class DefinitionError(ProcessError):
    """The process definition is invalid or unsupported."""


class StateError(ProcessError):
    """The requested transition violates the run contract."""


class AuthorizationError(ProcessError):
    """The operation lacks an explicit grant."""


class ExecutionError(ProcessError):
    """A job or one of its gates failed."""


class OutcomeUnknownError(ExecutionError):
    """An external effect may have happened and must not be retried blindly."""
