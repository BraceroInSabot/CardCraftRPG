"""API routes: one REST resource per entity, all served by ``EntityViewSet``."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from cardcraft.container import container_for, get_image_storage

from . import account_views as accounts
from . import serializers as s
from .views import EntityViewSet, health, meta

# (url prefix, ViewSet name, container attribute, serializer, list params)
RESOURCES = (
    ("systems", "RpgSystem", "systems", s.RpgSystemSerializer, s.ListParamsSerializer),
    ("campaigns", "Campaign", "campaigns", s.CampaignSerializer, s.CampaignListParams),
    ("items", "Item", "items", s.ItemSerializer, s.ItemListParams),
    ("races", "Race", "races", s.RaceSerializer, s.SystemScopedListParams),
    ("race-skills", "RaceSkill", "race_skills", s.RaceSkillSerializer, s.RaceSkillListParams),
    ("classes", "CharacterClass", "classes", s.CharacterClassSerializer, s.SystemScopedListParams),
    ("class-skills", "ClassSkill", "class_skills", s.ClassSkillSerializer, s.ClassSkillListParams),
)


def _provider(attribute: str):
    return lambda owner_id: getattr(container_for(owner_id), attribute)


router = DefaultRouter(trailing_slash=True)
for prefix, name, attribute, serializer, list_params in RESOURCES:
    viewset = EntityViewSet.for_resource(name, _provider(attribute), get_image_storage, serializer, list_params)
    router.register(prefix, viewset, basename=prefix)

urlpatterns = [
    path("meta/", meta, name="meta"),
    path("health/", health, name="health"),
    path("auth/csrf/", accounts.CsrfView.as_view(), name="auth-csrf"),
    path("auth/login/", accounts.LoginView.as_view(), name="auth-login"),
    path("auth/logout/", accounts.LogoutView.as_view(), name="auth-logout"),
    path("account/", accounts.AccountView.as_view(), name="account"),
    path("account/profile/", accounts.ProfileView.as_view(), name="account-profile"),
    path("account/card-defaults/", accounts.CardDefaultsView.as_view(), name="account-card-defaults"),
    path("account/password/", accounts.PasswordView.as_view(), name="account-password"),
    path("", include(router.urls)),
]
