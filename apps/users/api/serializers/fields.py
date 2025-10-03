from rest_framework.fields import CharField
from ....users import models


class MediatorUniversityField(CharField):
    """ Поле, которое позволяет использовать "Университет" по `названию` в сериализаторе. """

    def to_internal_value(self, title):
        """ Преобразуйте данные в экземпляр `University`.
        Если есть университет с указанным названием, мы возвращаем этот университет,
        в противном случае мы создаем новый университет с указанным названием.
        """
        title = super().to_internal_value(title)
        try:
            return models.MediatorUniversity.objects.get(title__iexact=title)
        except models.MediatorUniversity.DoesNotExist:
            return models.MediatorUniversity(title=title)
