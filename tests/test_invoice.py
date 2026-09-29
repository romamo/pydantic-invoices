"""Tests for Invoice schema."""

from datetime import date, timedelta

import pytest
from pydantic import ValidationError
from pydantic_invoices.schemas.invoice import (
    Invoice,
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceStatus,
)
from pydantic_invoices.schemas.invoice_line import InvoiceLine, InvoiceLineCreate


class TestInvoiceCreate:
    """Tests for InvoiceCreate schema."""

    def test_valid_invoice_create(self):
        """Test creating a valid invoice."""
        invoice = InvoiceCreate(
            number="INV-001",
            client_id=1,
            company_id=1,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            status=InvoiceStatus.UNPAID,
            payment_terms="Net 30",
            lines=[],
        )
        assert invoice.number == "INV-001"
        assert invoice.client_id == 1
        assert invoice.status == "UNPAID"

    def test_company_id_defaults_to_one(self):
        """Test that company_id defaults to 1."""
        invoice = InvoiceCreate(
            number="INV-001",
            client_id=1,
            issue_date=date.today(),
            due_date=date.today(),
            status=InvoiceStatus.UNPAID,
            payment_terms="Net 30",
            lines=[],
        )
        assert invoice.company_id == 1

    def test_with_invoice_lines(self):
        """Test invoice with line items."""
        lines = [
            InvoiceLineCreate(
                description="Service 1",
                quantity=2,
                unit_price=100.0,
            ),
            InvoiceLineCreate(
                description="Service 2",
                quantity=1,
                unit_price=200.0,
            ),
        ]
        invoice = InvoiceCreate(
            number="INV-001",
            client_id=1,
            issue_date=date.today(),
            due_date=date.today(),
            status=InvoiceStatus.UNPAID,
            payment_terms="Net 30",
            lines=lines,
        )
        assert len(invoice.lines) == 2
        assert invoice.lines[0].description == "Service 1"


class TestInvoice:
    """Tests for Invoice schema."""

    def test_total_amount_calculation(self):
        """Test that total_amount is calculated correctly."""
        invoice = Invoice(
            id=1,
            number="INV-001",
            client_id=1,
            company_id=1,
            issue_date=date.today(),
            due_date=date.today(),
            status=InvoiceStatus.UNPAID,
            payment_terms="Net 30",
            lines=[
                InvoiceLine(
                    id=1,
                    invoice_id=1,
                    description="Service 1",
                    quantity=2,
                    unit_price=100.0,
                ),
                InvoiceLine(
                    id=2,
                    invoice_id=1,
                    description="Service 2",
                    quantity=1,
                    unit_price=200.0,
                ),
            ],
            payments=[],
        )
        assert invoice.total_amount.amount == 400.0

    def test_balance_due_with_no_payments(self):
        """Test balance_due when no payments made."""
        invoice = Invoice(
            id=1,
            number="INV-001",
            client_id=1,
            company_id=1,
            issue_date=date.today(),
            due_date=date.today(),
            status=InvoiceStatus.UNPAID,
            payment_terms="Net 30",
            lines=[
                InvoiceLine(
                    id=1,
                    invoice_id=1,
                    description="Service",
                    quantity=1,
                    unit_price=100.0,
                ),
            ],
            payments=[],
        )
        assert invoice.balance_due.amount == 100.0

    def test_is_overdue(self):
        """Test is_overdue property."""
        # Not overdue
        invoice = Invoice(
            id=1,
            number="INV-001",
            client_id=1,
            company_id=1,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=1),
            status=InvoiceStatus.UNPAID,
            payment_terms="Net 30",
            lines=[],
            payments=[],
        )
        assert invoice.is_overdue is False

        # Overdue
        invoice_overdue = Invoice(
            id=2,
            number="INV-002",
            client_id=1,
            company_id=1,
            issue_date=date.today() - timedelta(days=60),
            due_date=date.today() - timedelta(days=30),
            status=InvoiceStatus.UNPAID,
            payment_terms="Net 30",
            lines=[],
            payments=[],
        )
        assert invoice_overdue.is_overdue is True

    def test_paid_invoice_not_overdue(self):
        """Test that paid invoices are never overdue."""
        invoice = Invoice(
            id=1,
            number="INV-001",
            client_id=1,
            company_id=1,
            issue_date=date.today() - timedelta(days=60),
            due_date=date.today() - timedelta(days=30),
            status=InvoiceStatus.PAID,
            payment_terms="Net 30",
            lines=[],
            payments=[],
        )
        assert invoice.is_overdue is False

    def test_invoice_without_due_date(self):
        """Test invoice behavior when due_date is None."""
        invoice = Invoice(
            id=1,
            number="INV-001",
            client_id=1,
            company_id=1,
            issue_date=date.today(),
            due_date=None,  # No due date
            status=InvoiceStatus.UNPAID,
            payment_terms="Net 30",
            lines=[],
            payments=[],
        )
        assert invoice.is_overdue is False
        assert invoice.days_overdue == 0


class TestInvoiceUpdate:
    """Tests for InvoiceUpdate schema."""

    def test_partial_update(self):
        """Test that InvoiceUpdate allows partial updates."""
        update = InvoiceUpdate(status=InvoiceStatus.PAID)
        assert update.status == InvoiceStatus.PAID
        assert update.due_date is None
        assert update.payment_terms is None

    def test_update_multiple_fields(self):
        """Test updating multiple fields."""
        update = InvoiceUpdate(
            status=InvoiceStatus.PAID,
            payment_terms="Net 15",
        )
        assert update.status == InvoiceStatus.PAID
        assert update.payment_terms == "Net 15"


class TestClientAddressSnapshots:
    """Buyer address snapshots on invoices."""

    def test_snapshots_on_create_and_invoice(self):
        data = dict(
            number="INV-ADDR-1",
            client_id=1,
            client_city_snapshot="Paris",
            client_postal_code_snapshot="75001",
            client_country_snapshot="fr",
        )
        created = InvoiceCreate(**data)
        invoice = Invoice(id=1, **data)
        assert created.client_country_snapshot == "FR"
        assert invoice.client_city_snapshot == "Paris"
        assert invoice.model_dump()["client_country_snapshot"] == "FR"

    def test_invalid_country_snapshot_rejected(self):
        with pytest.raises(ValidationError):
            InvoiceCreate(
                number="INV-ADDR-2", client_id=1, client_country_snapshot="ZZ"
            )
