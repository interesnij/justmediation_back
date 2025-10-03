class TransitionFailedException(Exception):
    """ Исключение возникло, когда мы получили сообщение об ошибке при переходе статуса.
    Примеры:
        @transition(
            field=status,
            source=STATUS_SENT,
            target=STATUS_PAID,
            on_error_STATUS_PAYMENT_FAILED,
        )
        def pay(self):
            try:
                services.pay(self)
                obj.save()
            except PaymentException as e:
                raise TransitionFailedException

    """
