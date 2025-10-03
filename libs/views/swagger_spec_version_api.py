from rest_framework.response import Response
from rest_framework.views import APIView

from libs.swagger import get_current_swagger_spec_version


class SwaggerSpecVersionView(APIView):
    """ Просмотр для поиска версии swagger. """

    def get(self, request):
        """ Сообщите версию спецификации swagger, которую использует API. """
        return Response({
            'version': get_current_swagger_spec_version()
        })
