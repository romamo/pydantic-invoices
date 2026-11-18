"""Tests for AuditLog entities."""

from datetime import datetime

import pytest
from pydantic import ValidationError
from pydantic_invoices.schemas.audit_log import AuditEntity, AuditLog

NOW = datetime(2026, 11, 18, 12, 0)


def test_legacy_entry_reads_as_invoice_entry():
    entry = AuditLog.model_validate(
        {"id": 1, "invoice_id": 7, "timestamp": NOW, "action": "CREATE"}
    )
    assert entry.entity_type is AuditEntity.INVOICE
    assert entry.entity_id == 7


def test_invoice_entry_fills_invoice_id():
    entry = AuditLog(id=1, entity_id=7, timestamp=NOW, action="ISSUE")
    assert entry.invoice_id == 7


def test_payment_note_entry_has_no_invoice_id():
    entry = AuditLog(
        id=2,
        entity_type=AuditEntity.PAYMENT_NOTE,
        entity_id=3,
        timestamp=NOW,
        action="DEACTIVATE",
    )
    assert entry.invoice_id is None
    with pytest.raises(ValidationError):
        AuditLog(
            id=3,
            entity_type="payment_note",
            entity_id=3,
            invoice_id=3,
            timestamp=NOW,
            action="DEACTIVATE",
        )


def test_mismatched_invoice_id_rejected():
    with pytest.raises(ValidationError):
        AuditLog(id=1, entity_id=7, invoice_id=8, timestamp=NOW, action="CREATE")


def test_correction_references_the_corrected_entry():
    entry = AuditLog(id=4, entity_id=7, corrects_id=1, timestamp=NOW, action="CORRECT")
    assert entry.corrects_id == 1
