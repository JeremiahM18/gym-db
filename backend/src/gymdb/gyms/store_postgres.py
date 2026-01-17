from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection




class PostgresGymStore:
    """
    Read-only Postgres-backed gym store.

    
    Guarantees:
    - Deterministic ordering
    - Explicit column projection
    - No domain logic
    - Connection injected
    """

    # NOTE: keep in sync with v2 response contract
    _FIELDS = """
        id,
        name,
        norm_name,
        region,
        lat,
        lon,
        osm_refs,
        inference,
        inference_meta
    """

    def __init__(self, conn: Connection):
        self._conn = conn

    @property
    def default_region(self) -> str:
        return "us"

    def filter(
            self,
            *,
            region: str,
            min_conf: float | None = None,
            limit: int = 100,
            offset: int = 0,
    ) -> list[dict]:
        """
        Filter gyms by region with optional confidence threshold.
        """
        sql = f"""
        SELECT {self._FIELDS}
        FROM gyms
        WHERE region = :region
        """

        params: dict[str, object] = {
            "region": region,
            "limit": int(limit),
            "offset": int(offset),
        }

        if min_conf is not None:
            sql += "\n AND confidence_score >= :min_conf"
            params["min_conf"] = float(min_conf)

        sql += """
        ORDER BY id
        LIMIT :limit OFFSET :offset
        """

        rows = self._conn.execute(
            text(sql), params).mappings().all()
        
        return [dict(r) for r in rows]
    
    def get_by_id(self, region: str, gym_id: str) -> dict | None:
        sql = f"""
        SELECT {self._FIELDS}
        FROM gyms
        WHERE region = :region 
          AND id = :gym_id
        """

        row = self._conn.execute(
                text(sql),
                {
                    "region": region, 
                    "gym_id": gym_id,
                },
        ).mappings().one_or_none()

        return dict(row) if row else None