import django_filters
from django_filters import rest_framework as filters


class BaseFilterSet(filters.FilterSet):
    """
    Reusable base FilterSet — extend this for every app's filters.

    Provides a standard foundation with helper methods for building
    common filter patterns consistently across endpoints.

    ── Usage ─────────────────────────────────────────────────────────────
    class EmployeeFilter(BaseFilterSet):
        class Meta:
            model  = Employees
            fields = {
                'first_name': ['exact', 'icontains'],
                'last_name':  ['exact', 'icontains'],
                'gender':     ['exact'],
                'hire_date':  ['exact', 'gte', 'lte'],
            }

    ── Common lookup expressions ──────────────────────────────────────────
    exact       ?field=value
    icontains   ?field__icontains=value   (case-insensitive substring)
    gte / lte   ?field__gte=value         (range filtering)
    in          ?field__in=a,b,c          (multiple values)
    isnull      ?field__isnull=true       (null check)
    """

    class Meta:
        # Subclasses must define model and fields
        abstract = True

    # ──────────────────────────────────────────────────────────────────
    # Helper: range filter pair (gte + lte) returned as a dict ready to
    # merge into a FilterSet's declared fields via extra_filters().
    # ──────────────────────────────────────────────────────────────────

    @classmethod
    def range_filters(cls, field_name, lookup_prefix=''):
        """
        Return a dict of two RangeFilter-style char filters for a field.
        Use when you need manual range declarations outside of Meta.fields.

        Example (in FilterSet body):
            salary_min = django_filters.NumberFilter(field_name='salary', lookup_expr='gte')
            salary_max = django_filters.NumberFilter(field_name='salary', lookup_expr='lte')
        """
        prefix = lookup_prefix or field_name
        return {
            f'{prefix}_min': django_filters.NumberFilter(
                field_name=field_name, lookup_expr='gte'
            ),
            f'{prefix}_max': django_filters.NumberFilter(
                field_name=field_name, lookup_expr='lte'
            ),
        }

    @classmethod
    def date_range_filters(cls, field_name, lookup_prefix=''):
        """
        Return a dict of two DateFilter declarations for date range filtering.

        Example (in FilterSet body):
            hire_after  = django_filters.DateFilter(field_name='hire_date', lookup_expr='gte')
            hire_before = django_filters.DateFilter(field_name='hire_date', lookup_expr='lte')
        """
        prefix = lookup_prefix or field_name
        return {
            f'{prefix}_after': django_filters.DateFilter(
                field_name=field_name, lookup_expr='gte'
            ),
            f'{prefix}_before': django_filters.DateFilter(
                field_name=field_name, lookup_expr='lte'
            ),
        }
