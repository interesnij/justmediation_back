import pytest

from libs.admin.mixins import ForbidDeleteAdd


@pytest.fixture(scope="module")
def forbid_delete_add():
    """Create forbid_delete_add for testing"""
    return ForbidDeleteAdd()


def test_has_delete_permission(forbid_delete_add):
    """``has_delete_permission`` should always return ``False``"""
    assert not forbid_delete_add.has_delete_permission(None)


def test_has_add_permission(forbid_delete_add):
    """``has_add_permission`` should always return ``False``"""
    assert not forbid_delete_add.has_add_permission(None)
