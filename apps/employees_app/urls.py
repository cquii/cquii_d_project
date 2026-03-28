from rest_framework.routers import DefaultRouter
from utils.cls_views import BaseModelViewSet
from .views import (
    DepartmentViewSet, DeptEmpViewSet, DeptManagerViewSet,
    EmployeeViewSet, SalaryViewSet, TitleViewSet,
)

router = DefaultRouter()
# router.register('employees',    EmployeeViewSet,    basename='employees')
# router.register('departments',  DepartmentViewSet,  basename='departments')
# router.register('dept-emp',     DeptEmpViewSet,     basename='dept-emp')
# router.register('dept-manager', DeptManagerViewSet, basename='dept-manager')
# router.register('salaries',     SalaryViewSet,      basename='salaries')
# router.register('titles',       TitleViewSet,       basename='titles')

def register_routes(routes: list[tuple[str, type[BaseModelViewSet]]]) -> list:
    """
    Registra un conjunto de ViewSets en el router y retorna los URL patterns.

    Args:
        routes: Lista de tuplas (prefix, viewset) donde:
                - prefix:  segmento de URL (ej. 'employees')
                - viewset: clase ViewSet asociada al recurso

    Returns:
        Lista de URL patterns generados por el router.
    """
    for prefix, ViewSet in routes:
        router.register(prefix, ViewSet, basename=prefix)
    return router.urls


urlpatterns = register_routes(
    [
        ("employees",    EmployeeViewSet),
        ("departments",  DepartmentViewSet),
        ("dept-emp",     DeptEmpViewSet),
        ("dept-manager", DeptManagerViewSet),
        ("salaries",     SalaryViewSet),
        ("titles",       TitleViewSet),
    ]
)
