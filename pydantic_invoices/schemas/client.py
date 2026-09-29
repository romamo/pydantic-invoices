"""Client schema - invoice recipient."""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Union
from pydantic_invoices.vo import CountryCode, TaxId


def _coerce_postal_code(v: Union[str, int, None]) -> Optional[str]:
    """Coerce integer postal codes (from YAML) to strings."""
    if isinstance(v, int):
        return str(v)
    return v


class ClientBase(BaseModel):
    """Base client schema."""

    name: str = Field(..., min_length=1, max_length=255, description="Client name")
    address: Optional[str] = Field(None, max_length=500, description="Client address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    postal_code: Optional[str] = Field(
        None, max_length=20, description="Postal/ZIP code"
    )
    country: Optional[CountryCode.Input] = Field(
        None, description="ISO 3166-1 alpha-2 country code"
    )
    tax_id: Optional[TaxId.Input] = Field(None, description="Client tax ID number")
    email: Optional[str] = Field(
        None, max_length=255, description="Client email address"
    )
    phone: Optional[str] = Field(None, max_length=50, description="Client phone number")
    preferred_template: Optional[str] = Field(
        None, max_length=255, description="Preferred invoice template filename"
    )

    _postal_code = field_validator("postal_code", mode="before")(_coerce_postal_code)


class ClientCreate(ClientBase):
    """Schema for creating a client."""

    pass


class ClientUpdate(BaseModel):
    """Schema for updating a client."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[CountryCode.Input] = None
    tax_id: Optional[TaxId.Input] = None
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)

    _postal_code = field_validator("postal_code", mode="before")(_coerce_postal_code)


class Client(ClientBase):
    """Complete client schema."""

    id: int

    model_config = ConfigDict(from_attributes=True)
