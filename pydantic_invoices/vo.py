"""Value Objects for the Accounting domain."""

from __future__ import annotations
import functools
import re
from decimal import Decimal, InvalidOperation
from typing import Any, TYPE_CHECKING, Union, Callable, ClassVar, TypeVar
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

_VO = TypeVar("_VO", bound="_PydanticVO")

_GENERIC_TAX_ID_RE = re.compile(r"[A-Z0-9\- \.]{5,30}")


class _PydanticVO:
    """Pydantic integration: coerce input via the constructor, serialize via `_serialize`."""

    # Non-ValueError exceptions the constructor may raise that must surface as ValueError
    _coerce_errors: ClassVar[tuple[type[Exception], ...]] = ()

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(
            cls._validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls._serialize,
                when_used="always",
            ),
        )

    @classmethod
    def _validate(cls: type[_VO], value: Any) -> _VO:
        if isinstance(value, cls):
            return value
        try:
            return cls(value)  # type: ignore[call-arg]
        except cls._coerce_errors as e:
            raise ValueError(str(e)) from e

    @classmethod
    def _serialize(cls, instance: Any) -> str:
        return str(instance)


class Money(_PydanticVO):
    """Money Value Object avoiding primitive obsession with floats.

    Internally uses decimal.Decimal to avoid rounding errors.
    """

    def __init__(
        self, amount: Decimal | str | float | int, currency: str = "USD"
    ) -> None:
        if isinstance(amount, (str, float, int)):
            self._amount = self._parse_amount(amount)
        else:
            self._amount = amount
        self._currency = currency.upper()

    @property
    def amount(self) -> Decimal:
        return self._amount

    @property
    def currency(self) -> str:
        return self._currency

    def _parse_amount(self, value: str | int | float) -> Decimal:
        """Parse various input formats including regional settings."""
        if isinstance(value, (int, float)):
            return Decimal(str(value))

        if not isinstance(value, str):
            raise ValueError(f"Cannot parse {type(value)} as Money")

        # Clean string from whitespace
        clean_val = value.strip()

        # Rule-based regional parsing:
        # If both '.' and ',' exist, we assume the last one is the decimal separator.
        # Example: 1.234,56 -> 1234.56
        # Example: 1,234.56 -> 1234.56
        if "," in clean_val and "." in clean_val:
            comma_idx = clean_val.rfind(",")
            point_idx = clean_val.rfind(".")
            if comma_idx > point_idx:
                # Comma is decimal separator: 1.234,56
                clean_val = clean_val.replace(".", "").replace(",", ".")
            else:
                # Point is decimal separator: 1,234.56
                clean_val = clean_val.replace(",", "")
        elif "," in clean_val:
            # Only comma exists. Is it a decimal or thousand separator?
            # If there's only one comma and it's followed by exactly 2 or 3 digits
            # it's ambiguous. We'll treat it as a decimal separator for now
            # as is common in many regions.
            clean_val = clean_val.replace(",", ".")

        try:
            return Decimal(clean_val)
        except InvalidOperation:
            raise ValueError(f"Invalid format for Money: {value}")

    def __repr__(self) -> str:
        return f"Money(amount={self.amount}, currency='{self.currency}')"

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"

    def __float__(self) -> float:
        return float(self.amount)

    def __bool__(self) -> bool:
        return bool(self.amount)

    # Comparison
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Money):
            return self.amount == other.amount and self.currency == other.currency
        if isinstance(other, (Decimal, float, int)):
            return self.amount == Decimal(str(other))
        return False

    def __lt__(self, other: "Money" | Decimal | float | int) -> bool:
        if not isinstance(other, Money):
            other = Money(other, self.currency)
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot compare different currencies: {self.currency} and {other.currency}"
            )
        return self.amount < other.amount

    def __le__(self, other: "Money" | Decimal | float | int) -> bool:
        if not isinstance(other, Money):
            other = Money(other, self.currency)
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot compare different currencies: {self.currency} and {other.currency}"
            )
        return self.amount <= other.amount

    def __gt__(self, other: "Money" | Decimal | float | int) -> bool:
        if not isinstance(other, Money):
            other = Money(other, self.currency)
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot compare different currencies: {self.currency} and {other.currency}"
            )
        return self.amount > other.amount

    def __ge__(self, other: "Money" | Decimal | float | int) -> bool:
        if not isinstance(other, Money):
            other = Money(other, self.currency)
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot compare different currencies: {self.currency} and {other.currency}"
            )
        return self.amount >= other.amount

    def __format__(self, format_spec: str) -> str:
        return self.amount.__format__(format_spec)

    # Arithmetic
    def __add__(self, other: Money | Decimal | float | int) -> Money:
        if not isinstance(other, Money):
            other = Money(other, self.currency)
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot add different currencies: {self.currency} and {other.currency}"
            )
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money | Decimal | float | int) -> Money:
        if not isinstance(other, Money):
            other = Money(other, self.currency)
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot subtract different currencies: {self.currency} and {other.currency}"
            )
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: int | Decimal | float) -> Money:
        return Money(self.amount * Decimal(str(factor)), self.currency)

    def __rmul__(self, factor: int | Decimal | float) -> Money:
        return self.__mul__(factor)

    # Pydantic Integration
    _coerce_errors = (InvalidOperation,)

    @classmethod
    def _serialize(cls, instance: Any) -> str:
        return str(instance.amount)

    if TYPE_CHECKING:
        Input = Union["Money", str, Decimal, float, int]


