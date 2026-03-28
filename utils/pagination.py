import math
from rest_framework.pagination import PageNumberPagination, CursorPagination
from rest_framework.response import Response


class BasePagination(PageNumberPagination):
    page_size_query_param = 'page_size'

    def get_paginated_response(self, data):
        page_size = self.get_page_size(self.request)
        last_page = math.ceil(self.page.paginator.count / page_size)
        return Response({
            'count':     self.page.paginator.count,
            'last_page': last_page,
            'next':      self.get_next_link(),
            'previous':  self.get_previous_link(),
            'results':   data,
        })


class SmallPagination(BasePagination):
    page_size = 5
    max_page_size = 30


class StandardPagination(BasePagination):
    page_size = 50
    max_page_size = 100


class BigPagination(BasePagination):
    page_size = 250
    max_page_size = 500


class DynamicCursorPagination(CursorPagination):
    """
    Toma el ordering del viewset automáticamente.
    Si el viewset define ordering = ('from_date',), el cursor usa 'from_date'.
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500

    def paginate_queryset(self, queryset, request, view=None):
        if view is not None and getattr(view, 'ordering', None):
            self.ordering = view.ordering
        return super().paginate_queryset(queryset, request, view)
