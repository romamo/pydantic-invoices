"""AuditLog schemas - Pure Pydantic models."""

from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, model_validator
from datetime import datetime
from typing import Any, Optional


class AuditEntity(str, Enum):
    """Kind of record an audit entry is about."""

    INVOICE = "invoice"
    PAYMENT_NOTE = "payment_note"
    CLIENT = "client"
    COMPANY = "company"


class AuditLog(BaseModel):
    """Audit log entry schema.

    `entity_type` + `entity_id` name the record. Invoice entries also carry
    `invoice_id` (equal to `entity_id`); entries about other records leave it None.
    Entries stored before 1.7.0 have only `invoice_id` and load as invoice entries.
    """

    id: int
    entity_type: AuditEntity = AuditEntity.INVOICE
    entity_id: int
    invoice_id: Optional[int] = None
    corrects_id: Optional[int] = Field(
        None, description="ID of the entry this one corrects; entries are never edited"
    )
    timestamp: datetime
    action: str = Field(..., max_length=50)
    old_value: Optional[str] = Field(None, max_length=1000)
    new_value: Optional[str] = Field(None, max_length=1000)
    user: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=1000)

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def legacy_invoice_entry(cls, data: Any) -> Any:
        """Read a pre-1.7.0 entry (only `invoice_id`) as an invoice entry."""
        if isinstance(data, dict) and "entity_id" not in data:
            data = {**data, "entity_id": data.get("invoice_id")}
        return data

    @model_validator(mode="after")
    def invoice_id_matches_entity(self) -> "AuditLog":
        if self.entity_type is AuditEntity.INVOICE:
            if self.invoice_id is None:
                self.invoice_id = self.entity_id
            elif self.invoice_id != self.entity_id:
                raise ValueError(
                    f"invoice_id {self.invoice_id} differs from entity_id {self.entity_id}"
                )
        elif self.invoice_id is not None:
            raise ValueError(f"A {self.entity_type.value} entry has no invoice_id")
        return self
