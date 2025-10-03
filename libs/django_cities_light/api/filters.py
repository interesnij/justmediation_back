from cities_light.management.commands import cities_light
from django_filters import FilterSet


class CityFilter(FilterSet):
    """Filter class for `City` model."""

    class Meta:
        model = cities_light.City
        fields = (
            'region',
            'country',
        )


class RegionFilter(FilterSet):
    """Filter class for `Region` model."""

    class Meta:
        model = cities_light.Region
        fields = (
            'country',
        )
