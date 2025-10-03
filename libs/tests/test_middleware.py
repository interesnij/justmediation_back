from unittest.mock import MagicMock

import pytest
from faker import Faker

from libs.middleware import TimezoneMiddleware

faker = Faker()


@pytest.fixture(scope="function")
def middleware():
    """Create middleware for testing"""
    return TimezoneMiddleware()


@pytest.fixture(scope="function")
def request_mock():
    """Create admin view for testing"""
    return MagicMock()


def test_process_request(middleware, request_mock):
    """Ensure that is ``tzname`` not in ``pytz`` available timezones
    have no side effects.
    """
    request_mock.META = {'HTTP_USER_TIMEZONE': 'Test'}
    middleware.process_request(request_mock)
    assert isinstance(request_mock, MagicMock)


def test_if_tzname_is_none(middleware, request_mock):
    """Ensure, that if header is not exists, function call have no side
    effects.
    """
    request_mock.META = {}
    middleware.process_request(request_mock)
    assert isinstance(request_mock, MagicMock)


def test_if_tzname_is_correct(middleware, request_mock):
    """Ensure, that if correct timezone passed in headers
    ``request.timezone`` will store timezone.
    """
    timezone = 'Asia/Krasnoyarsk'
    request_mock.META = {'HTTP_USER_TIMEZONE': timezone}
    middleware.process_request(request_mock)
    # Assert side effects
    assert str(request_mock.timezone) == timezone
