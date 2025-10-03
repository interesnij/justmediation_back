from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from libs.firebase import default_firestore_client as firestore
from . import serializers


class FirestoreCredentialsView(GenericViewSet):
    """ Просмотр API для получения учетных данных Firestore. """
    pagination_class = None
    permission_classes = IsAuthenticated,
    serializer_class = serializers.FirestoreCredentialsSerializer

    @action(methods=['GET'], detail=False, url_path='get-credentials')
    def get(self, *args, **kwargs):
        """ API-метод для получения токена Firestore для команды frontend.
        С помощью этого токена команда frontend может работать с firebase sdk и создавать
        соответствующие диаграммы и т.д.
        """
        user_token = firestore.generate_token(self.request.user)
        serializer = self.get_serializer({'token': user_token})
        return Response(data=serializer.data, status=status.HTTP_200_OK)
