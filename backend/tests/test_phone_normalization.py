import pytest

from app.schemas.auth import normalize_phone


@pytest.mark.parametrize('value', ['9876543210', '+91 98765 43210', '919876543210'])
def test_indian_phone_numbers_have_one_canonical_database_format(value: str) -> None:
    assert normalize_phone(value) == '919876543210'
