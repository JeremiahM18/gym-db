class FakeReceiptStore:
    def save(self, receipt):
        pass

    def get(self, job_id: str):
        raise KeyError(job_id)

    def list_recent(self, limit: int = 25):
        return []
