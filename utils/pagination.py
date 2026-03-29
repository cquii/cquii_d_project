import math
from base64 import b64encode
from typing import Optional
from urllib import parse

from django.db.models import QuerySet
from rest_framework.pagination import CursorPagination, PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.utils.urls import remove_query_param, replace_query_param
from rest_framework.views import APIView


class BasePagination(PageNumberPagination):
    """
    Shared base for all offset-based pagination classes.

    Extends DRF's PageNumberPagination with a consistent response envelope
    and an exposed ``page_size`` query parameter so clients can control it.

    Response schema
    ---------------
    count      (int)         Total records in the filtered queryset.
    last_page  (int)         Total pages for the current page_size.
    next       (str | null)  URL for the next page.
    previous   (str | null)  URL for the previous page.
    results    (list)        Serialized records for the current page.
    """

    page_size_query_param = 'page_size'

    def get_paginated_response(self, data: list) -> Response:
        """
        Build the standard response envelope with count and last_page.

        Parameters
        ----------
        data:
            Serialized records for the current page.

        Returns
        -------
        Response
            DRF Response containing count, last_page, next, previous, results.
        """
        page_size: int = self.get_page_size(self.request)
        last_page: int = math.ceil(self.page.paginator.count / page_size)
        return Response({
            'count':     self.page.paginator.count,
            'last_page': last_page,
            'next':      self.get_next_link(),
            'previous':  self.get_previous_link(),
            'results':   data,
        })


class SmallPagination(BasePagination):
    """Offset pagination for small reference tables (default 5, max 30 per page)."""

    page_size     = 5
    max_page_size = 30


class StandardPagination(BasePagination):
    """Offset pagination for medium-sized tables (default 50, max 100 per page)."""

    page_size     = 50
    max_page_size = 100


class BigPagination(BasePagination):
    """Offset pagination for large exports or bulk reads (default 250, max 500 per page)."""

    page_size     = 250
    max_page_size = 500


