class FakeResult:
    def __init__(self, scalar_value=None):
        self._scalar_value = scalar_value

    def scalar(self):
        return self._scalar_value


class FakeDB:
    def execute(self, stmt):
        sql = str(stmt)

        if "SELECT 1" in sql:
            return FakeResult(1)

        if "PostGIS_Version" in sql:
            return FakeResult("3.4.0")

        if "COUNT" in sql:
            return FakeResult(123)

        return FakeResult(None)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False
