"""HTTP controllers.

One generic ViewSet adapts any ``CrudUseCases`` bundle to REST. Views only
parse input, call a use case and render output; they never touch the ORM.
"""

from __future__ import annotations

from collections.abc import Callable

from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response

from cardcraft.application import MAX_IMAGE_BYTES, CardUseCases, ImageStorage, ImageUpload
from cardcraft.domain.entities import Rarity, SkillKind
from cardcraft.domain.queries import MAX_PAGE_SIZE

from .serializers import ImageUploadSerializer, ListParamsSerializer, NamedEntitySerializer

UseCasesProvider = Callable[[], CardUseCases]
StorageProvider = Callable[[], ImageStorage]


class EntityViewSet(viewsets.ViewSet):
    """Generic CRUD controller configured through class attributes."""

    lookup_value_regex = r"\d+"

    use_cases_provider: UseCasesProvider
    storage_provider: StorageProvider
    serializer_class: type[NamedEntitySerializer]
    list_params_class: type[ListParamsSerializer] = ListParamsSerializer

    @classmethod
    def for_resource(
        cls,
        name: str,
        use_cases_provider: UseCasesProvider,
        storage_provider: StorageProvider,
        serializer_class: type[NamedEntitySerializer],
        list_params_class: type[ListParamsSerializer] = ListParamsSerializer,
    ) -> type[EntityViewSet]:
        return type(
            f"{name}ViewSet",
            (cls,),
            {
                "use_cases_provider": staticmethod(use_cases_provider),
                "storage_provider": staticmethod(storage_provider),
                "serializer_class": serializer_class,
                "list_params_class": list_params_class,
            },
        )

    @property
    def use_cases(self) -> CardUseCases:
        return self.use_cases_provider()

    def _render(self, entity_or_entities, many: bool = False):
        context = {"request": self.request, "image_url": self.storage_provider().url}
        return self.serializer_class(entity_or_entities, many=many, context=context).data

    def list(self, request: Request) -> Response:
        params = self.list_params_class(data=request.query_params)
        params.is_valid(raise_exception=True)
        page = self.use_cases.list.execute(params.to_query())
        return Response(
            {
                "count": page.total,
                "page": page.page,
                "page_size": page.page_size,
                "total_pages": page.total_pages,
                "results": self._render(page.items, many=True),
            }
        )

    def retrieve(self, request: Request, pk: str) -> Response:
        entity = self.use_cases.get.execute(int(pk))
        return Response(self._render(entity))

    def create(self, request: Request) -> Response:
        payload = self._validated(request)
        entity = self.use_cases.create.execute(payload)
        return Response(self._render(entity), status=status.HTTP_201_CREATED)

    def update(self, request: Request, pk: str) -> Response:
        return self._update(request, int(pk), partial=False)

    def partial_update(self, request: Request, pk: str) -> Response:
        return self._update(request, int(pk), partial=True)

    def destroy(self, request: Request, pk: str) -> Response:
        self.use_cases.delete.execute(int(pk))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post", "delete"], url_path="image", parser_classes=[MultiPartParser])
    def image(self, request: Request, pk: str) -> Response:
        """``POST`` a multipart ``image`` file to set the card art; ``DELETE`` to remove it."""
        if request.method == "DELETE":
            return Response(self._render(self.use_cases.remove_image.execute(int(pk))))
        serializer = ImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data["image"]
        # Read one byte past the limit so oversized files are rejected without loading them whole.
        upload = ImageUpload(content=file.read(MAX_IMAGE_BYTES + 1), filename=file.name)
        return Response(self._render(self.use_cases.set_image.execute(int(pk), upload)))

    def _update(self, request: Request, entity_id: int, partial: bool) -> Response:
        payload = self._validated(request, partial=partial)
        entity = self.use_cases.update.execute(entity_id, payload)
        return Response(self._render(entity))

    def _validated(self, request: Request, partial: bool = False) -> dict:
        serializer = self.serializer_class(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        return dict(serializer.validated_data)


def _labelled(enum_cls) -> list[dict[str, str]]:
    return [{"value": m.value, "label": getattr(m, "label", m.value.replace("_", " ").title())} for m in enum_cls]


@api_view(["GET"])
def meta(request: Request) -> Response:
    """Static choices the UI needs to build forms and filters."""
    return Response(
        {
            "rarities": _labelled(Rarity),
            "skill_kinds": _labelled(SkillKind),
            "max_page_size": MAX_PAGE_SIZE,
            "max_image_bytes": MAX_IMAGE_BYTES,
        }
    )


@api_view(["GET"])
def health(request: Request) -> Response:
    return Response({"status": "ok"})