class HybridPagination(CursorPagination):
    """
    Cursor pagination for large tables with optional page-jump support.

    Large tables default to cursor-based navigation, which avoids the
    ``LIMIT … OFFSET N`` cost that grows with N.  When a client needs to
    jump to an arbitrary page (e.g. page 50), it can pass ``?page=<N>``
    and the paginator performs a single OFFSET query for that jump, then
    encodes the last item's position as a cursor token — so every
    subsequent ``next`` / ``previous`` request is still cursor-based.

    Request modes (mutually exclusive)
    ------------------------------------
    Default / ``?cursor=<token>``
        Pure cursor navigation.  No OFFSET cost.  Use for sequential
        browsing (next / previous).
    ``?page=<N>``
        OFFSET jump to any page.  ``next`` and ``previous`` in the
        response carry cursor tokens, so the client can continue with
        pure-cursor navigation from that point onward.

    Priority rule
    -------------
    If both ``?cursor`` and ``?page`` appear in the same request, cursor
    mode wins and ``?page`` is ignored.

    Response schema (same shape as BasePagination)
    -----------------------------------------------
    count      (null)        Always null — cursor pagination cannot
                             compute a total count cheaply.
    last_page  (null)        Always null — same reason.
    next       (str | null)  Cursor URL for the next page.
    previous   (str | null)  Cursor URL for the previous page.
    results    (list)        Serialized records for the current page.
    """

    page_size_query_param = 'page_size'
    page_size             = 50
    max_page_size         = 500

    # ── ordering helpers ──────────────────────────────────────────────────

    def _fallback_ordering(self, queryset: QuerySet) -> tuple[str, ...]:
        """
        Derive a safe default ordering from the model's primary key.

        Used when the viewset does not define an explicit ``ordering``
        attribute, ensuring cursor pagination always has a stable sort.

        For composite primary keys (Django's ``CompositePrimaryKey``) the
        first declared field is used, since cursor pagination requires a
        single-column comparison.

        Parameters
        ----------
        queryset:
            The queryset being paginated; used only to read model metadata.

        Returns
        -------
        tuple[str, ...]
            A one-element tuple with the ordering field name, ready to be
            passed to ``QuerySet.order_by(*ordering)``.
        """
        pk = queryset.model._meta.pk
        if pk is None:
            return ('pk',)
        if hasattr(pk, 'fields'):   # CompositePrimaryKey
            return (pk.fields[0],)
        return (pk.attname,)

    # ── core entry point ─────────────────────────────────────────────────

    def paginate_queryset(
        self,
        queryset: QuerySet,
        request: Request,
        view: Optional[APIView] = None,
    ) -> Optional[list]:
        """
        Paginate the queryset, choosing cursor or page-jump mode.

        Ordering is resolved in this priority order:
        1. ``view.ordering`` if the viewset defines it.
        2. The model's primary key via ``_fallback_ordering``.

        Parameters
        ----------
        queryset:
            The filtered queryset to paginate.
        request:
            The current HTTP request.
        view:
            The calling viewset instance (used to read ``ordering``).

        Returns
        -------
        list | None
            The page of model instances, or ``None`` if pagination is
            disabled.
        """
        if view is not None and getattr(view, 'ordering', None):
            self.ordering = view.ordering
        elif not getattr(self, 'ordering', None):
            self.ordering = self._fallback_ordering(queryset)

        self.request    = request
        self._page_mode = False

        has_page   = 'page'                  in request.query_params
        has_cursor = self.cursor_query_param  in request.query_params

        if has_page and not has_cursor:
            return self._paginate_by_page(queryset, request)

        return super().paginate_queryset(queryset, request, view)

    # ── page-jump mode ────────────────────────────────────────────────────

    def _paginate_by_page(self, queryset: QuerySet, request: Request) -> list:
        """
        Perform a single OFFSET query to jump to the requested page.

        After fetching the page, the first and last items are stored so
        that ``get_paginated_response`` can encode cursor tokens from them.

        Parameters
        ----------
        queryset:
            The filtered queryset; ordering is applied inside this method.
        request:
            The current HTTP request; used to read ``page`` and
            ``page_size`` query parameters.

        Returns
        -------
        list
            Model instances for the requested page.
        """
        try:
            page_number: int = max(1, int(request.query_params['page']))
        except (ValueError, TypeError):
            page_number = 1

        page_size: int = self.get_page_size(request)
        offset: int    = (page_number - 1) * page_size
        results: list  = list(queryset.order_by(*self.ordering)[offset:offset + page_size])

        self._page_mode    = True
        self._current_page = page_number
        self._page_results = results
        return results

    def _cursor_url(self, item: object, reverse: bool) -> str:
        """
        Encode a cursor token from a model instance and return a full URL.

        The cursor encodes the value of the first ordering field so that
        subsequent cursor requests can filter from that position without
        an OFFSET.

        Parameters
        ----------
        item:
            A model instance from the current page; its ordering-field
            value becomes the cursor position.
        reverse:
            ``True`` to generate a *previous* cursor (navigates backward),
            ``False`` for a *next* cursor (navigates forward).

        Returns
        -------
        str
            Absolute URL with the ``cursor`` query parameter set and the
            ``page`` parameter removed.
        """
        field: str    = self.ordering[0].lstrip('-')
        position: str = str(getattr(item, field))
        tokens: dict  = {'p': position}
        if reverse:
            tokens['r'] = '1'

        encoded: str = b64encode(
            parse.urlencode(tokens, doseq=True).encode('ascii')
        ).decode('ascii')

        url: str = remove_query_param(self.request.build_absolute_uri(), 'page')
        return replace_query_param(url, self.cursor_query_param, encoded)

    # ── unified response ──────────────────────────────────────────────────

    def get_paginated_response(self, data: list) -> Response:
        """
        Build the response envelope, producing cursor URLs in both modes.

        In cursor mode the links come from DRF's built-in
        ``get_next_link`` / ``get_previous_link``.  In page-jump mode
        they are encoded from the first and last items of the page via
        ``_cursor_url``, so the client seamlessly transitions to
        cursor-based navigation after the jump.

        Parameters
        ----------
        data:
            Serialized records for the current page.

        Returns
        -------
        Response
            DRF Response with count=null, last_page=null, next, previous,
            and results.
        """
        if self._page_mode:
            results = self._page_results
            next_link: Optional[str] = (
                self._cursor_url(results[-1], reverse=False) if results else None
            )
            prev_link: Optional[str] = (
                self._cursor_url(results[0], reverse=True)
                if results and self._current_page > 1 else None
            )
        else:
            next_link = self.get_next_link()
            prev_link = self.get_previous_link()

        return Response({
            'count':     None,
            'last_page': None,
            'next':      next_link,
            'previous':  prev_link,
            'results':   data,
        })


# Keep old name so any explicit pagination_class = DynamicCursorPagination still works.
DynamicCursorPagination = HybridPagination
