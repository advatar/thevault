import cgi

from gaelibs.osg_oauth import OSGOAuth
from oauth import OAuthToken

YAHOO_API_URL = "https://api.login.yahoo.com/oauth/v2"
YAHOO_REQUEST_TOKEN_URL = "https://api.login.yahoo.com/oauth/v2/get_request_token"
YAHOO_AUTHORIZE_URL = "https://api.login.yahoo.com/oauth/v2/request_auth"
YAHOO_ACCESS_TOKEN_URL = "https://api.login.yahoo.com/oauth/v2/get_token"

class Yahoo(OSGOAuth):

    def __init__(self, consumer_key=None, consumer_secret=None,
            oauth_token_key=None, oauth_token_secret=None):
        super(self.__class__, self).__init__(consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                oauth_token_key=oauth_token_key,
                oauth_token_secret=oauth_token_secret)
        # if oauth_token_key is not None and oauth_token_secret is not None:

    def get_request_token(self, request_token_url=None, parameters=None):
        url = request_token_url if request_token_url is not None else YAHOO_REQUEST_TOKEN_URL
        return super(self.__class__, self).get_request_token(url, parameters=parameters)

    def get_authorization_url(self, token, authorization_url=None, callback_url=None, parameters=None):
        url = authorization_url if authorization_url is not None else YAHOO_AUTHORIZE_URL
        return super(self.__class__, self).get_authorization_url(token,
                authorization_url=url, callback_url=callback_url, parameters=parameters)

    def get_access_token(self, request_token, access_token_url=None, parameters=None):
        url = access_token_url if access_token_url is not None else YAHOO_ACCESS_TOKEN_URL
        token = super(self.__class__, self).get_access_token(request_token,
                access_token_url=url, parameters=parameters)
        self.all_access_tokens = dict(cgi.parse_qsl(self.last_response.content))
        return token

    def get_all_access_tokens(self):
        if hasattr(self, "all_access_tokens"):
            return self.all_access_tokens
        return None

    def yahoo_api(self, resource, params=None):
        return self.request(resource, parameters=params)
