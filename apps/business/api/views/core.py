from rest_framework.permissions import IsAuthenticated
from rest_condition import And, Or
from ....users.api.permissions import (
    IsMediatorHasActiveSubscription,
    IsClient,
    IsSupportPaidFee,
)


class BusinessViewSetMixin:
    """ Микширование, которое сочетает в себе аналогичную логику представлений "business" 
    приложения. Все представления имеют одинаковые разрешения на действия:
    * "клиент" - может перечислять и извлекать только те экземпляры, в которых он является клиентом
        (или клиент matter).
    * "адвокат" - может создавать, удалять, перечислять, извлекать и обновлять экземпляры
        где он является адвокатом (или поверенным по делу) или если он является адвокатом
        с которым этот вопрос был доведен до сведения общественности.
    * "поддержка" - может создавать (не всегда), удалять, перечислять, извлекать и
        обновлять экземпляры, к которым он имеет общий доступ.
    """
    mediator_permissions = (
        IsAuthenticated,
        IsMediatorHasActiveSubscription,
    )
    client_permissions = (
        IsAuthenticated,
        IsClient,
    )
    mediator_support_permissions = Or(
        And(IsAuthenticated(), IsMediatorHasActiveSubscription()),
        And(IsAuthenticated(), IsSupportPaidFee()),
    )
    support_permissions = Or(
        And(IsAuthenticated(), IsMediatorHasActiveSubscription()),
        And(IsAuthenticated(), IsSupportPaidFee()),
    )
    permissions_map = {
        'create': (mediator_support_permissions,),
        'update': (mediator_support_permissions,),
        'partial_update': (mediator_support_permissions,),
        'destroy': (mediator_support_permissions,),
    }

    def get_queryset(self):
        """ Отфильтруйте все доступные для пользователей экземпляры
        Здесь возвращаются экземпляры, где текущий пользователь является клиентом (если он
        клиент) или адвокатом (если он адвокат).
        """
        qs = super().get_queryset()
        order_param = self.request.query_params.get('ordering', None)
        if order_param == '' or order_param is None:
            return qs.available_for_user(self.request.user).order_by('id')
        return qs.available_for_user(self.request.user)
