from rest_framework.routers import DefaultRouter, path
from .views import *

router = DefaultRouter()
router.register('categories', CategoryViewSet)
router.register('habits', HabitViewSet)
router.register('habitlogs', HabitLogViewSet)

urlpatterns = router.urls + [
    path('statistics/', StatisticsView.as_view()),
]
