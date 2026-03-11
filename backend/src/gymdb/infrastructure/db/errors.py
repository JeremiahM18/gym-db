class DatabaseError(RuntimeError):
    """Base DB error."""


class DatabaseUnavailable(DatabaseError):
    """DB id down / cannot connect."""


class QueryFailed(DatabaseError):
    """SQL ran but failed."""
