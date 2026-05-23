from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class UploadRead(BaseModel):
    id: uuid.UUID
    import_batch_id: uuid.UUID | None
    upload_type: str
    import_type: str
    status: str
    error_message: str | None
    rows_inserted: int
    rows_skipped: int
    can_reprocess: bool
    uploaded_at: datetime

    model_config = {"from_attributes": True}
