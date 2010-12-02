# -*- coding: utf-8 -*-

"""
A sample of kay settings.

:Copyright: (c) 2009 Accense Technology, Inc. 
                     Takashi Matsuo <tmatsuo@candit.jp>,
                     All rights reserved.
:license: BSD, see LICENSE for more details.
"""
APP_NAME = 'MyCube'
DEFAULT_TIMEZONE = 'Asia/Singapore'
DEBUG = False
PROFILE = False
SECRET_KEY = 'mycubesupersecretstringimpossibletoguessiJuHyG3(jiwn(01'
SESSION_PREFIX = 'gaesess:'
COOKIE_AGE = 1209600 # 2 weeks
COOKIE_NAME = 'KAY_SESSION'

ADD_APP_PREFIX_TO_KIND = True

ADMINS = (
)

TEMPLATE_DIRS = (
    'templates',
)
DEFAULT_MAIL_FROM = 'no-reply@mycube.com'

USE_I18N = False
DEFAULT_LANG = 'en'

INSTALLED_APPS = (
    'kay.sessions',
    'kay.auth',
    'core',
    'kay.ext.nuke',
    'backup_bridge',
    'vault',
)

APP_MOUNT_POINTS = {
    'core': '/',
}

# You can remove following settings if unnecessary.
CONTEXT_PROCESSORS = (
    'kay.context_processors.request',
    'kay.context_processors.url_functions',
    'kay.context_processors.media_url',
)

MIDDLEWARE_CLASSES = (
    'kay.sessions.middleware.SessionMiddleware',
    'kay.auth.middleware.AuthenticationMiddleware',
)

AUTH_USER_BACKEND = 'kay.auth.backends.googleaccount.GoogleBackend'
AUTH_USER_MODEL = 'kay.auth.models.GoogleUser'

FACEBOOK_APP_ID = '147092398634581'
FACEBOOK_APP_SECRET = '69ff7b3fb2494beb19bb46bf34675831'

GOOGLE_OAUTH_CONSUMER_KEY = "opensocialgraph.appspot.com"
GOOGLE_OAUTH_CONSUMER_SECRET = "ZwKQP4ILJ5G6witkPvCz7Jzx"

GOOGLE_TEST_OAUTH_TOKEN_KEY = "<token_key>"
GOOGLE_TEST_OAUTH_TOKEN_SECRET = "<token_secret>"

