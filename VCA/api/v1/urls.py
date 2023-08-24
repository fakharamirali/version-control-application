from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("application", views.AppVersionViewSet)


urlpatterns = router.urls
app_name = "VCA-api-V1"
