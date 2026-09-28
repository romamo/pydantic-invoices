"""Invoice schemas - Pure Pydantic models."""

from __future__ import annotations
from enum import Enum
from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    computed_field,
    model_validator,
)
from pydantic_invoices.vo import Money
from datetime import date
from typing import Optional, List, TYPE_CHECKING, Any


class InvoiceStatus(str, Enum):
    """Valid invoice status values."""

    DRAFT = "DRAFT"
    SENT = "SENT"
    UNPAID = "UNPAID"  # Legacy/Simple flow
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"
    CREDITED = "CREDITED"


class InvoiceType(str, Enum):
    """Type of invoice document."""

    STANDARD = "STANDARD"
    CREDIT_NOTE = "CREDIT_NOTE"


if TYPE_CHECKING:
    from .invoice_line import InvoiceLine, InvoiceLineCreate
    from .payment import Payment
    from .audit_log import AuditLog


class InvoiceBase(BaseModel):
    """Base invoice schema."""

    number: str = Field(
        ..., min_length=1, max_length=50, description="Unique invoice number"
    )
    issue_date: date = Field(
        default_factory=date.today, description="Invoice issue date"
    )

    status: InvoiceStatus = Field(
        default=InvoiceStatus.DRAFT,
        description="Invoice payment status",
    )
    type: InvoiceType = Field(
        default=InvoiceType.STANDARD,
        description="Type of invoice (Standard or Credit Note)",
    )
    due_date: Optional[date] = Field(None, description="Payment due date")
    payment_terms: str = Field(
        default="Net 30",
        max_length=100,
        description="Payment terms (e.g., Net 30, Net 60)",
    )

    # linking
    original_invoice_id: Optional[int] = Field(
        None, description="ID of the original invoice (for Credit Notes)"
    )
    reason: Optional[str] = Field(
        None, max_length=500, description="Reason for credit note or cancellation"
    )

    # Company (defaults to company #1)
    company_id: int = Field(
        default=1, gt=0, description="Company that issues this invoice"
    )

    # Client snapshots (immutable)
    client_name_snapshot: Optional[str] = Field(
        None, max_length=255, description="Client name at invoice time"
    )
    client_address_snapshot: Optional[str] = Field(
        None, max_length=500, description="Client address at invoice time"
    )
    client_tax_id_snapshot: Optional[str] = Field(
        None, max_length=50, description="Client tax ID at invoice time"
    )

    # Company snapshots (immutable)
    company_name_snapshot: Optional[str] = Field(
        None, max_length=255, description="Company name at invoice time"
    )
    company_address_snapshot: Optional[str] = Field(
        None, max_length=500, description="Company address at invoice time"
    )
    company_tax_id_snapshot: Optional[str] = Field(
        None, max_length=50, description="Company tax ID at invoice time"
    )

    # Payment notes (can select multiple)
    payment_note_ids: List[int] = Field(
        default_factory=list, description="IDs of payment notes to include"
    )
    template_name: Optional[str] = Field(
        None, max_length=255, description="Template filename used for this invoice"
    )

    @model_validator(mode="after")
    def validate_due_date(self) -> "InvoiceBase":
        """Ensure due date is not before issue date."""
        if self.due_date and self.due_date < self.issue_date:
            raise ValueError(
                f"Due date ({self.due_date}) cannot be earlier than "
                f"issue date ({self.issue_date})"
            )
        return self


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""

    client_id: int = Field(..., description="Client ID")
    lines: List["InvoiceLineCreate"] = Field(default_factory=list)
    status: InvoiceStatus = Field(
        default=InvoiceStatus.DRAFT,  # Default to DRAFT when creating
        description="Invoice payment status",
    )

    @model_validator(mode="before")
    @classmethod
    def handle_legacy_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Map 'date' to 'issue_date'
            if "date" in data and "issue_date" not in data:
                data["issue_date"] = data.pop("date")

            # Map 'payment_note_id' to 'payment_note_ids'
            if "payment_note_id" in data and "payment_note_ids" not in data:
                val = data.pop("payment_note_id")
                if val:
                    data["payment_note_ids"] = [val]
        return data


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice."""

    status: Optional[InvoiceStatus] = None
    due_date: Optional[date] = None
    payment_terms: Optional[str] = Field(None, max_length=100)
    reason: Optional[str] = Field(None, max_length=500)
    template_name: Optional[str] = Field(None, max_length=255)


class InvoiceSummary(BaseModel):
    """Schema for invoice statistics summary."""

    total_count: int
    paid_count: int
    unpaid_count: int
    overdue_count: int
    total_amount: Money
    total_paid: Money
    total_due: Money


class Invoice(InvoiceBase):
    """Complete invoice schema with computed properties."""

    id: int
    company_id: int = Field(default=1)  # Keep default for DX
    client_id: int
    template_name: Optional[str] = Field(default="default.html")
    type: InvoiceType = Field(default=InvoiceType.STANDARD)
    original_invoice_id: Optional[int] = None
    reason: Optional[str] = None

    # Snapshots (immutable after creation)
    client_name_snapshot: Optional[str] = None
    client_address_snapshot: Optional[str] = None
    client_tax_id_snapshot: Optional[str] = None
    company_name_snapshot: Optional[str] = None
    company_address_snapshot: Optional[str] = None
    company_tax_id_snapshot: Optional[str] = None
    lines: List["InvoiceLine"] = Field(default_factory=list)
    payments: List["Payment"] = Field(default_factory=list)
    audit_logs: List["AuditLog"] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_amount(self) -> Money:
        """Calculate total amount from all line items."""
        # Get currency from the first line or default to USD
        # In a real app, currency should be consistent across lines
        currency = (
            self.lines[0].unit_price.currency
            if self.lines and isinstance(self.lines[0].unit_price, Money)
            else "USD"
        )
        return sum((line.total for line in self.lines), start=Money(0, currency))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_paid(self) -> Money:
        """Calculate total amount paid across all payments."""
        currency = (
            self.lines[0].unit_price.currency
            if self.lines and isinstance(self.lines[0].unit_price, Money)
            else "USD"
        )
        return sum(
            (payment.amount for payment in self.payments), start=Money(0, currency)
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def balance_due(self) -> Money:
        """Calculate remaining balance to be paid."""
        return self.total_amount - self.total_paid

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_overdue(self) -> bool:
        """Check if invoice is past due date."""
        if self.status in (
            InvoiceStatus.PAID,
            InvoiceStatus.CANCELLED,
            InvoiceStatus.REFUNDED,
            InvoiceStatus.CREDITED,
        ):
            return False
        if self.due_date:
            return date.today() > self.due_date
        return False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def days_overdue(self) -> int:
        """Calculate number of days past due."""
        if not self.is_overdue or self.due_date is None:
            return 0
        return (date.today() - self.due_date).days

    model_config = ConfigDict(from_attributes=True)


# Resolve forward references after all classes are defined
from .invoice_line import InvoiceLine, InvoiceLineCreate  # noqa: E402
from .payment import Payment  # noqa: E402
from .audit_log import AuditLog  # noqa: E402

Invoice.model_rebuild()
InvoiceCreate.model_rebuild()
