from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path("api/", include("cardcraft.presentation.api.urls")),
]

# Serve uploaded card images during development.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
