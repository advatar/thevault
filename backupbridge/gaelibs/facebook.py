import urllib
import cgi
import logging

from django.utils import simplejson as json

from google.appengine.api import urlfetch
from gaelibs.oauth import OAuthError


FACEBOOK_GRAPH_API_URL = "https://graph.facebook.com"
FACEBOOK_AUTHORIZE_URL = "https://graph.facebook.com/oauth/authorize"
FACEBOOK_ACCESS_TOKEN_URL = "https://graph.facebook.com/oauth/access_token"

class Facebook(object):
    """
    Facebook wrapper around Graph API using the simpler OAuth2 protocol.
    """

    def __init__(self, app_id, app_secret, redirect_uri, code=None):
        """
        Initialize with app_id, app_secret and redirect_uri.
        'code' is optional
        """

        self.app_id = app_id
        self.app_secret = app_secret
        self.redirect_uri = redirect_uri
        self.code = code

    def get_authorization_url(self):
        """
        Returns the facebook authorization url. The view should be
        responsible to do the redirect.
        """

        oauth_args = {'client_id': self.app_id,
                'type': 'web_server',
                'redirect_uri': self.redirect_uri,
                'scope': 'offline_access'}
        oauth_args = urllib.urlencode(oauth_args)
        return "%s?%s" % (FACEBOOK_AUTHORIZE_URL, oauth_args)

    def get_access_token(self, code=None):
        """
        Fetches the access_token. Verification 'code' provided
        during init may be use if not provided here.
        """

        if code is None:
            code = self.code
        oauth_args = {'client_id': self.app_id,
                'redirect_uri': self.redirect_uri, 
                'client_secret': self.app_secret,
                'code': code}
        url = "%s?%s" % (FACEBOOK_ACCESS_TOKEN_URL, urllib.urlencode(oauth_args))

        resp = urlfetch.fetch(url)

        try:
            return dict(cgi.parse_qsl(resp.content))['access_token']
        except KeyError:
            return None

    @classmethod
    def get_profile(self, user_id, access_token):
        """
        Fetches the user profile using user numeric id or alias. 'me' alias
        will only work when user is logged in to facebook.
        """

        url = "%s/%s?%s" % (FACEBOOK_GRAPH_API_URL, user_id, urllib.urlencode(dict(access_token=access_token)),)
        resp = urlfetch.fetch(url)
        profile = json.loads(resp.content)

        if 'error' in profile:
            raise OAuthError(profile['error']['message'])
        else:
            return profile

    @classmethod
    def get_me(self, access_token):
        """
        Fetches the profile using @me
        """
        return self.get_profile('me', access_token)

    @classmethod
    def get_friends(self, name, access_token):
        """
        Fetches user's friends list with their name and id.
        """

        url = "%s/%s/friends?%s" % (FACEBOOK_GRAPH_API_URL, name,
                urllib.urlencode(dict(access_token=access_token)),)
        resp = urlfetch.fetch(url)
        friends = json.loads(resp.content)

        if 'error' in friends:
            raise OAuthError(friends['error']['message'])
        else:
            try:
                return friends['data']
            except KeyError:
                return []

