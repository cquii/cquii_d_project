from rest_framework.serializers import ModelSerializer
from .models import Departments, DeptEmp, DeptManager, Employees, Salaries, Titles


class DepartmentsSerializer(ModelSerializer):
    class Meta:
        model = Departments
        fields = '__all__'

class DeptEmpSerializer(ModelSerializer):
    class Meta:
        model = DeptEmp
        fields = '__all__'

class DeptManagerSerializer(ModelSerializer):
    class Meta:
        model = DeptManager
        fields = '__all__'

class EmployeesSerializer(ModelSerializer):
    class Meta:
        model = Employees
        fields = '__all__'

class SalariesSerializer(ModelSerializer):
    class Meta:
        model = Salaries
        fields = '__all__'

class TitlesSerializer(ModelSerializer):
    class Meta:
        model = Titles
        fields = '__all__'