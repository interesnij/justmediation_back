from rest_framework import serializers


class FirestoreCredentialsSerializer(serializers.Serializer):
    """ Простой сериализатор для учетных данных Firestore """
    token = serializers.ReadOnlyField()
