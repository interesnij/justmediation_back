import arrow

from config.celery import app

from apps.users.models import AppUser, Invite

from . import models, services, signals


@app.task()
def generate_invoices():
    """Celery task to generate Invoice.

    At the 1st day of each new month new `Invoice` is generated for a previous
    month and the task adds all time billings in Invoice period and connects it
    with invoice.

    Invoices are generated only for `hourly` rate typed `active` matters.

    """
    # calculate invoice period
    now = arrow.utcnow().shift(days=-1)
    period_start, period_end = services.get_invoice_period_ranges(now)

    # generate invoices only if there are related time billings
    time_billings = models.BillingItem.objects.all().match_period(
        period_start=period_start,
        period_end=period_end,
    )
    if not time_billings.exists():
        return

    # generate invoices
    matters = models.Matter.objects.open().hourly_rated()
    for matter in matters:
        services.get_invoice_for_matter(matter, period_start, period_end)


@app.task()
def send_shared_matter_notification_task(user_id: int):
    """ Отправьте уведомление "matter shared", когда пользователь будет зарегистрирован 
    и верифицирован. Когда пользователь, с которым был передан материал, зарегистрирован и 
    верифицирован - отправьте matter поделилась с ним уведомлением.

    Метод отправляет только последние сообщения с приглашением для пользователей, которых 
    несколько раз приглашали "share matter".

    """
    user = AppUser.objects.get(id=user_id)
    invites = Invite.objects.filter(
        email__iexact=user.email, matter__isnull=False
    ).order_by('-created')
    matters = []
    for invite in invites:
        matter = invite.matter
        # не обрабатывайте вопросы, по которым уже были отправлены уведомления
        if matter in matters:
            continue

        matters.append(matter)
        matter_shared, created = models.MatterSharedWith.objects.get_or_create(
            matter=matter, user=user
        )
        if not created:
            continue

        # MatterSharedWith is created, sent notification to mediator and
        # support
        signals.new_matter_shared.send(
            sender=models.MatterSharedWith,
            instance=matter_shared,
            inviter=invite.inviter,
            title=invite.title,
            message=invite.message,
        )
