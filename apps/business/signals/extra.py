from django.dispatch import Signal

new_video_call = Signal(providing_args=('instance',))
new_video_call.__doc__ = (
    'Signal that indicates that a new video call was created'
)

new_matter_referred = Signal(providing_args=('instance',))
new_matter_referred.__doc__ = (
    'Signal that indicates that a new matter was referred'
)

new_referral_accepted = Signal(providing_args=('instance',))
new_referral_accepted.__doc__ = (
    'Signal that indicates that a matter you referred was accepted'
)

new_referral_declined = Signal(providing_args=('instance',))
new_referral_declined.__doc__ = (
    'Signal that indicates that a matter you referred was declined'
)

matter_referral_revoked = Signal(providing_args=('instance',))
matter_referral_revoked.__doc__ = (
    'Signal that indicates that a referral of matter was revoked'
)
