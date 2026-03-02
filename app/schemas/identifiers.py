from typing import Annotated, Any

from pydantic import BeforeValidator, StringConstraints


def _normalize_identifier(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    return value


def _normalize_platform(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip().lower()
    return value


Identifier = Annotated[
    str,
    BeforeValidator(_normalize_identifier),
    StringConstraints(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._-]+$"),
]

PlatformIdentifier = Annotated[
    str,
    BeforeValidator(_normalize_platform),
    StringConstraints(min_length=1, max_length=32, pattern=r"^[A-Za-z0-9._-]+$"),
]
