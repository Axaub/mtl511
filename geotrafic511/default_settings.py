"""
Django settings for geotrafic511 project.

Generated by 'django-admin startproject' using Django 1.9c1.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = False

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'geotrafic511',
    'open511_server',
    'django_open511_ui'
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'geotrafic511.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'geotrafic511.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = 'fr'

TIME_ZONE = 'America/Montreal'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'collected_static')

OPEN511_UI_APP_SETTINGS = {
    'areas': [
        ('geonames.org/5882726', 'Ahuntsic-Cartierville'),
        ('geonames.org/5885369', 'Anjou'),
        ('geonames.org/5928430', 'Côte-des-Neiges–Notre-Dame-de-Grâce'),
        ('geonames.org/6053852', "L'Île-Bizard–Sainte-Geneviève"),
        ('geonames.org/6945990', 'LaSalle'),
        ('geonames.org/6545041', 'Lachine'),
        ('geonames.org/6052594', 'Le Plateau-Mont-Royal'),
        ('geonames.org/6053102', 'Le Sud-Ouest'),
        ('geonames.org/6072211', 'Mercier–Hochelaga-Maisonneuve'),
        ('geonames.org/6077254', 'Montréal-Nord'),
        ('geonames.org/6095438', 'Outremont'),
        ('geonames.org/6104320', 'Pierrefonds-Roxboro'),
        ('geonames.org/6123696', 'Rivière-des-Prairies–Pointe-aux-Trembles'),
        ('geonames.org/6127689', 'Rosemont–La Petite-Patrie'),
        ('geonames.org/6138610', 'Saint-Laurent'),
        ('geonames.org/6138625', 'Saint-Léonard'),
        ('geonames.org/6173767', 'Verdun'),
        ('geonames.org/6174337', 'Ville-Marie'),
        ('geonames.org/6174349', 'Villeray–Saint-Michel–Parc-Extension')
    ]
}
