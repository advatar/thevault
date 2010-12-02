# -*- coding: utf-8 -*-
"""
core.views
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
import urllib

from werkzeug import (
  unescape, redirect, Response,
)

from werkzeug.exceptions import (
  NotFound, MethodNotAllowed, BadRequest, Unauthorized,
  InternalServerError,
)

from kay.utils import render_to_response, url_for, get_by_id_or_404
from kay.auth.decorators import login_required, admin_required

from core.models import ConsumerApp, OAuthDataStore, RequestToken, User
from core.forms import ConsumerAppForm
from core.decorators import oauth_protect
from gaelibs.decorators import restrict_to_methods

from gaelibs.oauth import (
    OAuthRequest, OAuthServer, OAuthToken,
    OAuthSignatureMethod_PLAINTEXT,
    OAuthSignatureMethod_HMAC_SHA1,
    OAuthError
)

import logging
# Create your views here.

# some weirdness. need to import module if associations will use it
# e.g. request.user.twitteruser_set.get() will fail with importing
# TwitterUser
#from twitter_app.models import TwitterUser
#from facebook_app.models import FacebookUser
#from myspace_app.models import MyspaceUser

def index(request):
    template = "core/index.html"
    if not request.user.is_anonymous():
        template = "core/logged_in-index.html"

    return render_to_response(template)
    
@login_required  
def developer_register(request):
    """
    Gives user a way to create app that access other user's
    protected resource using OAuth.
    """
    form = ConsumerAppForm()
    return render_to_response('core/developer/register.html', {'form': form.as_widget()})

@restrict_to_methods("POST")
@login_required
def developer_do_register(request):
    """
    Process the app registration form.
    """
    form = ConsumerAppForm()
    if form.validate(request.form):
        token = OAuthDataStore.generate_tokens()
        consumer = form.save(user=request.user,
                consumer_key=token.key,
                consumer_secret=token.secret)
        return redirect(url_for('core/developer/app', app_id=consumer.key().id()))
            
    return render_to_response('core/developer/register.html', {'form': form.as_widget()})
    

@login_required
def developer_app(request, app_id):
    """
    Display the Application name, callback_url, consumer_key and consumer_secret
    to the developer.
    """
    app = get_by_id_or_404(ConsumerApp, app_id)
    if app.user != request.user:
        raise NotFound
    return render_to_response('core/developer/app.html', {'app': app})

@login_required
def developer_apps(request):
    """
    Display the list of apps this user has created.
    """
    apps = ConsumerApp.all().filter('user =', request.user.key())
    return render_to_response("core/developer/apps.html", {'apps': apps})
    
def initialize_oauth(request):
    oauth_request = OAuthRequest.from_request(request.method, request.url,
            headers=request.headers,
            query_string=urllib.urlencode(request.values))
    oauth_server = OAuthServer(OAuthDataStore())
    oauth_server.add_signature_method(OAuthSignatureMethod_PLAINTEXT())
    oauth_server.add_signature_method(OAuthSignatureMethod_HMAC_SHA1())
    return [oauth_request, oauth_server]


def oauth_request_token(request):
    """
    OAuth consumer initiate oauth flow by getting a request token
    """
    try:
        oauth_request, oauth_server = initialize_oauth(request)

        consumer_key = request.values.get("oauth_consumer_key", None)
        consumer = ConsumerApp.all().filter("consumer_key =", consumer_key).get()
        if not consumer:
            return Unauthorized()

        token = oauth_server.fetch_request_token(oauth_request)
        return Response(token.to_string(),
                content_type='application/x-www-form-urlencoded')
    except OAuthError, e:
        logging.debug(e)
        logging.debug(e.message)
        return BadRequest(e.message)
    except Exception, e:
        logging.debug(e)
        logging.debug(e.message)
        return InternalServerError()
    

@restrict_to_methods("GET")
@login_required
def oauth_authorize(request):
    """
    Display a form that will allow/disallow user to authorize
    consumers. Requires the target user to login.
    """
    try:
        user = request.user
        oauth_request, oauth_server = initialize_oauth(request)

    
        token = oauth_request.get_parameter('oauth_token')
        request_token = RequestToken.all().filter("token_key =", token).get()
        consumer = request_token.consumer
        oauth_request.set_parameter('oauth_consumer_key', consumer.consumer_key)
        token = oauth_server.fetch_request_token(oauth_request)

        return render_to_response("core/oauth/authorize.html",
                {'consumer': consumer, 'token': token})
    except OAuthError, e:
        logging.debug(e)
        logging.debug(e.message)
        return BadRequest(e.message)
    except Exception, e:
        logging.debug(e)
        logging.debug(e.message)
        return InternalServerError()

@restrict_to_methods("POST")
@login_required
def oauth_authorized(request):
    """
    Authorize the consumer to access the user's protected resource.
    Redirect back to callback_url provided during app registration or
    during the request_token phase.
    """
    try:
        oauth_request, oauth_server = initialize_oauth(request)

        user = request.user
        token = oauth_server.fetch_request_token(oauth_request)
        new_token = oauth_server.authorize_token(token, user)
        verifier = new_token.set_verifier()
        request_token = RequestToken.all().filter("token_key =", new_token.key).get()
        new_token.set_callback(request_token.consumer.callback_url)
        url = new_token.get_callback_url()
        return redirect("%s&%s" % (url, urllib.urlencode({'oauth_token': new_token.key}),))
    except OAuthError, e:
        logging.debug(e)
        logging.debug(e.message)
        return InternalServerError()
    except Exception, e:
        logging.debug(e)
        logging.debug(e.message)
        return InternalServerError()


@restrict_to_methods("POST")
def oauth_access_token(request):
    """
    Exchange the request_token with access_token.
    """
    try:
        oauth_request, oauth_server = initialize_oauth(request)
        access_token = oauth_server.fetch_access_token(oauth_request)
        return Response(access_token.to_string(),
                content_type="application/x-www-form-urlencoded")
    except OAutherror, e:
        logging.debug(e)
        logging.debug(e.message)
        return BadRequest(e.message)
    except Exception, e:
        logging.debug(e)
        logging.debug(e.message)
        return InternalServerError()


@restrict_to_methods("POST")
@oauth_protect
def oauth_info(request):
    friends = request.values.get("friends")
    return Response("you wanted to find %s" % friends, content_type='text/plain')

def test_request_token(request):
    oauth_token = request.values.get('oauth_token', None)
    request_token = RequestToken.all().filter("token_key =", oauth_token).get()
    token = OAuthToken(request_token.token_key, request_token.token_secret)
    return Response(token.to_string(), content_type='application/x-www-form-urlencoded')
