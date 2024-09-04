from .base import *
import environ

ALLOWED_HOSTS = ['43.202.173.40']
STATIC_ROOT = BASE_DIR / 'static/'
STATICFILES_DIRS = []
DEBUG = False

env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'pybo',
        'USER': 'dbmasteruser',
        'PASSWORD':'Y,f#D5Wfp&m*R8gb(,EMAc[SzWM6+j2D' ,
        'HOST': 'ls-b526c35546c4c984afa0256466afad5d7698ceda.cbg28k60wken.ap-northeast-2.rds.amazonaws.com',
        'PORT': '5432',
    }
}
