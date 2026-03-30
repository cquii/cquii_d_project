import django_filters
from django.db.models import Q
from django.db.models import CharField, TextField
from django.db.models.fields.related import ForeignKey, OneToOneField
from django_filters import rest_framework as filters


class BaseFilterSet(filters.FilterSet):
    """
    Reusable base FilterSet — extend this for every app's filters.

    Provides a standard foundation with helper methods for building
    common filter patterns consistently across endpoints.

    ── Built-in filters ───────────────────────────────────────────────────
    search      ?search=value
                Case-insensitive substring match across all text fields
                on the model and one level deep through FK / O2O relations.
                Searches related text (e.g. dept_name via dept_no FK),
                never raw ID columns.

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

    search = django_filters.CharFilter(method='filter_search', label='Search')

    def _search_lookups(self) -> list[str]:
        """
        Collect icontains lookup paths for every text field on the model
        and one level deep through ForeignKey / OneToOneField relations.

        Primary-key fields are excluded — they are ID columns, not
        human-readable text.  Only CharField and TextField are included.
        """
        lookups: list[str] = []
        for field in self._meta.model._meta.fields:
            if isinstance(field, (CharField, TextField)) and not field.primary_key:
                lookups.append(f'{field.name}__icontains')
            elif isinstance(field, (ForeignKey, OneToOneField)):
                for related_field in field.related_model._meta.fields:
                    if isinstance(related_field, (CharField, TextField)) and not related_field.primary_key:
                        lookups.append(f'{field.name}__{related_field.name}__icontains')
        return lookups

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        lookups = self._search_lookups()
        if not lookups:
            return queryset
        for word in value.split():
            word_query = Q()
            for lookup in lookups:
                word_query |= Q(**{lookup: word})
            queryset = queryset.filter(word_query)
        return queryset.distinct()

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
