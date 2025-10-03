from rest_framework import status

# Ярлыки статусов
# Используется для сокращения времени параметризации теста
OK = status.HTTP_200_OK
CREATED = status.HTTP_201_CREATED
NO_CONTENT = status.HTTP_204_NO_CONTENT

FOUND = status.HTTP_302_FOUND

BAD_REQUEST = status.HTTP_400_BAD_REQUEST
UNAUTHORIZED = status.HTTP_401_UNAUTHORIZED
FORBIDDEN = status.HTTP_403_FORBIDDEN
NOT_FOUND = status.HTTP_404_NOT_FOUND
CONFLICT = status.HTTP_409_CONFLICT
