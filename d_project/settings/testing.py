from .base import *

DEBUG = False

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
    'employees': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

DATABASE_ROUTERS = ['utils.db_router.EmployeesRouter']

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {},
    'loggers': {},
}
