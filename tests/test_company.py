"""Tests for Company schema."""

import pytest
from pydantic import ValidationError
from pydantic_invoices.schemas.company import CompanyCreate, CompanyUpdate


def test_number_prefix_defaults_to_none():
    assert CompanyCreate(name="Acme").number_prefix is None


def test_number_prefix_accepts_alphanumerics():
    assert CompanyCreate(name="Acme", number_prefix="AC2").number_prefix == "AC2"
    assert CompanyUpdate(number_prefix="AC").number_prefix == "AC"


@pytest.mark.parametrize("prefix", ["", "A-C", "A/C", "A C", "../x", "A" * 21])
def test_number_prefix_rejects_unsafe_values(prefix):
    with pytest.raises(ValidationError):
        CompanyCreate(name="Acme", number_prefix=prefix)
    with pytest.raises(ValidationError):
        CompanyUpdate(number_prefix=prefix)
