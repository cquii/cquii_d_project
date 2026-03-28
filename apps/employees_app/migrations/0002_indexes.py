from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('employees_app', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "CREATE INDEX idx_dept_emp_from_date ON dept_emp(from_date);",
                "CREATE INDEX idx_dept_emp_emp_no    ON dept_emp(emp_no);",
                "CREATE INDEX idx_dept_emp_dept_no   ON dept_emp(dept_no);",
            ],
            reverse_sql=[
                "DROP INDEX idx_dept_emp_from_date ON dept_emp;",
                "DROP INDEX idx_dept_emp_emp_no    ON dept_emp;",
                "DROP INDEX idx_dept_emp_dept_no   ON dept_emp;",
            ],
        ),
    ]
