"""Tests for Client schema."""

import pytest
from pydantic import ValidationError
from pydantic_invoices.schemas.client import Client, ClientCreate, ClientUpdate


class TestClientCreate:
    """Tests for ClientCreate schema."""

    def test_valid_client_create(self):
        """Test creating a valid client."""
        client = ClientCreate(
            name="Acme Corp",
            address="123 Main St",
            tax_id="12-3456789",
        )
        assert client.name == "Acme Corp"
        assert client.address == "123 Main St"
        assert client.tax_id == "123456789"

    def test_minimal_client(self):
        """Test creating client with minimal required fields."""
        client = ClientCreate(name="Minimal Client")
        assert client.name == "Minimal Client"
        assert client.address is None
        assert client.tax_id is None


class TestClient:
    """Tests for Client schema."""

    def test_full_client(self):
        """Test client with all fields."""
        client = Client(
            id=1,
            name="Full Client",
            address="456 Oak Ave",
            tax_id="98-7654321",
            email="client@example.com",
            phone="+1234567890",
        )
        assert client.id == 1
        assert client.name == "Full Client"
        assert client.email == "client@example.com"


class TestClientUpdate:
    """Tests for ClientUpdate schema."""

    def test_partial_update(self):
        """Test partial client update."""
        update = ClientUpdate(email="newemail@example.com")
        assert update.email == "newemail@example.com"
        assert update.name is None

    def test_update_multiple_fields(self):
        """Test updating multiple fields."""
        update = ClientUpdate(
            name="Updated Name",
            address="New Address",
        )
        assert update.name == "Updated Name"
        assert update.address == "New Address"


def test_invalid_tax_id_rejected():
    """Invalid tax IDs must not fall through to a plain str."""
    with pytest.raises(ValidationError):
        ClientCreate(name="Acme Corp", tax_id="a!")
