import time

from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from utils.pagination import DynamicCursorPagination, StandardPagination


class BaseModelViewSet(ModelViewSet):
    """
    Reusable base ViewSet — configure once, use everywhere.

    Every endpoint that extends this class gets full CRUD, filtering,
    search, ordering, and pagination for free.

    ── Required ──────────────────────────────────────────────────────────
    model (Model)               Django model class
    serializer_class            DRF serializer

    ── Optional ──────────────────────────────────────────────────────────
    db_name        (str)        DB alias for .using(). Default: 'default'
    filterset_class             django-filter FilterSet class
    search_fields  (list)       Fields exposed to ?search=
    ordering_fields(list|str)   Fields exposed to ?ordering=  Default: '__all__'
    ordering       (tuple)      Default queryset ordering, e.g. ('-hire_date',)
    pagination_class            Auto-detected by row count if not set explicitly.
    permission_classes (list)   Default: [AllowAny]

    ── Pagination auto-detection ──────────────────────────────────────────
    If the subclass does NOT define pagination_class, BaseModelViewSet
    counts the table rows (cached 5 min) and picks:
      - rows > CURSOR_THRESHOLD  →  DynamicCursorPagination
      - rows ≤ CURSOR_THRESHOLD  →  StandardPagination

    ── Usage ─────────────────────────────────────────────────────────────
    class EmployeeViewSet(BaseModelViewSet):
        model            = Employees
        serializer_class = EmployeesSerializer
        db_name          = 'employees'
        filterset_class  = EmployeeFilter
        search_fields    = ['first_name', 'last_name']
        ordering         = ('-hire_date',)
    """

    # ── configure in subclass ──────────────────────────────────────────
    model              = None
    db_name            = 'default'
    filterset_class    = None
    permission_classes = [AllowAny]
    select_related     = []   # e.g. ['emp_no', 'dept_no']

    # ── filter / search / ordering ─────────────────────────────────────
    filter_backends  = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields    = []
    ordering_fields  = '__all__'
    ordering         = None

    # ── pagination auto-detection ──────────────────────────────────────
    CURSOR_THRESHOLD = 10_000          # filas; por encima → cursor
    _CACHE_TTL       = 300             # segundos que dura el count cacheado
    _count_cache: dict[str, tuple[int, float]] = {}  # {model_label: (count, ts)}

    def _resolve_pagination_class(self):
        """
        Devuelve la clase de paginación a usar:
        - Si el subclass la define explícitamente → la respeta.
        - Si no → cuenta las filas (con caché) y elige cursor o page.
        """
        if 'pagination_class' in type(self).__dict__:
            return type(self).__dict__['pagination_class']

        model = self.model or (self.queryset.model if self.queryset is not None else None)
        if model is None:
            return StandardPagination

        label = model._meta.label
        now   = time.monotonic()
        cached = self._count_cache.get(label)

        if cached is None or (now - cached[1]) > self._CACHE_TTL:
            count = model.objects.count()
            BaseModelViewSet._count_cache[label] = (count, now)
        else:
            count = cached[0]

        return DynamicCursorPagination if count > self.CURSOR_THRESHOLD else StandardPagination

    @property
    def paginator(self):
        if not hasattr(self, '_paginator'):
            pagination_cls = self._resolve_pagination_class()
            self._paginator = pagination_cls() if pagination_cls else None
        return self._paginator

    # ──────────────────────────────────────────────────────────────────
    # Queryset
    # ──────────────────────────────────────────────────────────────────

    def get_queryset(self):
        # Allow subclasses to set queryset directly; apply db routing on top
        if self.queryset is not None:
            qs = self.queryset
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

    # ──────────────────────────────────────────────────────────────────
    # CRUD
    # ──────────────────────────────────────────────────────────────────

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
