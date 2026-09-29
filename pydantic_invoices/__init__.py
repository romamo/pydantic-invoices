"""Pydantic schemas and interfaces for invoice management.

This package provides type-safe Pydantic schemas and repository interfaces
for building invoice management systems.

Example:
    from pydantic_invoices import Invoice, InvoiceCreate, Client
    from pydantic_invoices.interfaces import InvoiceRepository

    # Use schemas
    invoice = InvoiceCreate(...)

    # Implement interfaces
    class MyRepo(InvoiceRepository):
        ...
"""

# Export common schemas
from .schemas import (
    Invoice,
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceLine,
    InvoiceLineCreate,
    Client,
    ClientCreate,
    ClientUpdate,
    Payment,
    PaymentCreate,
)

# Export all interfaces
from .interfaces import (
    BaseRepository,
    InvoiceRepository,
    ClientRepository,
    PaymentRepository,
    CompanyRepository,
    ProductRepository,
    PaymentNoteRepository,
)

__version__ = "1.5.0"

__all__ = [
    # Schemas
    "Invoice",
    "InvoiceCreate",
    "InvoiceUpdate",
    "InvoiceLine",
    "InvoiceLineCreate",
    "Client",
    "ClientCreate",
    "ClientUpdate",
    "Payment",
    "PaymentCreate",
    # Interfaces
    "BaseRepository",
    "InvoiceRepository",
    "ClientRepository",
    "PaymentRepository",
    "CompanyRepository",
    "ProductRepository",
    "PaymentNoteRepository",
]

# Advanced schemas - import explicitly:
# from pydantic_invoices.schemas.company import Company, CompanyCreate
# from pydantic_invoices.schemas.product import Product, ProductCreate
# from pydantic_invoices.schemas.payment_note import PaymentNote, PaymentNoteCreate
# from pydantic_invoices.schemas.audit_log import AuditLog
