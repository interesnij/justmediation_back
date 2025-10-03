# Configure `django-cities-light` package

# define possible for translation languages
CITIES_LIGHT_TRANSLATION_LANGUAGES = ['en']
# define for what countries cities and regions would be uploaded
CITIES_LIGHT_INCLUDE_COUNTRIES = [
    'US',
    'DZ',
    'AU',
    'AT',
    'AW',
    'AG',
    'BS',
    'BE',
    'BR',
    'CL',
    'CO',
    'CR',
    'DK',
    'DO',
    'EC',
    'FJ',
    'FI',
    'FR',
    'GR',
    'HK',
    'IN',
    'ID',
    'IE',
    'IT',
    'LU',
    'MY',
    'MX',
    'MC',
    'NZ',
    'PA',
    'PG',
    'PH',
    'PT',
    'SG',
    'ZA',
    'ES',
    'SE',
    'CH',
    'AE',
    'GB',
    'VE',
    'VU',
    'CA',
    'IL',
    'JP',
]
CITIES_LIGHT_INCLUDE_CITY_TYPES = [
    'PPL',
    'PPLA',
    'PPLA2',
    'PPLA3',
    'PPLA4',
    'PPLC',
    'PPLF',
    'PPLG',
    'PPLL',
    'PPLR',
    'PPLS',
    'STLMT',
]
CITIES_LIGHT_CITY_SOURCES = ['http://download.geonames.org/export/dump/cities500.zip']
# According to docs of `django-cities-light` :
# If your database engine for cities_light supports indexing TextFields
# (ie. it is not MySQL), then this should be set to True.
INDEX_SEARCH_NAMES = True
