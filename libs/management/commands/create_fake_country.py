from django.conf import settings
from django.core.management import BaseCommand
from libs.django_cities_light.factories import CountryFactory


class Command(BaseCommand):
    """ Создайте фальшивую страну.
    Команда Django cities light manage для загрузки данных о местоположении занимает слишком
    много времени и может раздражать. Вместо этого вы можете использовать это.
    """
    help = 'Generate fake country'

    def handle(self, *args, **options) -> None:
        assert settings.ENVIRONMENT != 'production'

        country = CountryFactory()
        self.stdout.write(f'Fake country {country.name} has been created')
