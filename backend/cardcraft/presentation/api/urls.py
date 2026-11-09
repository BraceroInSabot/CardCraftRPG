"""API routes: one REST resource per entity, all served by ``EntityViewSet``."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from cardcraft.container import get_container

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
    return lambda: getattr(get_container(), attribute)


router = DefaultRouter(trailing_slash=True)
for prefix, name, attribute, serializer, list_params in RESOURCES:
    viewset = EntityViewSet.for_resource(name, _provider(attribute), serializer, list_params)
    router.register(prefix, viewset, basename=prefix)

urlpatterns = [
    path("meta/", meta, name="meta"),
    path("health/", health, name="health"),
    path("", include(router.urls)),
]
