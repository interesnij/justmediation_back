from unittest.mock import patch

from libs.admin.mixins import FkAdminLink
from libs.tests.admin.app_for_testing import Post


@patch('django.urls.URLResolver._reverse_with_prefix', return_value='test')
def test_admin_url(url_resolver):
    """Test for related object link generation"""
    post = Post(title='title', text='test')
    fk_admin_link = FkAdminLink()
    # Assert without title
    assert fk_admin_link._admin_url(post) == \
        "<a href='test' target='_blank'>title</a>"

    # Assert when title transferred to ``_admin_url``
    assert fk_admin_link._admin_url(post, 'test') == \
        "<a href='test' target='_blank'>test</a>"
