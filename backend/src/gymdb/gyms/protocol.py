from typing import Protocol


class GymStoreProtocol(Protocol):
    default_region: str

    def filter(
        self,
        *,
        region: str,
        min_conf: float | None = ...,
        limit: int = ...,
        offset: int = ...,
    ) -> list[dict]: ...

    def get_by_id(self, region: str, gym_id: str) -> dict | None: ...
