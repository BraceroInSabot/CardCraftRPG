from django.urls import include, path

urlpatterns = [
    path("api/", include("cardcraft.presentation.api.urls")),
]
