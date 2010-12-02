# -*- coding: utf-8 -*-
"""
base.views
"""

"""
import logging

from google.appengine.api import users
from google.appengine.api import memcache
from werkzeug import (
  unescape, redirect, Response,
)
from werkzeug.exceptions import (
  NotFound, MethodNotAllowed, BadRequest
)

from kay.utils import (
  render_to_response, reverse,
  get_by_key_name_or_404, get_by_id_or_404,
  to_utc, to_local_timezone, url_for, raise_on_dev
)
from kay.i18n import gettext as _
from kay.auth.decorators import login_required

"""
import logging

from werkzeug.exceptions import BadRequest

from kay.utils import render_to_response, url_for
from kay.conf import settings
from kay.auth.decorators import login_required
from werkzeug import redirect, Response

from gaelibs.facebook_oauth import Facebook
from gaelibs.google_auth import GoogleAuth
from gaelibs.oauth import OAuthError
import urllib

#from facebook_app.models import FacebookUser, Contact



# Create your views here.

def index(request):
    return render_to_response('backup_bridge/index.html', {'message': 'Hello'})

def facebook_authorize(request):
    local_redirect = request.values.get('redirect_url', None)
    if not local_redirect:
        return BadRequest()
    
    request.session['local_redirect'] = local_redirect
    facebook = Facebook(
        settings.FACEBOOK_APP_ID,
        settings.FACEBOOK_APP_SECRET,
        url_for('backup_bridge/facebook_oauth_callback', _external=True))
    print url_for("backup_bridge/facebook_oauth_callback", _external=True)
    scope = [
        'offline_access',
        'user_events', 'friends_events',
        'user_notes', 'friends_notes',
        'user_photos', 'friends_photos',
        'user_status', 'friends_status',
        'user_photo_video_tags', 'friends_photo_video_tags',
        'user_groups', 'friends_groups',
        'user_videos', 'friends_videos',
        'user_about_me', 'friends_about_me',
        'user_activities', 'friends_activities',
        'user_birthday', 'friends_birthday',
        'user_education_history', 'friends_education_history',
        'user_groups', 'friends_groups',
        'user_hometown', 'friends_hometown',
        'user_interests', 'friends_interests',
        'user_likes', 'friends_likes',
        'user_location', 'friends_location',
        'user_relationships', 'friends_relationships',
        'user_relationship_details', 'friends_relationship_details',
        'user_website', 'friends_website',
        'user_work_history', 'friends_work_history',
        'user_checkins', 'friends_checkins'
        ]
    scope = ','.join(scope)
    url = facebook.get_authorization_url(scope)
    return redirect(url)

def facebook_oauth_callback(request):
    return render_to_response("backup_bridge/facebook_oauth_callback.html")

def facebook_register(request):
    access_token = request.values.get("access_token", None)
    local_redirect = request.session['local_redirect']
    del request.session['local_redirect']
    url = "%s?access_token=%s" % (local_redirect, access_token)
    return redirect(url)


def google_app_authorize(request):
    local_redirect = request.values.get('redirect_url', None)
    scope = request.values.get('scope', None)
    if not (local_redirect or scope):
        return BadRequest()

    request.session['local_redirect'] = local_redirect
    #request.session['scope'] = scope

    google_auth = GoogleAuth(settings.GOOGLE_OAUTH_CONSUMER_KEY,
            settings.GOOGLE_OAUTH_CONSUMER_SECRET)
    #scope = "https://www.google.com/m8/feeds/"
    request_token = google_auth.get_request_token(
            parameters={'scope': scope})
    request.session['google_request_token'] = request_token.to_string()
    callback_url = url_for('backup_bridge/google_app_oauth_callback', _external=True)
    url = google_auth.get_authorization_url(request_token,
            callback_url=callback_url)
    return redirect(url)
   
def google_app_oauth_callback(request):
    request_token = GoogleAuth.token_from_string(request.session['google_request_token'])
    del request.session['google_request_token']
    google_auth = GoogleAuth(settings.GOOGLE_OAUTH_CONSUMER_KEY,
            settings.GOOGLE_OAUTH_CONSUMER_SECRET)

    #scope = 'https://www.google.com/m8/feeds/'


    local_redirect = request.session.get('local_redirect', None)
    request.session.pop('local_redirect', None)

    try:
        access_token = google_auth.get_access_token(request_token)
        url = "%s?access_token=%s" % (local_redirect, urllib.quote(access_token.to_string()))
        return redirect(url)
    except:
        url = "%s?access_token=" % (local_redirect,)
        return redirect(url)

