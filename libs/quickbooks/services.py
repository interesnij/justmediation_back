""" Различные дополнительные методы и ярлыки. """


def create_qb_object(qb_class, **kwargs):
    """ Создайте простой объект quickbooks. """
    qb_object = qb_class()
    for key, value in kwargs.items():
        setattr(qb_object, key, value)
    return qb_object
