EMPLOYEES_APP_MODELS = {
    'departments', 'deptemp', 'deptmanager', 'employees', 'salaries', 'titles'
}


class EmployeesRouter:
    """
    Routes all employees_app models to the 'employees' MySQL database.
    All other models (auth, sessions, etc.) stay on 'default'.
    """

    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'employees_app':
            return 'employees'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'employees_app':
            return 'employees'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if (
            obj1._meta.app_label == 'employees_app'
            and obj2._meta.app_label == 'employees_app'
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'employees_app':
            return db == 'employees'
        return db == 'default'
