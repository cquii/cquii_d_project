import django_filters
from utils.filters import BaseFilterSet
from .models import Departments, DeptEmp, DeptManager, Employees, Salaries, Titles


class EmployeeFilter(BaseFilterSet):
    """
    Filter for /employees/

    Query params:
        ?first_name__icontains=ali
        ?last_name__icontains=smith
        ?gender=M
        ?hire_date__gte=1990-01-01&hire_date__lte=2000-12-31
        ?birth_date__gte=1960-01-01
    """
    first_name  = django_filters.CharFilter(lookup_expr='icontains')
    last_name   = django_filters.CharFilter(lookup_expr='icontains')
    hire_after  = django_filters.DateFilter(field_name='hire_date',  lookup_expr='gte')
    hire_before = django_filters.DateFilter(field_name='hire_date',  lookup_expr='lte')
    born_after  = django_filters.DateFilter(field_name='birth_date', lookup_expr='gte')
    born_before = django_filters.DateFilter(field_name='birth_date', lookup_expr='lte')

    class Meta:
        model  = Employees
        fields = ['gender']


class DepartmentFilter(BaseFilterSet):
    """
    Filter for /departments/

    Query params:
        ?dept_name__icontains=sales
        ?dept_no=d001
    """
    dept_name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model  = Departments
        fields = ['dept_no']


class DeptEmpFilter(BaseFilterSet):
    """
    Filter for /dept-emp/

    Query params:
        ?dept_no=d005
        ?emp_no=10001
        ?from_date__gte=1990-01-01
        ?to_date__lte=2000-01-01
    """
    from_after  = django_filters.DateFilter(field_name='from_date', lookup_expr='gte')
    from_before = django_filters.DateFilter(field_name='from_date', lookup_expr='lte')
    to_after    = django_filters.DateFilter(field_name='to_date',   lookup_expr='gte')
    to_before   = django_filters.DateFilter(field_name='to_date',   lookup_expr='lte')

    class Meta:
        model  = DeptEmp
        fields = ['emp_no', 'dept_no']


class DeptManagerFilter(BaseFilterSet):
    """
    Filter for /dept-manager/

    Query params:
        ?dept_no=d005
        ?emp_no=10001
        ?from_date__gte=1990-01-01
    """
    from_after  = django_filters.DateFilter(field_name='from_date', lookup_expr='gte')
    from_before = django_filters.DateFilter(field_name='from_date', lookup_expr='lte')
    to_after    = django_filters.DateFilter(field_name='to_date',   lookup_expr='gte')
    to_before   = django_filters.DateFilter(field_name='to_date',   lookup_expr='lte')

    class Meta:
        model  = DeptManager
        fields = ['emp_no', 'dept_no']


class SalaryFilter(BaseFilterSet):
    """
    Filter for /salaries/

    Query params:
        ?emp_no=10001
        ?salary__gte=60000&salary__lte=100000
        ?from_date__gte=1995-01-01
    """
    salary_min  = django_filters.NumberFilter(field_name='salary',    lookup_expr='gte')
    salary_max  = django_filters.NumberFilter(field_name='salary',    lookup_expr='lte')
    from_after  = django_filters.DateFilter(field_name='from_date',   lookup_expr='gte')
    from_before = django_filters.DateFilter(field_name='from_date',   lookup_expr='lte')
    to_after    = django_filters.DateFilter(field_name='to_date',     lookup_expr='gte')
    to_before   = django_filters.DateFilter(field_name='to_date',     lookup_expr='lte')

    class Meta:
        model  = Salaries
        fields = ['emp_no']


class TitleFilter(BaseFilterSet):
    """
    Filter for /titles/

    Query params:
        ?emp_no=10001
        ?title__icontains=engineer
        ?from_date__gte=1995-01-01
    """
    title       = django_filters.CharFilter(lookup_expr='icontains')
    from_after  = django_filters.DateFilter(field_name='from_date', lookup_expr='gte')
    from_before = django_filters.DateFilter(field_name='from_date', lookup_expr='lte')
    to_after    = django_filters.DateFilter(field_name='to_date',   lookup_expr='gte')
    to_before   = django_filters.DateFilter(field_name='to_date',   lookup_expr='lte')

    class Meta:
        model  = Titles
        fields = ['emp_no']
