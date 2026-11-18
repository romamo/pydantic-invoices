"""Payment note schema - predefined payment instructions."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class PaymentNoteBase(BaseModel):
    """Base payment note schema."""

    title: str = Field(
        ..., min_length=1, max_length=100, description="Payment note title"
    )
    content: str = Field(
        ..., min_length=1, max_length=2000, description="Payment instructions content"
    )

    # Association
    company_id: Optional[int] = Field(
        None, description="Company ID (None = available for all companies)"
    )

    # Settings
    is_active: bool = Field(default=True, description="Whether this note is active")
    is_default: bool = Field(
        default=False, description="Whether this is the default payment note"
    )
    display_order: int = Field(
        default=0, description="Display order (lower numbers first)"
    )


class PaymentNoteCreate(PaymentNoteBase):
    """Schema for creating a payment note."""

    pass


class PaymentNoteUpdate(BaseModel):
    """Schema for updating a payment note."""

    title: Optional[str] = Field(None, min_length=1, max_length=100)
    content: Optional[str] = Field(None, min_length=1, max_length=2000)
    company_id: Optional[int] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    display_order: Optional[int] = None


class PaymentNote(PaymentNoteBase):
    """Complete payment note schema."""

    id: int

    model_config = ConfigDict(from_attributes=True)


class PaymentNoteSnapshot(BaseModel):
    """A payment note's printed text, frozen on an invoice when it is created."""

    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1, max_length=2000)

    model_config = ConfigDict(frozen=True, from_attributes=True)
