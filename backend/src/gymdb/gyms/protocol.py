from typing import Protocol


class GymStoreProtocol(Protocol):
    @property
    def default_region(self) -> str: ...

    def filter(
        self,
        *,
        region: str,
        min_conf: float | None = ...,
        limit: int = ...,
        offset: int = ...,
    ) -> list[dict]: ...

    def nearby(
        self,
        *,
        region: str,
        lat: float,
        lon: float,
        radius_m: float,
        min_conf: float | None = ...,
    ) -> list[dict]: ...

    def get_by_id(self, region: str, gym_id: str) -> dict | None: ...
