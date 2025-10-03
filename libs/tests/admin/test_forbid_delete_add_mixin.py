from django.contrib import admin

import pytest

from libs.tests.admin.app_for_testing import (
    Post,
    PostAdmin,
    PostAdminWithExcludeField,
    PostAdminWithExcludeFieldInForm,
    PostAdminWithFieldsAttr,
)


@pytest.fixture(scope="module")
def post_admin():
    """Create PostAdmin for testing"""
    return PostAdmin(Post, admin.AdminSite())


@pytest.fixture(scope="module")
def post_admin_with_fields_attr():
    """Create PostAdminWithFieldsAttr for testing"""
    return PostAdminWithFieldsAttr(Post, admin.AdminSite())


@pytest.fixture(scope="module")
def post_admin_with_exclude_field():
    """Create PostAdminWithExcludeField for testing"""
    return PostAdminWithExcludeField(Post, admin.AdminSite())


@pytest.fixture(scope="module")
def post_admin_exclude_field_in_form():
    """Create PostAdminWithExcludeFieldInForm for testing"""
    return PostAdminWithExcludeFieldInForm(Post, admin.AdminSite())


def test_get_readonly_fields(post_admin):
    """Test ``get_readonly_fields`` should return all fields of model"""
    assert post_admin.get_readonly_fields(None), ['title', 'text']


def test_get_readonly_fields_with_fields_attr(post_admin_with_fields_attr):
    """Test ``get_readonly_fields`` with ``fields`` attribute, should return
    attribute value"""
    assert post_admin_with_fields_attr.get_readonly_fields(None),\
        ['test_field']


def test_get_readonly_fields_with_exclude_fields(
    post_admin_with_exclude_field
):
    """Test ``get_readonly_fields`` with ``exclude`` attribute, should not
    return fields which points in ``exclude``"""
    assert post_admin_with_exclude_field.get_readonly_fields(None), ['text']


def test_get_readonly_fields_with_exclude_fields_in_form(
    post_admin_exclude_field_in_form
):
    """Test ``get_readonly_fields`` with ``exclude`` attribute in ``Meta``
    class in form which defined in admin class"""
    assert post_admin_exclude_field_in_form.get_readonly_fields(None), ['text']
