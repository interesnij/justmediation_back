import math
from django.db.models import Q
from rest_framework import mixins
from rest_framework.permissions import AllowAny
from cities_light.management.commands import cities_light
from cities_light.management.commands.cities_light import Region
from apps.core.api.views import BaseViewSet
from ..api import filters, serializers


class TopCityViewSet(mixins.ListModelMixin, BaseViewSet):
    """ Просмотр Api для отображения списка всех городов """
    serializer_class = serializers.CitySerializer
    base_permission_classes = (AllowAny,)
    queryset = cities_light.City.objects.select_related('region')
    search_fields = [
        'name',
    ]
    filter_class = filters.CityFilter

    def get_queryset(self):
        if self.request.query_params.get('is_top') == 'false':
            qs = super().get_queryset().filter(
                Q(name='New York City') |
                Q(name='City of London') |
                Q(display_name='Sydney, New South Wales, Australia') |
                Q(name='Tokyo')
            )
        else:
            qs = super().get_queryset().filter(
                Q(
                    name='Philadelphia',
                    region=Region.objects.get(name='Pennsylvania')) |
                Q(
                    name='Baltimore',
                    region=Region.objects.get(name='Maryland')) |
                Q(
                    name='Newark',
                    region=Region.objects.get(name='New Jersey')) |
                Q(
                    name='Jersey City',
                    region=Region.objects.get(name='New Jersey')) |
                Q(
                    name='New Haven',
                    region=Region.objects.get(name='Connecticut')) |
                Q(
                    name='Boston',
                    region=Region.objects.get(name='Massachusetts')) |
                Q(
                    name='New York City',
                    region=Region.objects.get(name='New York')) |
                Q(
                    name='Hartford',
                    region=Region.objects.get(name='Connecticut')) |
                Q(
                    name='Washington',
                    region=Region.objects.get(name='Washington, D.C.')) |
                Q(
                    name='Yonkers',
                    region=Region.objects.get(name='New York'))
            )
        return qs


class CityViewSet(mixins.ListModelMixin, BaseViewSet):
    """ Просмотр Api для отображения списка всех городов """
    serializer_class = serializers.CitySerializer
    base_permission_classes = (AllowAny,)
    queryset = cities_light.City.objects.select_related('region', 'country')
    filter_class = filters.CityFilter

    def get_queryset(self):
        qs = super().get_queryset()
        qp = self.request.query_params
        latitude = qp.get('latitude', None)
        longitude = qp.get('longitude', None)

        def HaversineDistance(location1, location2):
            """ Способ вычисления расстояния между двумя наборами широты/Lon. """
            lat1, lon1 = location1
            lat2, lon2 = location2
            earth = 6371
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat / 2) * math.sin(dlat / 2) + \
                math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
                math.sin(dlon / 2) * math.sin(dlon / 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            d = earth * c
            return d

        def get_closest_cities():
            allcities = qs.values_list('id', 'latitude', 'longitude')
            nearest = None
            distance = 10000
            for city in allcities:
                _distance = HaversineDistance(
                    (float(latitude), float(longitude)),
                    (float(city[1]), float(city[2]))
                )
                if _distance < distance:
                    nearest = city
                    distance = _distance
            return nearest

        if latitude and longitude:
            nearest = get_closest_cities()
            qs = qs.filter(id=nearest[0])
        search = qp.get('search', '')
        if search == '':
            return qs
        else:
            q1 = qs.filter(name__istartswith=search)
            q2 = qs.filter(name__icontains=' ' + search)
            ids = q1.union(q2, all=True).values_list('id', flat=True)
            clauses_list = []
            for i, pk in enumerate(ids):
                clauses_list.append(f'WHEN cities_light_city.id={pk} THEN {i}')
            clauses = ' '.join(clauses_list)
            ordering = 'CASE %s END' % clauses
            return qs.filter(id__in=ids).extra(
                select={'ordering': ordering}, order_by=('ordering',)
            )


class RegionsViewSet(mixins.ListModelMixin, BaseViewSet):
    """ Представление Api для отображения списка всех регионов (штатов) """
    serializer_class = serializers.RegionSerializer
    base_permission_classes = (AllowAny,)
    queryset = cities_light.Region.objects.all()
    filter_class = filters.RegionFilter

    def get_queryset(self):
        qs = super().get_queryset()
        qp = self.request.query_params
        search = qp.get('search', '')
        if search == '':
            return qs
        else:
            q1 = qs.filter(name__istartswith=search)
            q2 = qs.filter(name__icontains=' ' + search)
            ids = q1.union(q2, all=True).values_list('id', flat=True)
            clauses = ' '.join(
                ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(ids)]
            )
            ordering = 'CASE %s END' % clauses
            return qs.filter(id__in=ids).extra(
                select={'ordering': ordering}, order_by=('ordering',)
            )


class CountryViewSet(mixins.ListModelMixin, BaseViewSet):
    """ Просмотр Api для отображения списка всех стран """
    serializer_class = serializers.CountryWithStateSerializer
    base_permission_classes = (AllowAny,)
    queryset = cities_light.Country.objects.prefetch_related('region_set')

    def get_queryset(self):
        qs = super().get_queryset()
        qp = self.request.query_params
        search = qp.get('search', '')
        if search == '':
            return qs
        else:
            q1 = qs.filter(name__istartswith=search)
            q2 = qs.filter(name__icontains=' ' + search)
            ids = q1.union(q2, all=True).values_list('id', flat=True)
            clauses = ' '.join(
                ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(ids)]
            )
            ordering = 'CASE %s END' % clauses
            return qs.filter(id__in=ids).extra(
                select={'ordering': ordering}, order_by=('ordering',)
            )
