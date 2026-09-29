import pytest
from decimal import Decimal
from pydantic import BaseModel, ValidationError
from pydantic_invoices.vo import CountryCode, Money, TaxId


def test_money_basic_parsing():
    assert Money("100.50").amount == Decimal("100.50")
    assert Money(100.50).amount == Decimal("100.5")
    assert Money(100).amount == Decimal("100")


def test_money_regional_parsing():
    # US/UK style
    assert Money("1,234.56").amount == Decimal("1234.56")
    # German/EU style
    assert Money("1.234,56").amount == Decimal("1234.56")
    # Simple comma
    assert Money("1234,56").amount == Decimal("1234.56")
    # No thousand separator
    assert Money("1234.56").amount == Decimal("1234.56")


def test_money_arithmetic():
    m1 = Money("10.50")
    m2 = Money("5.25")

    assert (m1 + m2).amount == Decimal("15.75")
    assert (m1 - m2).amount == Decimal("5.25")
    assert (m1 * 2).amount == Decimal("21.00")


def test_money_different_currencies():
    m1 = Money("10.50", "USD")
    m2 = Money("5.25", "EUR")

    with pytest.raises(ValueError, match="Cannot add different currencies"):
        m1 + m2


def test_money_invalid_parsing():
    with pytest.raises(ValueError, match="Invalid format for Money"):
        Money("invalid")


def test_money_pydantic_validation():
    from pydantic import BaseModel

    class Model(BaseModel):
        price: Money

    m = Model(price="1.234,56")
    assert isinstance(m.price, Money)
    assert m.price.amount == Decimal("1234.56")

    # Check serialization
    assert m.model_dump()["price"] == "1234.56"


def test_taxid_eu_vat_parsing():
    # Valid EU VAT (Cyprus)
    t = TaxId("CY10259033P")
    assert t.value == "CY10259033P"

    # With spaces/lowercase
    t2 = TaxId(" cy 10259 033p ")
    assert t2.value == "CY10259033P"


def test_taxid_us_ein_parsing():
    # Valid US EIN
    t = TaxId("12-3456789")
    # Normalized format inside python-stdnum drops the hyphen
    assert t.value == "123456789"


def test_taxid_fallback_parsing():
    # A generic alphanumeric id that is not specifically validated
    # should fallback and be accepted
    t = TaxId("GENERIC-123")
    assert t.value == "GENERIC-123"


def test_taxid_invalid_parsing():
    # symbols or empty or too short should fail fast
    with pytest.raises(ValueError):
        TaxId("")

    with pytest.raises(ValueError, match="Invalid Tax ID format"):
        TaxId("a!")

    with pytest.raises(ValueError, match="Invalid Tax ID format"):
        TaxId("123")  # too short


def test_taxid_pydantic_validation():
    class CompanyModel(BaseModel):
        tax_id: TaxId

    # Should coerce string seamlessly
    m = CompanyModel(tax_id="CY10259033P")
    assert isinstance(m.tax_id, TaxId)
    assert m.tax_id.value == "CY10259033P"

    # Should serialize seamlessly back to string
    assert m.model_dump()["tax_id"] == "CY10259033P"


def test_country_code_normalizes_case_and_whitespace():
    assert CountryCode(" de ").value == "DE"
    assert CountryCode("XI").value == "XI"
    assert CountryCode("1a").value == "1A"


def test_country_code_rejects_unknown_codes():
    for value in ["", "D", "DEU", "XX", "Germany"]:
        with pytest.raises(ValueError, match="not an ISO 3166-1 alpha-2"):
            CountryCode(value)


def test_country_code_pydantic_validation():
    class Address(BaseModel):
        country: CountryCode.Input

    address = Address(country="fr")
    assert isinstance(address.country, CountryCode)
    assert address.model_dump()["country"] == "FR"
    with pytest.raises(ValidationError):
        Address(country="Neverland")
