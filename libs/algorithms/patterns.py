class Singleton(type):
    """ Единый паттерн.

    Использование:
    class Example(object, metaclass=Singleton):
        pass
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        """ Возвращает экземпляр singleton. """
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args,
                                                                 **kwargs)
        return cls._instances[cls]
