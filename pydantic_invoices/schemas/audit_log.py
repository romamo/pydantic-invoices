"""AuditLog schemas - Pure Pydantic models."""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class AuditLog(BaseModel):
    """Audit log entry schema."""

    id: int
    invoice_id: int
    timestamp: datetime
    action: str = Field(..., max_length=50)
    old_value: Optional[str] = Field(None, max_length=1000)
    new_value: Optional[str] = Field(None, max_length=1000)
    user: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=1000)

    model_config = ConfigDict(from_attributes=True)
