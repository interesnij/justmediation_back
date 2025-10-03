import factory
from cities_light.management.commands import cities_light


class CityFactory(factory.DjangoModelFactory):
    """Factory for generating test `City` model."""
    name = factory.Faker('sha256')

    class Meta:
        model = cities_light.City


class RegionFactory(factory.DjangoModelFactory):
    """Factory for generating test `Region` model."""

    name = factory.Faker('sha256')

    class Meta:
        model = cities_light.Region

    @factory.post_generation
    def city_set(self, create, extracted, **kwargs):
        """Generate cities for region.

        Cities requires country and region on creation. Doesn't work with
        RelatedFactoryList.
        """
        self.city_set.set(CityFactory.create_batch(
            region=self, country=self.country, size=5
        ))


class CountryFactory(factory.DjangoModelFactory):
    """Factory for generating test `Country` model."""

    name = factory.Faker('sha256')

    class Meta:
        model = cities_light.Country

    @factory.post_generation
    def region_set(self, create, extracted, **kwargs):
        """Generate regions for country.

        Regions requires country on creation. Doesn't work with
        RelatedFactoryList.
        """
        self.region_set.set(RegionFactory.create_batch(
            country=self, size=5
        ))
