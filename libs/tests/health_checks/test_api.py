from django.urls import reverse_lazy

from rest_framework.test import APIClient

import pytest

from ...health_checks.apps import HEALTH_CHECKS
from ...testing.constants import OK


def health_check_url():
    """Get api health check url."""
    return reverse_lazy('v1:health_check:health_check')


@pytest.mark.parametrize(argnames='check', argvalues=HEALTH_CHECKS)
def test_health_check_api(api_client: APIClient, check: str):
    """Check that every defined health check works(one by one)."""
    url = f'{health_check_url()}?checks={check}'
    response = api_client.get(url)
    assert response.status_code == OK
    assert check in response.data, response.data
    assert response.data[check]['status'] == 'OK', response.data
