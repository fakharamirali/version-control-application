from django.urls import path, include

urlpatterns = [
    path("v1/", include("VCA.api.v1.urls"))
]
