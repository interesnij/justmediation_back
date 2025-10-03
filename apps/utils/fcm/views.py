from django.http import Http404

from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet


class FCMViewSet(FCMDeviceAuthorizedViewSet):
    """Viewset managing user's FCM devices for push notifications."""

    def get_object(self):
        """Overridden to fix FCMDevice.MultipleObjectsReturned.

        The reason for this happening it that FCM Django allows creation of
        duplicate inactive devices with the same registration id for one user.
        But in ViewSet method get_object it's not filtered to fetch only
        active, thus returning more than one.

        We change it to return the latest created matched(by registration_id)
        device.

        For more information:
        https://sentry.saritasa.io/saritasa/jlp/issues/3957/

        """
        queryset = self.filter_queryset(self.get_queryset())

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        # Get latest created device with request's registration_id
        obj = queryset.filter(**filter_kwargs).order_by(
            '-date_created'
        ).first()
        if not obj:
            raise Http404

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj
