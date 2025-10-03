from rest_framework import serializers
from cities_light.management.commands import cities_light

# Запрос страны по умолчанию, который будет использоваться при создании нового города.
default_country_query = cities_light.Country.objects.filter(code2='US')


class CountryWithStateSerializer(serializers.ModelSerializer):
    """Serializer for Country model."""
    has_state = serializers.SerializerMethodField()

    def get_has_state(self, obj):
        return obj.region_set.exists()

    class Meta:
        model = cities_light.Country
        fields = (
            'id', 'name', 'code2', 'phone', 'has_state'
        )


class CountrySerializer(serializers.ModelSerializer):
    """Serializer for Country model."""

    class Meta:
        model = cities_light.Country
        fields = (
            'id', 'name', 'code2', 'phone'
        )


class RegionSerializer(serializers.ModelSerializer):
    """Serializer for Region model."""
    class Meta:
        model = cities_light.Region
        fields = (
            'id', 'name'
        )


class CitySerializer(serializers.ModelSerializer):
    """Serializer for City model."""
    id = serializers.IntegerField(required=False)
    name = serializers.CharField(required=False)
    state = RegionSerializer(source='region', read_only=True)
    country = CountrySerializer(read_only=True)

    class Meta:
        model = cities_light.City
        fields = (
            'id', 'name', 'state', 'country', 'latitude', 'longitude'
        )

    def validate(self, attrs):
        """Create new City if no PK provided."""
        attrs = super().validate(attrs)
        city_id, city_name = attrs.get('id'), attrs.get('name')

        city = None
        if city_id:
            city = cities_light.City.objects.filter(id=city_id).first()
        elif city_name:
            city, _ = cities_light.City.objects.get_or_create(
                country=default_country_query.first(),
                name=city_name,
            )

        if not city:
            raise serializers.ValidationError(
                {'name': 'No city was found or created.'}
            )

        return city


class CityShortSerializer(CitySerializer):

    class Meta(CitySerializer.Meta):
        fields = (
            'id', 'name'
        )
