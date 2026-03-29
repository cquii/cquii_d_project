import time
from typing import Any, Optional

from django.db.models import Model, QuerySet
from rest_framework import status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import CursorPagination, PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend

from utils.pagination import HybridPagination, StandardPagination


class BaseModelViewSet(ModelViewSet):
    """
    Reusable base ViewSet — configure once, use everywhere.

    Every viewset that extends this class gets full CRUD, filtering,
    search, ordering, and auto-detected pagination for free.

    Required attributes
    -------------------
    model (type[Model])
        Django model class to operate on.
    serializer_class
        DRF serializer for the model.

    Optional attributes
    -------------------
    db_name (str)
        Database alias for ``.using()``.  Default: ``'default'``.
    filterset_class
        django-filter FilterSet class for advanced field filtering.
    search_fields (list[str])
        Fields exposed to ``?search=``.
    ordering_fields (list[str] | str)
        Fields exposed to ``?ordering=``.  Default: ``'__all__'``.
    ordering (tuple[str, ...])
        Default queryset ordering, e.g. ``('-hire_date',)``.  Also used
        by ``HybridPagination`` as the cursor column.
    pagination_class
        Explicit pagination class.  When omitted, auto-detected by row
        count (see *Pagination auto-detection* below).
    select_related (list[str])
        FK/OneToOne field names to join eagerly in ``get_queryset``,
        preventing N+1 queries on related records.
    permission_classes (list)
        Default: ``[AllowAny]``.

    Pagination auto-detection
    -------------------------
    When a subclass does **not** define ``pagination_class``,
    ``BaseModelViewSet`` counts the table rows (result cached for 5
    minutes) and picks:

    - rows > ``CURSOR_THRESHOLD`` → ``HybridPagination`` (cursor-based,
      with optional ``?page=<N>`` jump support)
    - rows ≤ ``CURSOR_THRESHOLD`` → ``StandardPagination`` (offset-based,
      includes ``count`` and ``last_page`` in the response)

    Usage example
    -------------
    ::

        class EmployeeViewSet(BaseModelViewSet):
            model            = Employees
            serializer_class = EmployeesSerializer
            filterset_class  = EmployeeFilter
            search_fields    = ['first_name', 'last_name']
            ordering         = ('-hire_date',)
    """

    # ── configure in subclass ──────────────────────────────────────────
    model:              Optional[type[Model]] = None
    db_name:            str                   = 'default'
    filterset_class                           = None
    permission_classes: list                  = [AllowAny]
    select_related:     list[str]             = []

    # ── filter / search / ordering ─────────────────────────────────────
    filter_backends:  list  = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields:    list  = []
    ordering_fields         = '__all__'
    ordering:         None  = None

    # ── pagination auto-detection ──────────────────────────────────────
    CURSOR_THRESHOLD: int = 10_000   # rows; above this → HybridPagination
    _CACHE_TTL:       int = 300      # seconds the cached row count stays valid

    # Shared across all instances; keyed by model label to avoid redundant COUNT(*).
    _count_cache: dict[str, tuple[int, float]] = {}

    # ── pagination helpers ─────────────────────────────────────────────

    def _resolve_pagination_class(
        self,
    ) -> type[PageNumberPagination] | type[CursorPagination]:
        """
        Return the pagination class to use for this request.

        Resolution order:
        1. If the subclass explicitly defines ``pagination_class`` in its
           own ``__dict__``, that value is returned as-is.
        2. Otherwise, the table row count is fetched (or read from a
           5-minute cache) and compared against ``CURSOR_THRESHOLD``:
           - count > threshold  → ``HybridPagination``
           - count ≤ threshold  → ``StandardPagination``

        Returns
        -------
        type[PageNumberPagination] | type[CursorPagination]
            The pagination class (not an instance).
        """
        if 'pagination_class' in type(self).__dict__:
            return type(self).__dict__['pagination_class']

        model: Optional[type[Model]] = (
            self.model
            or (self.queryset.model if self.queryset is not None else None)
        )
        if model is None:
            return StandardPagination

        label: str        = model._meta.label
        now:   float      = time.monotonic()
        cached: Optional[tuple[int, float]] = self._count_cache.get(label)

        if cached is None or (now - cached[1]) > self._CACHE_TTL:
            count: int = model.objects.count()
            BaseModelViewSet._count_cache[label] = (count, now)
        else:
            count = cached[0]

        return HybridPagination if count > self.CURSOR_THRESHOLD else StandardPagination

    @property
    def paginator(self) -> Optional[PageNumberPagination | CursorPagination]:
        """
        Return a cached pagination instance for the current request.

        The instance is created once per viewset invocation by calling
        ``_resolve_pagination_class`` and is stored on ``self._paginator``
        to satisfy DRF's internal contract.

        Returns
        -------
        PageNumberPagination | CursorPagination | None
            A pagination instance, or ``None`` if pagination is disabled.
        """
        if not hasattr(self, '_paginator'):
            pagination_cls = self._resolve_pagination_class()
            self._paginator = pagination_cls() if pagination_cls else None
        return self._paginator

    # ── queryset ───────────────────────────────────────────────────────

    def get_queryset(self) -> QuerySet:
        """
        Build the base queryset for every action.

        Applies, in order:
        1. ``self.queryset`` if defined, otherwise ``model.objects.all()``.
        2. ``.using(db_name)`` if ``db_name`` is not ``'default'``.
        3. ``.select_related(*select_related)`` if the list is non-empty.
        4. ``.order_by(*ordering)`` if ``ordering`` is defined.

        Returns
        -------
        QuerySet
            The fully-configured queryset ready for filtering and
            pagination.
        """
        if self.queryset is not None:
            qs: QuerySet = self.queryset
        else:
            assert self.model is not None, (
                f"'{self.__class__.__name__}' must define `model` or `queryset`."
            )
            qs = self.model.objects.all()

        if self.db_name and self.db_name != 'default':
            qs = qs.using(self.db_name)

        if self.select_related:
            qs = qs.select_related(*self.select_related)

        if self.ordering:
            qs = qs.order_by(*self.ordering)

        return qs

    # ── CRUD ────────────────────────────────────────────────────────────

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Return a paginated list of records.

        Applies all active filter backends before paginating.

        Parameters
        ----------
        request:
            The current HTTP request; query parameters drive filtering,
            ordering, searching, and pagination.

        Returns
        -------
        Response
            Paginated response if a paginator is configured, otherwise a
            plain list of all matching records.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Return a single record by its primary key.

        Parameters
        ----------
        request:
            The current HTTP request.

        Returns
        -------
        Response
            Serialized representation of the requested instance.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Create a new record from the request body.

        Parameters
        ----------
        request:
            The current HTTP request; ``request.data`` is validated and
            saved.

        Returns
        -------
        Response
            Serialized representation of the created instance with HTTP
            201 Created.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Fully replace an existing record (PUT).

        Parameters
        ----------
        request:
            The current HTTP request; ``request.data`` must include all
            required fields.

        Returns
        -------
        Response
            Serialized representation of the updated instance.
        """
        partial: bool = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Partially update an existing record (PATCH).

        Delegates to ``update`` with ``partial=True`` so only provided
        fields are validated and changed.

        Parameters
        ----------
        request:
            The current HTTP request; only the fields to change are
            required.

        Returns
        -------
        Response
            Serialized representation of the updated instance.
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Delete an existing record.

        Parameters
        ----------
        request:
            The current HTTP request.

        Returns
        -------
        Response
            HTTP 204 No Content on success.
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
