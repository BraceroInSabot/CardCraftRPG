"""HTTP controllers.

One generic ViewSet adapts any ``CrudUseCases`` bundle to REST. Views only
parse input, call a use case and render output; they never touch the ORM.
"""

from __future__ import annotations

from collections.abc import Callable

from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from cardcraft.application import CrudUseCases
from cardcraft.domain.entities import Rarity, SkillKind
from cardcraft.domain.queries import MAX_PAGE_SIZE

from .serializers import ListParamsSerializer, NamedEntitySerializer

UseCasesProvider = Callable[[], CrudUseCases]


class EntityViewSet(viewsets.ViewSet):
    """Generic CRUD controller configured through class attributes."""

    lookup_value_regex = r"\d+"

    use_cases_provider: UseCasesProvider
    serializer_class: type[NamedEntitySerializer]
    list_params_class: type[ListParamsSerializer] = ListParamsSerializer

    @classmethod
    def for_resource(
        cls,
        name: str,
        use_cases_provider: UseCasesProvider,
        serializer_class: type[NamedEntitySerializer],
        list_params_class: type[ListParamsSerializer] = ListParamsSerializer,
    ) -> type[EntityViewSet]:
        return type(
            f"{name}ViewSet",
            (cls,),
            {
                "use_cases_provider": staticmethod(use_cases_provider),
                "serializer_class": serializer_class,
                "list_params_class": list_params_class,
            },
        )

    @property
    def use_cases(self) -> CrudUseCases:
        return self.use_cases_provider()

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
                "results": self.serializer_class(page.items, many=True).data,
            }
        )

    def retrieve(self, request: Request, pk: str) -> Response:
        entity = self.use_cases.get.execute(int(pk))
        return Response(self.serializer_class(entity).data)

    def create(self, request: Request) -> Response:
        payload = self._validated(request)
        entity = self.use_cases.create.execute(payload)
        return Response(self.serializer_class(entity).data, status=status.HTTP_201_CREATED)

    def update(self, request: Request, pk: str) -> Response:
        return self._update(request, int(pk), partial=False)

    def partial_update(self, request: Request, pk: str) -> Response:
        return self._update(request, int(pk), partial=True)

    def destroy(self, request: Request, pk: str) -> Response:
        self.use_cases.delete.execute(int(pk))
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _update(self, request: Request, entity_id: int, partial: bool) -> Response:
        payload = self._validated(request, partial=partial)
        entity = self.use_cases.update.execute(entity_id, payload)
        return Response(self.serializer_class(entity).data)

    def _validated(self, request: Request, partial: bool = False) -> dict:
        serializer = self.serializer_class(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        return dict(serializer.validated_data)


def _labelled(enum_cls) -> list[dict[str, str]]:
    return [{"value": m.value, "label": m.value.replace("_", " ").title()} for m in enum_cls]


@api_view(["GET"])
def meta(request: Request) -> Response:
    """Static choices the UI needs to build forms and filters."""
    return Response(
        {
            "rarities": _labelled(Rarity),
            "skill_kinds": _labelled(SkillKind),
            "max_page_size": MAX_PAGE_SIZE,
        }
    )


@api_view(["GET"])
def health(request: Request) -> Response:
    return Response({"status": "ok"})
