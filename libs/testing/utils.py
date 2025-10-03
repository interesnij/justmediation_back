import tempfile
from django.utils import timezone


def generate_file(size=1024):
    """ Генерирует файл заданного размера
    Его можно использовать в тестах

    Аргументы:
        size (int): размер файла
    Возвращается:
        file: сгенерированный файл
    """
    tmp_file = tempfile.NamedTemporaryFile()
    with open(tmp_file.name, 'wb') as out:
        out.write(b'x' * size)
    return tmp_file


def get_curr_time():
    """ Вспомогательная функция для получения текущего времени сервера.
    Текущее серверное время, используемое при синхронизации модели (ищите
    `sync_from` и `sync_to`).

    Активно используется на саммите
    """
    return str(timezone.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
