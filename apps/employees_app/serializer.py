from rest_framework import serializers
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


class EmployeeSummarySerializer(ModelSerializer):
    salary     = serializers.SerializerMethodField()
    title      = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()

    class Meta:
        model  = Employees
        fields = ['emp_no', 'first_name', 'last_name', 'gender', 'birth_date', 'hire_date', 'salary', 'title', 'department']

    def get_salary(self, obj):
        return [
            {'amount': s.salary, 'from_date': s.from_date, 'to_date': s.to_date}
            for s in getattr(obj, 'all_salaries', [])
        ]

    def get_title(self, obj):
        records = getattr(obj, 'current_titles', [])
        if not records:
            return None
        t = records[0]
        return {'name': t.title, 'from_date': t.from_date}

    def get_department(self, obj):
        return [
            {'dept_no': de.dept_no.dept_no, 'dept_name': de.dept_no.dept_name, 'from_date': de.from_date, 'to_date': de.to_date}
            for de in getattr(obj, 'all_depts', [])
        ]