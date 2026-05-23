from __future__ import annotations

from pydantic import BaseModel


class DemoLoadResponse(BaseModel):
    store_id: str
    import_batch_id: str
    rows_inserted: int
    message: str
