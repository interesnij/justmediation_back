__all__ = (
    'M2MChangedSignalHandler',
)


class M2MChangedSignalHandler(object):
    """ Используется в качестве обработчиков сигналов M2M.
    Все сигналы M2M в Django обрабатываются одним обработчиком, который получает `действие`
    атрибут. `действие` содержит тип сигнала (post_add,
    post_remove, post_clear и т.д.) Подробнее о сигналах m2m вы можете найти в Django docs.

    У этого класса есть один метод - `handle`, который имеет ту же сигнатуру,
    что и обработчик m2m-сигнала.

    Чтобы добавить обработку конкретного сигнала m2m, вам необходимо реализовать
    подходящий метод для конкретного действия.

    Примеры:
        # реализовать обработчик
        class MyM2MHandler(M2MChangedSignalHandler):
            def post_add(self):
                # сделай что-нибудь

            def post_remove(self):
                # сделай что-нибудь

        # обработчик регистрации
        # как только сигнал должен быть функцией (не методом класса), мы должны
        # зарегистрировать этот обработчик таким образом

        @receiver(m2m_changed, sender=AppUser.groups.through)
        def signal_m2m_changed_auth_group(**kwargs):
            MyM2MHandler(**kwargs).handle()
    """

    def __init__(
            self, sender, instance, action, reverse, model, pk_set, **kwargs):
        self.sender = sender
        self.instance = instance
        self.action = action
        self.reverse = reverse
        self.model = model
        self.pk_set = pk_set or ()
        self.kwargs = kwargs

    def handle(self):
        """ Сигнал процесса. """
        handler = getattr(self, self.action, None)
        if not handler:
            return
        handler()

    def pre_add(self):
        """ Выполните действие перед добавлением. """
        pass

    def post_add(self):
        """ Выполните действие после добавления. """
        pass

    def pre_remove(self):
        """ Выполните действие перед удалением. """
        pass

    def post_remove(self):
        """ Выполните действие после удаления. """
        pass

    def pre_clear(self):
        """ Выполните действие перед очисткой. """
        pass

    def post_clear(self, sender, instance, reverse, model, pk_set, **kwargs):
        """ Выполните действие после очистки. """
        pass
