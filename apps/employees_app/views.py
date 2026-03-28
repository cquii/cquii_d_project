from utils.cls_views import BaseModelViewSet

from .models import Departments, DeptEmp, DeptManager, Employees, Salaries, Titles
from .serializer import (
    DepartmentsSerializer, DeptEmpSerializer, DeptManagerSerializer,
    EmployeesSerializer, SalariesSerializer, TitlesSerializer,
)
from .filters import (
    DepartmentFilter, DeptEmpFilter, DeptManagerFilter,
    EmployeeFilter, SalaryFilter, TitleFilter,
)


class EmployeeViewSet(BaseModelViewSet):
    model            = Employees
    serializer_class = EmployeesSerializer
    filterset_class  = EmployeeFilter
    search_fields    = []
    ordering_fields  = '__all__'
    ordering         = ('emp_no',)


class DepartmentViewSet(BaseModelViewSet):
    model            = Departments
    serializer_class = DepartmentsSerializer
    filterset_class  = DepartmentFilter
    search_fields    = ['dept_name']
    ordering_fields  = ['dept_no', 'dept_name']
    ordering         = ('dept_no',)


class DeptEmpViewSet(BaseModelViewSet):
    model            = DeptEmp
    serializer_class = DeptEmpSerializer
    filterset_class  = DeptEmpFilter
    select_related   = ['emp_no', 'dept_no']
    ordering_fields  = ['from_date', 'to_date']
    ordering         = ('from_date',)


class DeptManagerViewSet(BaseModelViewSet):
    model            = DeptManager
    serializer_class = DeptManagerSerializer
    filterset_class  = DeptManagerFilter
    select_related   = ['emp_no', 'dept_no']
    ordering_fields  = ['from_date', 'to_date']
    ordering         = ('from_date',)


class SalaryViewSet(BaseModelViewSet):
    model            = Salaries
    serializer_class = SalariesSerializer
    filterset_class  = SalaryFilter
    select_related   = ['emp_no']
    ordering_fields  = ['salary', 'from_date', 'to_date']
    ordering         = ('-salary',)


class TitleViewSet(BaseModelViewSet):
    model            = Titles
    serializer_class = TitlesSerializer
    filterset_class  = TitleFilter
    select_related   = ['emp_no']
    search_fields    = ['title']
    ordering_fields  = ['title', 'from_date', 'to_date']
    ordering         = ('title',)