@functools.cache
def _stdnum() -> tuple[type[Exception], tuple[Callable[[str], str], ...]]:
    """Import python-stdnum on first use; it adds ~7 ms to package import."""
    from stdnum.exceptions import ValidationError
    import stdnum.eu.vat
    import stdnum.gb.vat
    import stdnum.us.ein
    import stdnum.au.abn

    return ValidationError, (
        stdnum.eu.vat.validate,
        stdnum.gb.vat.validate,
        stdnum.us.ein.validate,
        stdnum.au.abn.validate,
    )


def _normalize_tax_id(value: str) -> str:
    """Try each known validator in order; fall back to a generic regex."""
    validation_error, validators = _stdnum()
    for validate in validators:
        try:
            return validate(value)
        except validation_error:
            continue

    # Fallback: strict alphanumeric structural check for unknown formats
    if not _GENERIC_TAX_ID_RE.fullmatch(value):
        raise ValueError(f"Invalid Tax ID format: {value}")

    return value


class TaxId(_PydanticVO):
    """Tax Identification Number (e.g., EIN, VAT, TIC, ABN).

    Provides universal validation via python-stdnum and fails fast
    if the format is invalid. Avoids primitive obsession.
    """

    def __init__(self, value: str) -> None:
        if not isinstance(value, str):
            raise ValueError(f"Cannot parse {type(value)} as TaxId")

        clean_val = value.strip().upper()
        if not clean_val:
            raise ValueError("TaxId cannot be empty")

        self._value = _normalize_tax_id(clean_val)

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"TaxId('{self._value}')"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, TaxId):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return False

    if TYPE_CHECKING:
        Input = Union["TaxId", str]


# ISO 3166-1 alpha-2, plus the EN 16931 additions XI (Northern Ireland) and 1A (Kosovo)
_COUNTRY_CODES = frozenset(
    """
    AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI
    BJ BL BM BN BO BQ BR BS BT BV BW BY BZ CA CC CD CF CG CH CI CK CL CM CN
    CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK
    FM FO FR GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HM
    HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE JM JO JP KE KG KH KI KM KN
    KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK
    ML MM MN MO MP MQ MR MS MT MU MV MW MX MY MZ NA NC NE NF NG NI NL NO NP
    NR NU NZ OM PA PE PF PG PH PK PL PM PN PR PS PT PW PY QA RE RO RS RU RW
    SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ TC TD TF
    TG TH TJ TK TL TM TN TO TR TT TV TW TZ UA UG UM US UY UZ VA VC VE VG VI
    VN VU WF WS YE YT ZA ZM ZW XI 1A
    """.split()
)


class CountryCode(_PydanticVO):
    """ISO 3166-1 alpha-2 country code, as used for postal addresses in e-invoices."""

    def __init__(self, value: str) -> None:
        if not isinstance(value, str):
            raise ValueError(f"Cannot parse {type(value)} as CountryCode")

        code = value.strip().upper()
        if code not in _COUNTRY_CODES:
            raise ValueError(f"'{value}' is not an ISO 3166-1 alpha-2 country code")
        self._value = code

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"CountryCode('{self._value}')"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, CountryCode):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return False

    def __hash__(self) -> int:
        return hash(self._value)

    if TYPE_CHECKING:
        Input = Union["CountryCode", str]


if not TYPE_CHECKING:
    Money.Input = Union[Money, str, Decimal, float, int]
    # The validator already coerces str; a runtime Union would let invalid str bypass it
    TaxId.Input = TaxId
    CountryCode.Input = CountryCode
