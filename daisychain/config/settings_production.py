from .settings_base import *
from config.keys import keys

SECRET_KEY = keys["DJANGO"]["PRODUCTION"]

DEBUG = False
ALLOWED_HOSTS = [
    'example.com',
    'localhost',
]

# ####### Mail #########
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.example.com'
EMAIL_PORT = '587'
EMAIL_HOST_USER = 'test@example.com'
EMAIL_HOST_PASSWORD = keys['DJANGO']['SMTP']
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'test@example.com'
# #######################

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'daisychain',
        'USER': 'daisychain',
        'PASSWORD': keys['DJANGO']['POSTGRES'],
        'HOST': 'localhost',
        'PORT': '',
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'simple': {
            'format': '[%(asctime)s] %(levelname)s %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s '
                      '[%(name)s.%(funcName)s:%(lineno)d] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'production_logfile': {
            'level': 'DEBUG',
            'filters': ['require_debug_false'],
            'class': 'logging.FileHandler',
            'filename': '/var/log/daisychain/server.log',
            'formatter': 'simple'
        },
        'database_logfile': {
            'level': 'DEBUG',
            'filters': ['require_debug_false', 'require_debug_true'],
            'class': 'logging.FileHandler',
            'filename': '/var/log/daisychain/database.log',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'channel': {
            'handlers': ['console', 'production_logfile'],
            'level': 'DEBUG'
         },
        'database': {
            'handlers': ['console', 'database_logfile'],
            'level': 'INFO'
        },
        'django': {
            'handlers': ['console', 'production_logfile'],
        },
        'py.warnings': {
            'handlers': ['console', 'production_logfile'],
        },
    }
}
