
from django.urls import include, path

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register(
    r'leads',
    views.LeadViewSet,
    basename='leads'
)
router.register(
    r'posted-matter',
    views.PostedMatterViewSet,
    basename='posted-matter'
)
router.register(
    r'proposals',
    views.ProposalViewSet,
    basename='posted-matter'
)
router.register(
    r'matters',
    views.MatterViewSet,
    basename='matters'
)
router.register(
    r'time-billing',
    views.BillingItemViewSet,
    basename='billing-item'
)
router.register(
    r'invoices',
    views.InvoiceViewSet,
    basename='invoices'
)
router.register(
    r'activities',
    views.ActivityViewSet,
    basename='activities'
)
router.register(
    r'stages',
    views.StageViewSet,
    basename='stages'
)
router.register(
    r'notes',
    views.NoteViewSet,
    basename='notes'
)
router.register(
    r'checklist',
    views.ChecklistEntryViewSet,
    basename='checklist'
)

router.register(
    'matter-post',
    views.MatterPostViewSet,
    basename='matter-post',
)

router.register(
    'matter-comment',
    views.MatterCommentViewSet,
    basename='matter-comment',
)

router.register(
    'voice-consent',
    views.VoiceConsentViewSet,
    basename='voice-consent',
)

router.register(
    'video-calls',
    views.VideoCallViewSet,
    basename='video-calls',
)

router.register(
    'statistics',
    views.StatisticsViewSet,
    basename='business-statistics',
)

router.register(
    'matter-shared-with',
    views.MatterSharedWithViewSet,
    basename='matter-shared-with',
)

router.register(
    'opportunities',
    views.OpportunityViewSet,
    basename='opportunities',
)

urlpatterns = [
    path(r'', include(router.urls))
]

