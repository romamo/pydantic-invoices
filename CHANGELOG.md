# Changelog

## 1.5.0

- Added `CountryCode` Value Object: an ISO 3166-1 alpha-2 code (plus the EN 16931 codes `XI` and `1A`), normalized to upper case; unknown codes raise
- Added `city`, `postal_code` and `country` (`CountryCode`) to `ClientBase` and `ClientUpdate`; integer postal codes are coerced to strings as for companies
- Added buyer address snapshots to invoices: `client_city_snapshot`, `client_postal_code_snapshot`, `client_country_snapshot`. EN 16931 e-invoices (Factur-X, UBL) require the buyer's country code
- `TaxId` fields now reject invalid values: `TaxId.Input` resolves to `TaxId` at runtime, so strings like `"123"` no longer bypass validation through the `str` member of the union. Stored clients or companies with such tax IDs fail to load until corrected
- `TaxId` loads `python-stdnum` on first validation instead of at import

## 1.4.1

- Added `TaxId` Value Object with multi-format validation via `python-stdnum` (EU VAT, UK VAT, US EIN, AU ABN) and a generic alphanumeric fallback.
- Applied `TaxId` to `tax_id` fields in `CompanyBase`, `CompanyUpdate`, `ClientBase`, and `ClientUpdate` schemas.
- Simplified `InvoiceBase.issue_date` to use `date` instead of `datetime`, removing the now-redundant `parse_issue_date` validator.

## 1.3.1

- Relaxed `postal_code` validation in `Company` schema to support integer inputs (e.g. from YAML).
- Updated release workflows.


## 1.3.0

- Added `py.typed` marker.
- Updated repository interfaces (`ClientRepository` searches).
- Added system diagram documentation.

## 1.2.2

- Added smoke test.
- Added GitHub Actions CI workflow.

## 1.2.1

- Added release workflow (`release_new_version`).
- Added GitHub Actions workflow for publishing.
- Fixed repository URLs in `pyproject.toml`.
- Refactored tests structure.

## 1.2.0

- Initial release with tag.
